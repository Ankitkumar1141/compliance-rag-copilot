from typing import List, Dict, Any
from models.llm_factory import get_llm
from rag.generation.prompt_builder import PromptBuilder
from langchain_core.documents import Document

class AnswerGenerator:
    """
    Combines retrieved context with prompt builder and executes LLM generation.
    """
    def __init__(self, provider: str = None, model_name: str = None, prompts_dir: str = "prompts"):
        self.llm = get_llm(provider, model_name)
        self.prompt_builder = PromptBuilder(prompts_dir=prompts_dir)
        self.prompt_template = self.prompt_builder.build_chat_prompt()

    def generate(self, query: str, context_docs: List[Document], chat_history: str = "") -> Dict[str, Any]:
        """
        Generates compliance answers based on user query and retrieved documents.
        """
        # Format the context and inputs
        inputs = self.prompt_builder.format_prompt_inputs(
            context_docs=context_docs,
            query=query,
            chat_history=chat_history
        )
        
        try:
            # Execute LangChain LLM chain
            chain = self.prompt_template | self.llm
            response = chain.invoke(inputs)
            answer_text = response.content.strip()
        except Exception as e:
            print(f"[ERROR] LLM generation failed: {e}")
            answer_text = (
                "[ERROR] Failed to generate compliance response due to an LLM error.\n\n"
                "Please verify LLM provider configuration and network connection."
            )

        # Structure sources for output and citation validation
        sources_list = []
        seen_sources = set()
        for doc in context_docs:
            src = doc.metadata.get("source", "Unknown")
            sec = doc.metadata.get("section", "General")
            page = doc.metadata.get("page", 1)
            cat = doc.metadata.get("category", "Compliance Guideline")
            
            source_key = (src, sec, page)
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources_list.append({
                    "source": src,
                    "section": sec,
                    "page": page,
                    "category": cat
                })

        return {
            "answer": answer_text,
            "sources": sources_list
        }
