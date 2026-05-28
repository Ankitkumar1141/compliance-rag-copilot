from typing import List
from langchain_core.documents import Document
try:
    from langchain_classic.retrievers.ensemble import EnsembleRetriever
except ImportError:
    try:
        from langchain.retrievers import EnsembleRetriever
    except ImportError:
        from langchain_community.retrievers import EnsembleRetriever

from rag.retrieval.vector_search import VectorSearch
from rag.retrieval.bm25_search import BM25Search

class HybridRetriever:
    """
    Ensemble retriever combining dense retrieval (Chroma vector search, 60% weight)
    and sparse retrieval (BM25 keyword search, 40% weight).
    """
    def __init__(self, persist_dir: str = None, chunks_json_path: str = "data/processed_docs/chunks.json"):
        self.vector_search = VectorSearch(persist_dir=persist_dir)
        self.bm25_search = BM25Search(chunks_json_path=chunks_json_path)
        self.ensemble_retriever = None
        self._initialize_ensemble()

    def _initialize_ensemble(self):
        try:
            vector_retriever = self.vector_search.get_retriever(k=10)
            bm25_retriever = self.bm25_search.get_retriever(k=10)
            
            self.ensemble_retriever = EnsembleRetriever(
                retrievers=[vector_retriever, bm25_retriever],
                weights=[0.6, 0.4]
            )
            print("[INFO] Successfully initialized Hybrid Ensemble Retriever (Vector 0.6, BM25 0.4).")
        except Exception as e:
            print(f"[WARNING] Could not construct EnsembleRetriever: {e}")
            self.ensemble_retriever = None

    def retrieve(self, query: str, top_n: int = 15) -> List[Document]:
        """
        Retrieves top_n merged documents using hybrid dense + sparse retrieval.
        """
        # Re-initialize if previously failed (e.g., database was created after init)
        if self.ensemble_retriever is None:
            self._initialize_ensemble()

        if self.ensemble_retriever is not None:
            try:
                # Update k dynamically if possible, or filter retrieved list
                # Since EnsembleRetriever merges list, let's retrieve and slice to top_n
                docs = self.ensemble_retriever.get_relevant_documents(query)
                return docs[:top_n]
            except Exception as e:
                print(f"[ERROR] Ensemble retrieval failed: {e}. Falling back to individual search.")
        
        # Fallback to whatever is available
        if self.vector_search.db is not None:
            print("[INFO] Falling back to pure Vector Search.")
            return self.vector_search.similarity_search(query, k=top_n)
        elif self.bm25_search.retriever is not None:
            print("[INFO] Falling back to pure BM25 Search.")
            return self.bm25_search.search(query, k=top_n)
            
        print("[WARNING] Both dense and sparse databases are unavailable. Returning empty results.")
        return []
