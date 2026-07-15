import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from src.ingestion.loader import load_folder
from src.ingestion.chunker import chunk_documents
from src.embedding.embedder import embed_chunks
from src.retrieval.vector_store import store_chunks

RAW_FOLDER = "data/raw"
BATCH_SIZE = 100

def main():
    print(f"Chargement des documents depuis {RAW_FOLDER} ...")
    docs = load_folder(RAW_FOLDER)
    print(f"{len(docs)} documents chargés")

    print("Chunking ...")
    chunks = chunk_documents(docs)
    print(f"{len(chunks)} chunks générés")

    print("Embedding + stockage (par lots) ...")
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        batch = embed_chunks(batch)
        store_chunks(batch)
        print(f"  {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)} chunks traités")

    print("Ingestion terminée.")

if __name__ == "__main__":
    main()