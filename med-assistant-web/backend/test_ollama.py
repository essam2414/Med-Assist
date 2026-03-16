import sys
from langchain_ollama import ChatOllama
from langchain_core.messages import SystemMessage

try:
    llm = ChatOllama(
        model="llama3.2", 
        temperature=0,
        num_predict=400,
        num_thread=8,
        num_ctx=4096,
        repeat_penalty=1.2,
        keep_alive=-1,
        format="json"  
    )
    print("ChatOllama initialized.")
    response = llm.invoke([SystemMessage(content="Return JSON: {\"test\": 1}")])
    print(response.content)
except Exception as e:
    print(f"ERROR: {e}")
