import os
from typing import List
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate

class PromptBuilder:
    """
    Loads externalized prompts and formats them with retrieved context,
    history, and query.
    """
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = prompts_dir
        self.system_prompt_path = os.path.join(prompts_dir, "system_prompt.txt")
        self.compliance_prompt_path = os.path.join(prompts_dir, "compliance_prompt.txt")
        
        self.system_prompt = self._load_prompt_file(self.system_prompt_path)
        self.compliance_template = self._load_prompt_file(self.compliance_prompt_path)

    def _load_prompt_file(self, path: str) -> str:
        """
        Loads prompt content from file.
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Required prompt file not found at: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def build_chat_prompt(self) -> ChatPromptTemplate:
        """
        Builds and returns a LangChain ChatPromptTemplate.
        """
        system_message = SystemMessagePromptTemplate.from_template(self.system_prompt)
        human_message = HumanMessagePromptTemplate.from_template(self.compliance_template)
        
        return ChatPromptTemplate.from_messages([
            system_message,
            human_message
        ])

    def format_prompt_inputs(self, context_docs: list, query: str, chat_history: str = "") -> dict:
        """
        Formats retrieved documents into a context block and prepares prompt inputs.
        """
        # Format context: doc 1: text (Source: ... Page: ... Section: ...)
        context_blocks = []
        for i, doc in enumerate(context_docs):
            src = doc.metadata.get("source", "Unknown")
            sec = doc.metadata.get("section", "General")
            page = doc.metadata.get("page", "Unknown")
            cat = doc.metadata.get("category", "General")
            
            block = (
                f"Document [{i+1}]: {doc.page_content.strip()}\n"
                f"Source Info: {cat} - {src} | Section: {sec} | Page: {page}\n"
                f"---"
            )
            context_blocks.append(block)
            
        context_str = "\n\n".join(context_blocks)
        
        return {
            "context": context_str,
            "chat_history": chat_history or "None",
            "question": query
        }
