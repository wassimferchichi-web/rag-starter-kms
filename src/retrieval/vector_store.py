import chromadb
import hashlib
from typing import List, Dict

client = chromadb.PersistentClient(path="data/chroma_db")

def get_collection(name: str = "rag_kms"):
    return client.get_or_create_collection(name=name)

def _make_id(chunk: Dict) -> str:
    meta = chunk["metadata"]
    base = f"{meta.get('source')}_{meta.get('sheet','')}_{meta.get('row','')}_{meta.get('page')}_{meta.get('chunk_index')}_{chunk['text'][:50]}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()[:32]

def store_chunks(chunks: List[Dict], collection_name: str = "rag_kms"):
    collection = get_collection(collection_name)
    collection.add(
        ids=[_make_id(c) for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks]
    )

def search(query_embedding: List[float], k: int = 5, collection_name: str = "rag_kms") -> List[Dict]:
    collection = get_collection(collection_name)
    results = collection.query(query_embeddings=[query_embedding], n_results=k)
    return [{"text": results["documents"][0][i], "metadata": results["metadatas"][0][i], "score": results["distances"][0][i]} for i in range(len(results["documents"][0]))]

def reset_collection(collection_name: str = "rag_kms"):
    client.delete_collection(collection_name)