from typing import List, Dict, Any

class CitationFormatter:
    """
    Utility to format document source citations into structured markdown format.
    """
    @staticmethod
    def format_sources(sources: List[Dict[str, Any]]) -> str:
        """
        Takes a list of source metadata dicts and formats them into a Markdown citation block.
        """
        if not sources:
            return ""

        markdown_lines = ["\n\n### 📚 Sources & Citations\n"]
        for idx, src in enumerate(sources, 1):
            category = src.get("category", "Compliance")
            filename = src.get("source", "Document")
            section = src.get("section", "General")
            page = src.get("page", 1)
            
            line = f"**{idx}. [{category}] {filename}** - Section: `{section}`, Page: `{page}`"
            markdown_lines.append(line)
            
        return "\n".join(markdown_lines)
        
    @staticmethod
    def append_citations_to_answer(answer: str, sources: List[Dict[str, Any]]) -> str:
        """
        Appends formatted citation block to the end of an LLM-generated answer.
        """
        citation_block = CitationFormatter.format_sources(sources)
        if citation_block:
            return f"{answer}{citation_block}"
        return answer
