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

# Memory cache to avoid re-vectorizing consultation transcripts on every single query
patient_vectorstore_cache = {}

SYSTEM_PROMPT = """You are an Internal Medical Records Summarization Engine. 

Your ONLY role is to retrieve, synthesize, and relay information found within the patient database for authorized personnel. You do NOT give medical advice.

CORE CAPABILITIES & EXPECTED BEHAVIOR:
- Answer factual questions about the patient (e.g., age, key diagnoses, current medications).
- Summarize a single consultation or all consultations to date (e.g., most frequent problems across all visits).
- Locate specific information in the record (e.g., when a symptom was first reported).
- List consultations and basic metadata (e.g., count total consultations, dates, clinician involved).
- Extract key problems/concerns overall or per consultation.
- Clarify or rephrase data for the doctor (e.g., explain history in simple terms, bullet list of symptoms).
- Highlight missing or unclear information non-directively (e.g., "The notes mention headaches but not duration").

STRICT CLINICAL GUARDRAILS (NEVER VIOLATE):
- NO DIAGNOSES OR TREATMENT RECOMMENDATIONS: Never propose a diagnosis, medication, dose, or management plan.
- NO INVENTING FACTS: If a detail is missing from the record, say exactly: "This is not documented in the available notes."
- NO OVERWRITING CLINICAL JUDGEMENT: Your output is strictly a summary of existing data for clinician review only.

CRITICAL INSTRUCTIONS:
1. When a name or ID is mentioned, you MUST call `get_patient_records(patient_reference=NAME_OR_ID, query=QUESTION)`.
2. The `patient_reference` argument MUST be ONLY the person's name or ID.
3. If asked about the number of consultations, use the 'Total Consultations' number in the 'PATIENT CONSULTATION LOG'.
4. If the tool explicitly says "Patient not found", respond with: "I'm sorry, I cannot provide details on that patient as they are not in our database."
5. Summarizing health data is your core function; do NOT refuse by claiming you cannot provide medical advice.
6. Keep answers focused, professional, and non-directive. Use bullet points when helpful.
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
        
        # 1. FETCH MANDATORY DATA (Summary is fast, don't cache this part)
        current_date = datetime.now().strftime('%Y-%m-%d')
        patient_info = f"Today's Date: {current_date}\nPatient Name: {patient.name}\nDOB: {patient.date_of_birth}\nGender: {patient.gender}\nKey History: {patient.key_history}\n"
        
        consultations = db.query(Consultation).filter(Consultation.patient_id == patient.id).order_by(Consultation.created_at.desc()).all()
        if not consultations:
            return patient_info + "\nThis patient has no recorded consultations."
        
        cons_list = []
        for i, cons in enumerate(consultations):
            date_str = cons.created_at.strftime('%Y-%m-%d')
            label = " (MOST RECENT)" if i == 0 else ""
            doctor_name = cons.doctor.name if cons.doctor else "Unknown"
            cons_list.append(f"- Date: {date_str}, Name/Title: {cons.title}, Clinician: Dr. {doctor_name}{label}")
        
        # Chronological list for the LLM to count and find "last"
        total_cons = len(consultations)
        consultation_summary = f"PATIENT CONSULTATION LOG (Total Consultations: {total_cons}):\n" + "\n".join(cons_list) + "\n"
        latest_headline = f"The most recent consultation was on {consultations[0].created_at.strftime('%Y-%m-%d')} regarding '{consultations[0].title}'.\n"

        # 2. CACHE CHECK FOR HEAVY TRANSCRIPT SEARCH
        if patient.id in patient_vectorstore_cache:
            vectorstore = patient_vectorstore_cache[patient.id]
            retriever = vectorstore.as_retriever(search_kwargs={"k": 5}) # Increased k for more context
            relevant_docs = retriever.invoke(query)
            context = "\n\n---\n\n".join([d.page_content for d in relevant_docs])
            return f"{patient_info}\n{latest_headline}\n{consultation_summary}\nRelevant Transcript Snippets for '{query}':\n\n{context}"

        # 3. Only build documents if not in cache
        documents = []
        for cons in consultations:
            date_str = cons.created_at.strftime('%Y-%m-%d')
            transcripts = db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == cons.id).order_by(TranscriptEntry.start_time).all()
            if transcripts:
                transcript_text = "\n".join([f"[{t.start_time:.1f} - {t.end_time:.1f}] {t.speaker}: {t.text}" for t in transcripts])
                doc_content = f"Consultation Date: {date_str}\nTitle: {cons.title}\nTranscript:\n{transcript_text}"
                documents.append(Document(page_content=doc_content, metadata={"date": date_str, "title": cons.title}))
        
        if not documents:
            return patient_info + consultation_summary + "\nNote: No detailed transcript text is available."

        # 4. BUILD AND CACHE THE VECTORSTORE
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        splits = text_splitter.split_documents(documents)
        vectorstore = FAISS.from_documents(splits, hf_embeddings)
        patient_vectorstore_cache[patient.id] = vectorstore
        
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        relevant_docs = retriever.invoke(query)
        context = "\n\n---\n\n".join([d.page_content for d in relevant_docs])
        
        return (
            f"Patient Information:\n{patient_info}\n"
            f"{latest_headline}\n"
            f"{consultation_summary}\n"
            f"Relevant Transcript Snippets for query '{query}':\n\n{context}"
        )

    return get_patient_records

def get_chat_agent_executor(db: Session):
    # Performance tuning for Core Ultra 7
    llm = ChatOllama(
        model="llama3.2", 
        temperature=0,
        num_predict=200,
        num_thread=8,       # Core Ultra 7 usually has 6 or 8 performance threads
        num_ctx=4096,       # Lower context window makes local inference much faster
        repeat_penalty=1.2,
        keep_alive=-1
    )
    
    patient_tool = create_patient_retriever_tool(db)
    tools = [patient_tool]
    
    # Passing SYSTEM_PROMPT via first message instead, to avoid API signature conflicts across langgraph versions
    agent = create_react_agent(llm, tools=tools)
        
    return agent
