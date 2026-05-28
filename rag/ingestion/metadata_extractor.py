import os
import re
from typing import List, Dict, Any
from langchain_core.documents import Document

class MetadataExtractor:
    """
    Standardizes and enriches chunk metadata with source, section, page, and compliance category.
    """
    # Regex to detect sections, articles, or controls (e.g., "Article 6", "Section 4.3", "Control A.12.4")
    SECTION_REGEXES = [
        re.compile(r"(?:article|art\.)\s*(\d+[a-z]?)", re.IGNORECASE),
        re.compile(r"(?:section|sec\.)\s*(\d+(?:\.\d+)*)", re.IGNORECASE),
        re.compile(r"(?:control|ctrl\.)\s*([a-z]\.\d+(?:\.\d+)*)", re.IGNORECASE),
        re.compile(r"(?:annex|clause)\s*(\d+(?:\.\d+)*)", re.IGNORECASE)
    ]

    @staticmethod
    def detect_category(filename: str) -> str:
        """
        Infers compliance category from filename.
        """
        filename_lower = filename.lower()
        if "gdpr" in filename_lower:
            return "GDPR"
        elif "soc2" in filename_lower or "soc 2" in filename_lower:
            return "SOC2"
        elif "iso27001" in filename_lower or "iso 27001" in filename_lower:
            return "ISO27001"
        elif "owasp" in filename_lower:
            return "OWASP Security Guidelines"
        else:
            return "Company Compliance Guidelines"

    def extract_section(self, text: str) -> str:
        """
        Scan text to find section markers. Returns the first match found, or 'General'.
        """
        for regex in self.SECTION_REGEXES:
            match = regex.search(text)
            if match:
                # Return context matched string (e.g., "Article 6" or "Section 4.3")
                start, end = match.span()
                matched_text = text[start:end].strip()
                # Capitalize nicely
                return matched_text.capitalize()
        return "General"

    def enrich(self, chunks: List[Document]) -> List[Document]:
        """
        Enriches a list of chunked Documents with uniform metadata.
        """
        enriched_chunks = []
        for chunk in chunks:
            # Extract current metadata and path
            meta = dict(chunk.metadata)
            path = meta.get("path") or meta.get("source") or "Unknown"
            filename = os.path.basename(path)
            
            # 1. Clean/set source and path
            meta["source"] = filename
            meta["path"] = path
            
            # 2. Compliance Category
            meta["category"] = self.detect_category(filename)
            
            # 3. Page normalization
            if "page" in meta:
                # Keep page number (1-based from PyPDFLoader, etc.)
                meta["page"] = int(meta["page"]) + 1  # 0-indexed to 1-indexed conversion if necessary (PyPDFLoader is 0-indexed)
            else:
                meta["page"] = 1

            # 4. Search for sections inside text
            meta["section"] = self.extract_section(chunk.page_content)
            
            # Build and append enriched document
            enriched_doc = Document(
                page_content=chunk.page_content,
                metadata=meta
            )
            enriched_chunks.append(enriched_doc)
            
        return enriched_chunks
