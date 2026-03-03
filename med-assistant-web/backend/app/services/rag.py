import os
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from langgraph.prebuilt import create_react_agent

from app.models.patient import Patient
from app.models.consultation import Consultation
from app.models.transcript import TranscriptEntry

SYSTEM_PROMPT = """You are a specialized Medical AI Assistant designed to help doctors query patient information and consultation transcripts.

CRITICAL INSTRUCTIONS:
1. You MUST ONLY use the information provided to you via the `query_patient_records` tool. DO NOT invent information or rely on your general medical training to answer patient-specific questions.
2. If a doctor asks about a patient but DOES NOT provide BOTH their Name and Display ID in the conversation, you MUST ask the doctor to provide the patient's Display ID (and Name if missing) before querying the records.
3. If the information retrieved from the records is NOT ENOUGH to answer the doctor's query, you MUST ask the doctor to clarify or provide more specific information. Do not guess.
4. You have access to the conversation history. If the doctor already provided the patient's Name and Display ID earlier in the conversation, you should deduce it and use it to query records for follow-up questions.
5. Keep your answers concise, professional, and directly related to the user's query about the patient.
6. DO NOT use markdown formatting (such as asterisks for bolding or italics) in your responses. Output plain text only to ensure compatibility with the chat interface.
7. Always calculate a patient's age using their provided Date of Birth (DOB) and the Today's Date given in the records. Do not approximate or guess.
"""

def create_patient_retriever_tool(db: Session):
    
    @tool
    def query_patient_records(patient_name: str, display_id: str, query: str) -> str:
        """
        Query a specific patient's records and consultation transcripts.
        Requires EXACT patient_name and display_id to fetch the data.
        The query argument is what you want to extract from the patient's data.
        """
        # Find patient
        patient = db.query(Patient).filter(
            Patient.display_id == display_id,
            Patient.name.ilike(f"%{patient_name}%")
        ).first()

        if not patient:
            return f"Error: Patient with name '{patient_name}' and display ID '{display_id}' not found in the database."
        
        # Build prompt context from patient details
        current_date = datetime.now().strftime('%Y-%m-%d')
        patient_info = f"Today's Date: {current_date}\nPatient Name: {patient.name}\nDOB: {patient.date_of_birth}\nGender: {patient.gender}\nKey History: {patient.key_history}\n\n"
        
        # Get consultations and transcripts
        consultations = db.query(Consultation).filter(Consultation.patient_id == patient.id).all()
        if not consultations:
            return patient_info + "This patient has no recorded consultations."
        
        documents = []
        for cons in consultations:
            transcripts = db.query(TranscriptEntry).filter(TranscriptEntry.consultation_id == cons.id).order_by(TranscriptEntry.start_time).all()
            if not transcripts:
                continue
            
            transcript_text = "\n".join([f"[{t.start_time:.1f} - {t.end_time:.1f}] {t.speaker}: {t.text}" for t in transcripts])
            
            doc_content = f"Consultation Date: {cons.created_at.strftime('%Y-%m-%d')}\nTitle: {cons.title}\nTranscript:\n{transcript_text}"
            documents.append(Document(page_content=doc_content, metadata={"date": cons.created_at.strftime('%Y-%m-%d'), "title": cons.title}))
        
        if not documents:
            return patient_info + "This patient has consultations but no transcript texts available."

        # RAG Pipeline for the specific patient
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(documents)
        
        # If the transcript is very small, we could just return it directly. But we use VectorStore for scalability.
        vectorstore = FAISS.from_documents(splits, OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY")))
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
        
        relevant_docs = retriever.invoke(query)
        
        context = "\n\n---\n\n".join([d.page_content for d in relevant_docs])
        
        return (
            f"Patient Information:\n{patient_info}\n\n"
            f"Relevant Consultation Transcripts for query '{query}':\n\n{context}"
        )

    return query_patient_records

def get_chat_agent_executor(db: Session):
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=os.getenv("OPENAI_API_KEY"), temperature=0)
    
    patient_tool = create_patient_retriever_tool(db)
    tools = [patient_tool]
    
    # Passing SYSTEM_PROMPT via first message instead, to avoid API signature conflicts across langgraph versions
    agent = create_react_agent(llm, tools=tools)
        
    return agent
