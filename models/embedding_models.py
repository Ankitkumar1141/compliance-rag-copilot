import os
from typing import Any
from langchain_core.embeddings import Embeddings

def get_embedding_model(provider: str = None, model_name: str = None) -> Embeddings:
    """
    Factory function to retrieve a LangChain Embeddings model.
    Supports 'local' (HuggingFace), 'openai', and 'gemini' providers.
    """
    if provider is None:
        provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    if model_name is None:
        model_name = os.getenv("EMBEDDING_MODEL")

    if provider == "local":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        # Default local model if none specified
        model_name = model_name or "sentence-transformers/all-MiniLM-L6-v2"
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"}  # default to CPU for cross-platform stability
        )
        
    elif provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI embeddings.")
        return OpenAIEmbeddings(model=model_name or "text-embedding-3-small", openai_api_key=api_key)
        
    elif provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required for Gemini embeddings.")
        return GoogleGenerativeAIEmbeddings(model=model_name or "models/embedding-001", google_api_key=api_key)
        
    else:
        raise ValueError(f"Unsupported embedding provider: {provider}. Use 'local', 'openai', or 'gemini'.")
