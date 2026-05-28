import os
import json
import argparse
from typing import List
from langchain_core.documents import Document

from rag.ingestion.document_loader import DocumentLoader
from rag.ingestion.chunker import DocumentChunker
from rag.ingestion.metadata_extractor import MetadataExtractor
from rag.ingestion.embedder import Embedder

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

class IngestionPipeline:
    """
    Orchestrates the loading, chunking, enrichment, and vector storage of compliance files.
    """
    def __init__(self, raw_dir: str = "data/raw_docs", processed_dir: str = "data/processed_docs"):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        self.loader = DocumentLoader()
        self.chunker = DocumentChunker()
        self.metadata_extractor = MetadataExtractor()
        self.embedder = Embedder()

    def run(self, overwrite: bool = False) -> List[Document]:
        """
        Runs the full ingestion pipeline.
        """
        # Ensure directories
        os.makedirs(self.raw_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)

        # 1. Scan and Load Documents
        raw_files = [
            os.path.join(self.raw_dir, f) 
            for f in os.listdir(self.raw_dir) 
            if os.path.isfile(os.path.join(self.raw_dir, f))
        ]
        
        if not raw_files:
            print(f"[WARNING] No raw files found in: {self.raw_dir}. Please place PDF, DOCX, Markdown, or Text files there.")
            return []

        print(f"[INFO] Found {len(raw_files)} files for ingestion.")
        all_documents = []
        for file_path in raw_files:
            print(f"[INFO] Loading: {file_path}")
            loaded_docs = self.loader.load(file_path)
            all_documents.extend(loaded_docs)

        if not all_documents:
            print("[WARNING] Loaded 0 documents. Ingestion aborted.")
            return []

        # 2. Chunk Documents
        chunks = self.chunker.split(all_documents)

        # 3. Enrich Metadata
        enriched_chunks = self.metadata_extractor.enrich(chunks)

        # 4. Save chunks to local JSON cache (processed_docs/chunks.json)
        chunks_cache_path = os.path.join(self.processed_dir, "chunks.json")
        try:
            chunks_data = [
                {"page_content": doc.page_content, "metadata": doc.metadata}
                for doc in enriched_chunks
            ]
            with open(chunks_cache_path, "w", encoding="utf-8") as f:
                json.dump(chunks_data, f, indent=2, ensure_ascii=False)
            print(f"[INFO] Saved {len(enriched_chunks)} processed chunks to cache: {chunks_cache_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save chunks to JSON cache: {e}")

        # 5. Embed and index in Vector Store
        self.embedder.save_to_vector_store(enriched_chunks, overwrite=overwrite)

        print("[INFO] Ingestion Pipeline complete!")
        return enriched_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run compliance copilot ingestion pipeline.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite the existing vector store.")
    args = parser.parse_args()

    pipeline = IngestionPipeline()
    pipeline.run(overwrite=args.overwrite)
