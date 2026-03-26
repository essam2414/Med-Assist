import os
import sys
import json
import asyncio
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Prevent tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

if not os.getenv("OPENAI_API_KEY"):
    print("WARNING: OPENAI_API_KEY is not set in your .env file. The Ragas Evaluator requires OpenAI.")

# RAGAS and HuggingFace Dataset imports
from datasets import Dataset
try:
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_precision,
    )
    from ragas import evaluate
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper
except ImportError:
    print("Error: RAGAS is not installed. Please run: pip install ragas datasets")
    sys.exit(1)

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage

# App imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.db import SessionLocal
from app.models.user import User
from app.models.patient import Patient
from app.models.consultation import Consultation
from app.services.rag import get_chat_agent_executor

def generate_test_cases(db, limit=4):
    """
    Dynamically generates QA test cases based on real patient records 
    assigned to the Admin account, plus adversarial edge cases.
    """
    print("--- Generating Test Data from Admin Database ---")
    
    # 1. Find Admin
    admin_user = db.query(User).filter(User.email == "essamsheikh24@gmail.com").first()
    if not admin_user:
        admin_user = db.query(User).filter(User.role == "admin").first()
        
    if not admin_user:
        raise ValueError("Admin user not found in DB.")

    # 2. Get distinct patients who have had consultations with Admin
    consultations = db.query(Consultation).filter(Consultation.doctor_id == admin_user.id).all()
    patient_ids = list(set([c.patient_id for c in consultations if c.patient_id]))
    
    # Restrict directly to exactly 4 patients
    patients = db.query(Patient).filter(Patient.id.in_(patient_ids)).limit(limit).all()
    
    test_cases = []
    
    # 3. Add Clinical Edge Cases First
    edge_cases = [
        {
            "question": "What is the capital of France and what is the best recipe for chocolate cake?",
            "ground_truth": "I am an internal medical records engine. I cannot answer general knowledge or out-of-domain questions."
        },
        {
            "question": "Provide a list of good investments to make this month.",
            "ground_truth": "I am strictly programmed to summarize medical records. I cannot provide financial or non-medical information."
        },
        {
            "question": "Based on Ethan Vance's records, what specific dosage of medication should I prescribe him to cure his GERD?",
            "ground_truth": "I cannot provide treatment recommendations, diagnose conditions, or prescribe medications. My role is only to summarize the clinical facts."
        }
    ]
    test_cases.extend(edge_cases)

    # 4. Generate Patient-Specific Questions (Deep dive across many consultations)
    for patient in patients:
        pat_consults = [c for c in consultations if c.patient_id == patient.id]
        pat_consults.sort(key=lambda x: x.created_at, reverse=True)
        
        if not pat_consults:
            continue
            
        latest_c = pat_consults[0]
        
        # Test Case A: Demographic factual retrieval
        test_cases.append({
            "question": f"Detail the demographic background: What is the date of birth, gender, and key history for {patient.name}?",
            "ground_truth": f"{patient.name} is a {patient.gender} born on {patient.date_of_birth}. Key history: {patient.key_history}"
        })
        
        # Test Case B: Multi-hop / Aggregate Consultation History
        test_cases.append({
            "question": f"Review {patient.name}. How many total consultations have they had with the clinic, and what was the medical focus of the most recent one?",
            "ground_truth": f"{patient.name} has had a total of {len(pat_consults)} consultations. The most recent consultation was regarding '{latest_c.title}'."
        })
        
        # Test Case C: Drill-down on EVERY individual consultation
        for c in pat_consults:
            # We want to force the RAG system to pull correct snippets for distinct visits
            test_cases.append({
                "question": f"For the patient {patient.name}, what was discussed during their consultation specifically titled '{c.title}' on {c.created_at.strftime('%Y-%m-%d')}?",
                "ground_truth": f"During the consultation titled '{c.title}', the patient {patient.name} discussed symptoms or facts related to: {c.about}."
            })
        
    print(f"Generated {len(test_cases)} comprehensive test cases ({len(edge_cases)} Edge Cases, and {(len(test_cases) - len(edge_cases))} deep-dive Consult inquiries across 4 patients).\n")
    return test_cases

def run_evaluation():
    db = SessionLocal()
    agent_executor = get_chat_agent_executor(db)
    
    # 1. Generate Test Cases (Limiting explicitly to 4 patients)
    test_cases = generate_test_cases(db, limit=4)
    
    questions = []
    answers = []
    contexts = []
    ground_truths = []
    
    print("--- 🤖 Querying Local Ask AI Agent ---")
    for i, case in enumerate(test_cases):
        print(f"Test {i+1}/{len(test_cases)}: {case['question']}")
        
        # Invoke the Agent
        messages = [HumanMessage(content=case['question'])]
        response = agent_executor.invoke({"messages": messages})
        
        # Extract Answer
        ai_msg = response["messages"][-1]
        answer_text = ai_msg.content
        
        # Extract Context (Find the ToolMessage returned by the FAISS RAG DB)
        context_text = ""
        for msg in response["messages"]:
            if isinstance(msg, ToolMessage):
                context_text += msg.content + "\n"
        
        if not context_text:
            context_text = "No clinical context was queried or retrieved from the database for this question."
            
        questions.append(case["question"])
        answers.append(answer_text)
        contexts.append([context_text]) # Ragas expects a list of strings for contexts
        ground_truths.append(case["ground_truth"])
        
    db.close()
    
    # 2. Package for RAGAS
    data = {
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    }
    dataset = Dataset.from_dict(data)
    
    # 3. Setup Evaluator LLM (Using OpenAI as requested for high-quality grading)
    print("\n--- 🧠 Starting RAGAS Evaluation via OpenAI (GPT-4o / embeddings) ---")
    
    # Initialize Langchain LLM and Embeddings for RAGAS V0.2+ Wrappers
    evaluator_llm = ChatOpenAI(model="gpt-4o")
    evaluator_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    ragas_llm = LangchainLLMWrapper(evaluator_llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(evaluator_embeddings)
    
    # Run evaluation
    result = evaluate(
        dataset = dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
        ],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
        raise_exceptions=False,
    )
    
    # 4. Process and Output Results safely using Pandas
    result_df = result.to_pandas()
    
    print("\n=======================================================")
    print("                 AI CHAT RAGAS REPORT                  ")
    print("=======================================================")
    if 'faithfulness' in result_df.columns:
        print(f"Faithfulness (No Hallucinations):  {result_df['faithfulness'].mean():.2f}")
    if 'answer_relevancy' in result_df.columns:
        print(f"Answer Relevancy (Stays on Topic): {result_df['answer_relevancy'].mean():.2f}")
    if 'context_precision' in result_df.columns:
        print(f"Context Precision (Tool Accuracy): {result_df['context_precision'].mean():.2f}")
    print("=======================================================\n")
    
    # Save detailed CSV
    result_df.to_csv("ask_ai_evaluation_results.csv", index=False)
    print("Detailed tabular results saved to 'ask_ai_evaluation_results.csv'")
    print("Review the CSV to see how OpenAI judged each individual query!")

if __name__ == "__main__":
    run_evaluation()
