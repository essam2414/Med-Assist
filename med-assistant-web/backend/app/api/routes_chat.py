import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.deps import get_current_user, get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import (
    ChatSessionResp, ChatSessionCreate, ChatSendRequest, ChatMessageResp
)
from app.services.rag import get_chat_agent_executor, SYSTEM_PROMPT

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.get("/sessions", response_model=List[ChatSessionResp])
def list_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    return sessions

@router.post("/sessions", response_model=ChatSessionResp)
def create_session(request: ChatSessionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    new_session = ChatSession(
        user_id=current_user.id,
        title=request.title
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

@router.get("/sessions/{session_id}", response_model=ChatSessionResp)
def get_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session

@router.delete("/sessions/{session_id}")
def delete_session(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    db.delete(session)
    db.commit()
    return {"status": "deleted"}

@router.post("/sessions/{session_id}/messages", response_model=ChatMessageResp)
def send_message(session_id: int, request: ChatSendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    session = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    # Save user message
    user_msg = ChatMessage(session_id=session.id, role="user", content=request.message)
    db.add(user_msg)
    db.commit()
    
    # Reload session messages
    db.refresh(session)
    
    current_title = session.title.lower() if session.title else ""
    if current_title in ["new chat", "new conversation", ""] or not current_title:
        user_messages = [msg for msg in session.messages if msg.role == "user"]
        if len(user_messages) == 1:
            session.title = request.message[:30] + ("..." if len(request.message) > 30 else "")
            db.commit()
            db.refresh(session)
    
    # Format messages for LangChain Agent
    chat_history = [SystemMessage(content=SYSTEM_PROMPT)]
    # Skip the very last message in session.messages (which is the one just added above)
    # Limit to the last 6 messages to prevent context bloat for local models
    recent_messages = session.messages[:-1][-6:]
    for msg in recent_messages:
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        else:
            chat_history.append(AIMessage(content=msg.content))
    
    try:
        agent_executor = get_chat_agent_executor(db)
        
        messages = chat_history + [HumanMessage(content=request.message)]
        response = agent_executor.invoke({"messages": messages})
        reply_content = response["messages"][-1].content
        
        # Save assistant message
        assistant_msg = ChatMessage(session_id=session.id, role="assistant", content=reply_content)
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        
        return assistant_msg
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
