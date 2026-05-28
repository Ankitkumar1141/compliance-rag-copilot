import os
from typing import Any, List, Optional
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration

class MockChatModel(BaseChatModel):
    """
    A fallback mock LLM that runs offline without any API keys or local servers.
    Useful for testing the RAG pipeline out-of-the-box.
    """
    model_name: str = "mock-compliance-model"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any,
    ) -> ChatResult:
        # Simple compliance heuristics based on the input prompt context
        user_query = ""
        context = ""
        
        # Try to extract the user's question and context from the prompt
        for msg in messages:
            content = msg.content
            if isinstance(content, str):
                if "Question:" in content or "User asks:" in content:
                    user_query = content
                if "Context:" in content:
                    context = content

        # Check for policy violations
        is_violation = False
        violation_reason = "No violation detected based on context."
        
        lower_query = user_query.lower()
        if "password" in lower_query and ("plain text" in lower_query or "plaintext" in lower_query or "store" in lower_query):
            is_violation = True
            violation_reason = "Storing passwords in plain text is a critical violation of OWASP Password Storage Guidelines and ISO 27001 Control A.12.4.4."
        elif "gdpr" in lower_query and "consent" in lower_query:
            is_violation = True
            violation_reason = "GDPR Article 6 requires explicit consent for processing personal data, which must be freely given, specific, informed, and unambiguous."
        
        if is_violation:
            response_text = (
                f"[POLICY VIOLATION DETECTED]\n\n"
                f"No, you cannot perform this action.\n\n"
                f"**Reasoning & Citation:**\n"
                f"According to the security compliance standards: {violation_reason}\n\n"
                f"Please refer to the company's internal compliance rules and documentation for password security and personal data processing."
            )
        else:
            response_text = (
                "Based on the provided compliance documents, the requested action is permitted under standard operational parameters.\n\n"
                "**Citation:** See company internal engineering handbook and general security guidelines."
            )
            
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=response_text))])

    @property
    def _llm_type(self) -> str:
        return "mock_compliance"


def get_llm(provider: str = None, model_name: str = None, **kwargs: Any) -> BaseChatModel:
    """
    Factory function to retrieve a LangChain Chat Model.
    Supports 'ollama', 'groq', 'huggingface', 'gemini', 'openai', and 'mock'.
    """
    if provider is None:
        provider = os.getenv("LLM_PROVIDER", "mock").lower()
    if model_name is None:
        model_name = os.getenv("LLM_MODEL")

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError:
            from langchain_community.chat_models import ChatOllama
        # Default local model if none specified
        model_name = model_name or "llama3"
        return ChatOllama(
            model=model_name,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            **kwargs
        )

    elif provider == "groq":
        from langchain_groq import ChatGroq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("[WARNING] GROQ_API_KEY is empty. Falling back to MockChatModel.")
            return MockChatModel()
        return ChatGroq(
            model_name=model_name or "llama-3.3-70b-specdec",
            groq_api_key=api_key,
            **kwargs
        )

    elif provider == "huggingface":
        # We can use HuggingFace Endpoint for chat
        from langchain_community.llms import HuggingFaceEndpoint
        from langchain_community.chat_models.huggingface import ChatHuggingFace
        api_key = os.getenv("HF_API_KEY")
        if not api_key:
            print("[WARNING] HF_API_KEY is empty. Falling back to MockChatModel.")
            return MockChatModel()
        
        # Hugging Face Inference API endpoint
        repo_id = model_name or "Qwen/Qwen2.5-Coder-32B-Instruct"
        llm = HuggingFaceEndpoint(
            repo_id=repo_id,
            huggingfacehub_api_token=api_key,
            temperature=0.1,
            max_new_tokens=1024,
            **kwargs
        )
        return ChatHuggingFace(llm=llm)

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("[WARNING] GEMINI_API_KEY is empty. Falling back to MockChatModel.")
            return MockChatModel()
        return ChatGoogleGenerativeAI(
            model=model_name or "gemini-1.5-flash",
            google_api_key=api_key,
            temperature=0.1,
            **kwargs
        )

    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("[WARNING] OPENAI_API_KEY is empty. Falling back to MockChatModel.")
            return MockChatModel()
        return ChatOpenAI(
            model=model_name or "gpt-4o-mini",
            openai_api_key=api_key,
            temperature=0.1,
            **kwargs
        )

    elif provider == "mock":
        return MockChatModel()

    else:
        print(f"[WARNING] Unknown provider '{provider}'. Falling back to MockChatModel.")
        return MockChatModel()
