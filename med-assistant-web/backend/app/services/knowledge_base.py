import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

class KnowledgeBaseService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vectorstore_path = "data/vectorstore/guidelines"
        self._vectorstore = None

    @property
    def vectorstore(self):
        if self._vectorstore is None:
            if os.path.exists(self.vectorstore_path):
                self._vectorstore = FAISS.load_local(
                    self.vectorstore_path, 
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )
            else:
                print(f"Warning: Guidelines vectorstore not found at {self.vectorstore_path}")
        return self._vectorstore

    def query_guidelines(self, query: str, k: int = 3):
        """Retrieves relevant guideline snippets for a given query."""
        if not self.vectorstore:
            return "No guidelines available."
        
        docs = self.vectorstore.similarity_search(query, k=k)
        return "\n\n---\n\n".join([doc.page_content for doc in docs])

# Singleton instance
knowledge_base = KnowledgeBaseService()
