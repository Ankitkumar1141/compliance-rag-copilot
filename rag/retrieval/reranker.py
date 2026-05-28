from typing import List
from langchain_core.documents import Document
from models.reranker_factory import Reranker

class RerankingStage:
    """
    Reranks a high-recall list of documents down to a high-precision subset (e.g. top 5)
    using the CrossEncoder reranker model.
    """
    def __init__(self, model_name: str = None):
        self.reranker = Reranker(model_name=model_name)

    def rerank(self, query: str, documents: List[Document], top_k: int = 5) -> List[Document]:
        """
        Reranks retrieved documents for the query and returns the top_k.
        """
        return self.reranker.rerank(query, documents, top_k=top_k)
