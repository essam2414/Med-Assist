import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from langgraph.prebuilt import create_react_agent
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry

# Initialize embeddings once at module level to save time per query
hf_embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

SYSTEM_PROMPT = """You are a helpful Medical AI Assistant.
ALWAYS call the `get_patient_records` tool for every question about a patient.
BE EXTREMELY BRIEF (1-3 sentences).

STRICT RULES:
1. Search chat history for the Patient's Name or ID.
2. If found, call `get_patient_records(patient_reference=NAME_OR_ID, query=USER_QUESTION)`.
3. NEVER use pronouns (he/him/she/her) in the 'patient_reference' argument. You must use the actual Name or ID.
4. If you have already fetched the records once, you MUST fetch them again for follow-up questions to ensure accuracy.
5. If the Name or ID is nowhere in the recent chat history, ask: "I need the patient's ID to access their records."
"""

def create_patient_retriever_tool(db: Session):
    
    @tool
    def get_patient_records(patient_reference: str, query: str) -> str:
        """
        Retrieves all database records for a patient (history, consultations, and transcripts).
        'patient_reference' MUST be the patient's Name or Display ID. 
        'query' is the specific question about their health or consultations.
        """
        print(f"--- RAG Tool Called: ref='{patient_reference}', query='{query}' ---")
        
        # Find patient
        patient = db.query(Patient).filter(
            or_(
                Patient.display_id.ilike(f"%{patient_reference}%"),
                Patient.name.ilike(f"%{patient_reference}%")
            )
        ).first()

        if not patient:
            return f"Error: Patient with reference '{patient_reference}' not found in the database. Please ask the user for clarification."
        
        # Build prompt context from patient details
        current_date = datetime.now().strftime('%Y-%m-%d')
        patient_info = f"Today's Date: {current_date}\nPatient Name: {patient.name}\nDOB: {patient.date_of_birth}\nGender: {patient.gender}\nKey History: {patient.key_history}\n\n"
        
        # Get consultations and transcripts
        consultations = db.query(Consultation).filter(Consultation.patient_id == patient.id).all()
        if not consultations:
            return patient_info + "This patient has no recorded consultations."
        
        # Build a mandatory summary of all consultations
        cons_list = []
        documents = []
        for cons in consultations:
            date_str = cons.created_at.strftime('%Y-%m-%d')
            cons_list.append(f"- {date_str}: {cons.title}")
            
            transcripts = db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == cons.id).order_by(TranscriptEntry.start_time).all()
            if transcripts:
                transcript_text = "\n".join([f"[{t.start_time:.1f} - {t.end_time:.1f}] {t.speaker}: {t.text}" for t in transcripts])
                doc_content = f"Consultation Date: {date_str}\nTitle: {cons.title}\nTranscript:\n{transcript_text}"
                documents.append(Document(page_content=doc_content, metadata={"date": date_str, "title": cons.title}))
        
        consultation_summary = "Consultation History:\n" + "\n".join(cons_list) + "\n\n"
        
        if not documents:
            return patient_info + consultation_summary + "Note: No detailed transcript text is available for these consultations."

        # RAG Pipeline for the specific patient
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)
        
        # Use local HuggingFace embeddings
        vectorstore = FAISS.from_documents(splits, hf_embeddings)
        retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
        
        relevant_docs = retriever.invoke(query)
        
        context = "\n\n---\n\n".join([d.page_content for d in relevant_docs])
        
        return (
            f"Patient Information:\n{patient_info}\n"
            f"{consultation_summary}"
            f"Relevant Transcript Snippets for query '{query}':\n\n{context}"
        )

    return get_patient_records

def get_chat_agent_executor(db: Session):
    # Balanced performance tuning for Ollama
    llm = ChatOllama(
        model="llama3.2", 
        temperature=0,
        num_predict=200,    # Prevents cutoff while remaining brief
        repeat_penalty=1.2  # Prevent looping
    )
    
    patient_tool = create_patient_retriever_tool(db)
    tools = [patient_tool]
    
    # Passing SYSTEM_PROMPT via first message instead, to avoid API signature conflicts across langgraph versions
    agent = create_react_agent(llm, tools=tools)
        
    return agent
