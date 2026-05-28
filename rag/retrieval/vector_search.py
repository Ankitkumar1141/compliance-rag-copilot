from typing import List, Tuple
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from rag.ingestion.embedder import Embedder

class VectorSearch:
    """
    Handles dense retrieval (vector similarity search) using Chroma DB.
    """
    def __init__(self, persist_dir: str = None):
        self.embedder = Embedder(persist_dir=persist_dir)
        try:
            self.db = self.embedder.load_vector_store()
        except Exception as e:
            print(f"[WARNING] Could not load vector store in VectorSearch: {e}")
            self.db = None

    def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """
        Query Chroma vector store for similar chunks.
        """
        if self.db is None:
            print("[WARNING] Vector database is not initialized.")
            return []
        return self.db.similarity_search(query, k=k)

    def similarity_search_with_score(self, query: str, k: int = 5) -> List[Tuple[Document, float]]:
        """
        Query Chroma vector store and return (Document, score) tuples.
        """
        if self.db is None:
            return []
        return self.db.similarity_search_with_score(query, k=k)

    def get_retriever(self, k: int = 5) -> BaseRetriever:
        """
        Returns a LangChain compatible retriever.
        """
        if self.db is None:
            raise ValueError("Vector database is not loaded. Cannot create retriever.")
        return self.db.as_retriever(search_kwargs={"k": k})
