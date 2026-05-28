import os
from typing import List
from langchain_core.documents import Document

class Reranker:
    """
    Reranker using cross-encoders from sentence-transformers to evaluate context relevance.
    Reranks the retrieved documents and returns the top K.
    """
    def __init__(self, model_name: str = None):
        self.model_name = model_name or os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        self.model = None
        self._initialized = False

    def _initialize_model(self):
        if self._initialized:
            return
        try:
            from sentence_transformers import CrossEncoder
            # Load model onto CPU by default to run cross-platform without issues
            self.model = CrossEncoder(self.model_name, device="cpu")
            self._initialized = True
            print(f"[INFO] Successfully loaded reranker model: {self.model_name}")
        except Exception as e:
            print(f"[ERROR] Failed to load CrossEncoder model {self.model_name}: {e}")
            print("[WARNING] Proceeding without reranking (reverting to baseline retrieval order).")
            self.model = None
            self._initialized = True

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        """
        Reranks a list of LangChain Documents based on similarity to query.
        """
        if not documents:
            return []

        self._initialize_model()

        if self.model is None:
            # Fallback to returning original top_k if model could not be loaded
            return documents[:top_k]

        # Prepare pairs for cross-encoder evaluation: [ [query, doc1_text], [query, doc2_text], ... ]
        pairs = [[query, doc.page_content] for doc in documents]
        
        try:
            scores = self.model.predict(pairs)
            
            # Associate score with each document
            scored_docs = list(zip(scores, documents))
            
            # Sort descending by score
            scored_docs.sort(key=lambda x: x[0], reverse=True)
            
            # Extract and update metadata with rerank score
            reranked_docs = []
            for score, doc in scored_docs[:top_k]:
                # Copy document to avoid modifying original in-place unexpectedly
                new_doc = Document(
                    page_content=doc.page_content,
                    metadata={**doc.metadata, "rerank_score": float(score)}
                )
                reranked_docs.append(new_doc)
                
            return reranked_docs
        except Exception as e:
            print(f"[ERROR] Exception occurred during reranking: {e}")
            # Fallback
            return documents[:top_k]
