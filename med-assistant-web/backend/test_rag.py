import sys
import os
from dotenv import load_dotenv

load_dotenv()

from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.db import SessionLocal
from app.services.rag import get_chat_agent_executor, SYSTEM_PROMPT
from app.models.patient import Patient

def main():
    db = SessionLocal()
    
    # Just list some patients to know what to query
    patients = db.query(Patient).all()
    print("Available patients:")
    for p in patients:
        print(f" - {p.name} (Display ID: {p.display_id})")
        
    print("\n--- Initializing Agent ---\n")
    agent = get_chat_agent_executor(db)
    
    chat_history = [SystemMessage(content=SYSTEM_PROMPT)]
    
    # Test 1: Vague query (no name/ID)
    print("User: Can you tell me about my patient's last consultation?")
    print("Sending query...\n")
    resp1 = agent.invoke({
        "messages": chat_history + [HumanMessage(content="Can you tell me about my patient's last consultation?")]
    })
    out1 = resp1["messages"][-1].content
    print(f"Agent: {out1}\n")
    
    # Update history
    chat_history.append(HumanMessage(content="Can you tell me about my patient's last consultation?"))
    chat_history.append(AIMessage(content=out1))
    
    if patients:
        p = patients[0]
        # Test 2: Provide Name and ID
        q = f"The patient is {p.name} with display ID {p.display_id}. What were their main concerns?"
        print(f"User: {q}")
        print("Sending query...\n")
        resp2 = agent.invoke({
            "messages": chat_history + [HumanMessage(content=q)]
        })
        out2 = resp2["messages"][-1].content
        print(f"Agent: {out2}\n")
        
        # Test 3: Follow up without ID
        chat_history.append(HumanMessage(content=q))
        chat_history.append(AIMessage(content=out2))
        
        q2 = "Did the patient mention any allergies or specific symptoms?"
        print(f"User: {q2}")
        print("Sending query...\n")
        resp3 = agent.invoke({
            "messages": chat_history + [HumanMessage(content=q2)]
        })
        out3 = resp3["messages"][-1].content
        print(f"Agent: {out3}\n")

if __name__ == "__main__":
    main()
