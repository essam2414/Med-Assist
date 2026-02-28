import os
from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from app.deps import get_current_user
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse, ChatMessage

router = APIRouter(prefix="/api/chat", tags=["chat"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@router.post("", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        # Format messages for OpenAI completion API
        messages_for_api = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Simple gpt-4o-mini request with no extra instructions
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_api
        )
        
        reply_content = response.choices[0].message.content
        return ChatResponse(message=ChatMessage(role="assistant", content=reply_content))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
