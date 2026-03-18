import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def build_guidelines_index():
    print("Building Guidelines Knowledge Base...")
    
    guidelines_dir = "data/guidelines"
    output_dir = "data/vectorstore/guidelines"
    
    if not os.path.exists(guidelines_dir):
        print(f"Error: {guidelines_dir} not found.")
        return

    documents = []
    for filename in os.listdir(guidelines_dir):
        if filename.endswith(".txt"):
            path = os.path.join(guidelines_dir, filename)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                # Use filename as source metadata
                documents.append(Document(page_content=content, metadata={"source": filename}))

    if not documents:
        print("No guideline files found.")
        return

    # Split into meaningful chunks
    # Since we hand-selected the text, we can use slightly larger chunks to keep context together
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800, 
        chunk_overlap=150,
        separators=["\n\n", "\n", " ", ""]
    )
    splits = text_splitter.split_documents(documents)
    print(f"Created {len(splits)} chunks from {len(documents)} files.")

    # Embed and Save
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(splits, embeddings)
    
    os.makedirs(output_dir, exist_ok=True)
    vectorstore.save_local(output_dir)
    print(f"Success: Guidelines index saved to {output_dir}")

if __name__ == "__main__":
    build_guidelines_index()
