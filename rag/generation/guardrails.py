import re
from typing import List, Tuple
from langchain_core.documents import Document

class Guardrails:
    """
    Executes security guardrails: checks for prompt injection in inputs
    and verifies grounding (hallucination checks) in outputs.
    """
    INJECTION_KEYWORDS = [
        r"ignore\s+(?:all\s+)?previous\s+instructions",
        r"disregard\s+(?:all\s+)?prior\s+prompts",
        r"you\s+must\s+forget",
        r"jailbreak",
        r"system\s+prompt\s+override",
        r"act\s+as\s+a\s+dan",
        r"bypass\s+restrictions"
    ]

    def validate_input(self, query: str) -> Tuple[bool, str]:
        """
        Validates user query against prompt injection patterns.
        Returns (is_safe, error_message)
        """
        for pattern in self.INJECTION_KEYWORDS:
            if re.search(pattern, query, re.IGNORECASE):
                return False, "[GUARDRAIL VIOLATION] Suspicious query pattern detected. Prompt injection attempt blocked."
        return True, ""

    def validate_groundedness(self, answer: str, context_docs: List[Document]) -> Tuple[bool, str]:
        """
        Validates if the generated answer is grounded in the retrieved documents.
        Checks for semantic keyword grounding.
        """
        if not context_docs:
            # If no context was found, and the model didn't say it doesn't know, it might be hallucinating
            know_not_keywords = ["cannot find", "do not have", "no information", "cannot answer", "i don't know", "error"]
            if any(kw in answer.lower() for kw in know_not_keywords):
                return True, "" # Acknowledged ignorance is grounded
            return False, "[GUARDRAIL WARNING] The answer is generated without any retrieved source documents."

        # simple heuristic check: if the answer is telling the user "Yes, you can do this" or "No, you cannot"
        # make sure we verify that the nouns/key concepts (like password, consent, gdpr) in the answer actually exist in context.
        # Check if the answer claims a policy violation, but none of the documents contain words like "violation", "must not", "shall not", "under no circumstances", "plaintext", etc.
        answer_lower = answer.lower()
        context_text = " ".join([doc.page_content.lower() for doc in context_docs])
        
        # Extract nouns/keywords from answer to see if they exist in the context
        # (e.g. if the model talks about 'Argon2' but 'argon2' is nowhere in the context, flag a groundedness warning)
        special_terms = ["argon2", "bcrypt", "pbkdf2", "gdpr", "soc2", "iso27001", "owasp", "md5", "sha1"]
        for term in special_terms:
            if term in answer_lower and term not in context_text:
                return False, f"[GUARDRAIL WARNING] Hallucination warning: Answer contains specific term '{term}' which is not in the source documents."

        return True, ""
