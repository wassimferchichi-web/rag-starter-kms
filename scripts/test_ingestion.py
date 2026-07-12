import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.loader import load_pdf
from src.ingestion.chunker import chunk_documents

docs = load_pdf("data/raw/test.pdf")
print(f"Pages chargées : {len(docs)}")
chunks = chunk_documents(docs)
print(f"Chunks générés : {len(chunks)}")
print(f"Chunk 0 : {chunks[0]['text'][:150]}")
print(f"Metadata : {chunks[0]['metadata']}")