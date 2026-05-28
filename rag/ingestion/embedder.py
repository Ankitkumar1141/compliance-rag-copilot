import os
import shutil
from typing import List
from langchain_core.documents import Document
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
from models.embedding_models import get_embedding_model

class Embedder:
    """
    Handles embedding of document chunks and persistence into a Chroma vector database.
    """
    def __init__(self, persist_dir: str = None, provider: str = None, model_name: str = None):
        self.persist_dir = persist_dir or os.getenv("CHROMA_DB_PATH", "data/embeddings")
        self.embedding_model = get_embedding_model(provider, model_name)

    def save_to_vector_store(self, chunks: List[Document], overwrite: bool = False) -> Chroma:
        """
        Creates or updates a Chroma vector store with chunk embeddings.
        """
        if not chunks:
            raise ValueError("No chunks provided to embed.")

        # Ensure directory structure
        os.makedirs(os.path.dirname(self.persist_dir), exist_ok=True)

        if overwrite and os.path.exists(self.persist_dir):
            print(f"[INFO] Overwriting existing vector store at: {self.persist_dir}")
            # Close/clean up to release locks on Windows, then delete directory
            shutil.rmtree(self.persist_dir, ignore_errors=True)

        print(f"[INFO] Embedding {len(chunks)} chunks and saving to {self.persist_dir}...")
        
        # Load Chroma DB
        db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_model,
            persist_directory=self.persist_dir
        )
        # chromadb 0.4+ auto-persists; explicit persist() call is no longer needed.
        
        print(f"[INFO] Ingestion completed. Embeddings saved at: {self.persist_dir}")
        return db

    def load_vector_store(self) -> Chroma:
        """
        Loads the existing Chroma vector database from disk.
        """
        if not os.path.exists(self.persist_dir):
            raise FileNotFoundError(f"No vector store exists at: {self.persist_dir}")
            
        db = Chroma(
            persist_directory=self.persist_dir,
            embedding_function=self.embedding_model
        )
        return db
