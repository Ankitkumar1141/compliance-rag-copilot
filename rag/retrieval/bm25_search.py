import os
import json
from typing import List
from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever

class BM25Search:
    """
    Handles keyword-based sparse retrieval using BM25.
    Initializes from cached JSON chunks or a provided document list.
    """
    def __init__(self, chunks_json_path: str = "data/processed_docs/chunks.json"):
        self.chunks_json_path = chunks_json_path
        self.retriever = None
        self._initialize_retriever()

    def _initialize_retriever(self):
        if not os.path.exists(self.chunks_json_path):
            print(f"[WARNING] Chunks JSON cache not found at: {self.chunks_json_path}. BM25Retriever is uninitialized.")
            return

        try:
            with open(self.chunks_json_path, "r", encoding="utf-8") as f:
                chunks_data = json.load(f)

            documents = [
                Document(page_content=item["page_content"], metadata=item["metadata"])
                for item in chunks_data
            ]
            
            if documents:
                # Initialize BM25 retriever
                self.retriever = BM25Retriever.from_documents(documents)
                print(f"[INFO] Initialized BM25Retriever with {len(documents)} chunks.")
        except Exception as e:
            print(f"[ERROR] Failed to initialize BM25Retriever: {e}")
            self.retriever = None

    def search(self, query: str, k: int = 5) -> List[Document]:
        """
        Perform keyword search using BM25.
        """
        # Re-initialize if not loaded (e.g. if the file was created after class instantiation)
        if self.retriever is None:
            self._initialize_retriever()

        if self.retriever is None:
            print("[WARNING] BM25 retriever not initialized. Returning empty list.")
            return []

        self.retriever.k = k
        return self.retriever.invoke(query)

    def get_retriever(self, k: int = 5) -> BM25Retriever:
        """
        Returns the LangChain compatible BM25Retriever.
        """
        if self.retriever is None:
            self._initialize_retriever()
        if self.retriever is None:
            raise ValueError("BM25 retriever is not initialized.")
        self.retriever.k = k
        return self.retriever
