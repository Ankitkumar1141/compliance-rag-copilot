from typing import List
from models.llm_factory import get_llm, MockChatModel
from langchain_core.prompts import ChatPromptTemplate

class QueryTransformer:
    """
    Transforms and expands the user's query into multiple search queries
    optimized for semantic and keyword search.
    """
    def __init__(self, provider: str = None, model_name: str = None):
        self.llm = get_llm(provider, model_name)
        
        self.prompt = ChatPromptTemplate.from_template(
            "You are a compliance search assistant. Your job is to translate a user's compliance question "
            "into 3 distinct, keyword-rich search queries optimized for a compliance database search (supporting both keyword and vector search).\n\n"
            "Original Query: {query}\n\n"
            "Format your response as a simple list of 3 items, one per line. Do not add numbers, bullet points, intro, or explanation.\n"
            "Example output:\n"
            "password hashing argon2 bcrypt\n"
            "OWASP password storage standard\n"
            "storing plain text passwords policy"
        )

    def transform(self, query: str) -> List[str]:
        """
        Expands the input query into 3 search variations. Fallback returns the original query.
        """
        # If it's the MockChatModel, return standard mock expansions
        if isinstance(self.llm, MockChatModel):
            lower_query = query.lower()
            if "password" in lower_query:
                return [
                    query,
                    "password storage requirements",
                    "hashing and encryption standard"
                ]
            elif "gdpr" in lower_query:
                return [
                    query,
                    "GDPR article 6 lawfulness of processing",
                    "personal data processing consent"
                ]
            return [query]

        try:
            # Chain execution
            chain = self.prompt | self.llm
            response = chain.invoke({"query": query})
            
            content = response.content.strip()
            # Split lines and clean
            queries = [q.strip() for q in content.split("\n") if q.strip()]
            
            # Make sure we got at least some output, otherwise fallback
            if not queries:
                return [query]
                
            # Cap to 3 queries and prepend original query to make sure we don't lose the exact match
            final_queries = [query]
            for q in queries[:3]:
                if q.lower() != query.lower():
                    final_queries.append(q)
            return final_queries[:3]
            
        except Exception as e:
            print(f"[ERROR] Failed to transform query: {e}. Falling back to original query.")
            return [query]
