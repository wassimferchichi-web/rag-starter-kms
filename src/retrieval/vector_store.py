import chromadb
from typing import List, Dict

client = chromadb.PersistentClient(path="data/chroma_db")

def get_collection(name: str = "rag_kms"):
    return client.get_or_create_collection(name=name)

def store_chunks(chunks: List[Dict], collection_name: str = "rag_kms"):
    collection = get_collection(collection_name)
    collection.add(
        ids=[f"{c['metadata']['source']}_p{c['metadata']['page']}_c{c['metadata']['chunk_index']}" for c in chunks],
        embeddings=[c['embedding'] for c in chunks],
        documents=[c['text'] for c in chunks],
        metadatas=[c['metadata'] for c in chunks]
    )

def search(query_embedding: List[float], k: int = 5, collection_name: str = "rag_kms") -> List[Dict]:
    collection = get_collection(collection_name)
    results = collection.query(query_embeddings=[query_embedding], n_results=k)
    chunks = []
    for i in range(len(results['documents'][0])):
        chunks.append({
            'text': results['documents'][0][i],
            'metadata': results['metadatas'][0][i],
            'score': results['distances'][0][i]
        })
    return chunks

def reset_collection(collection_name: str = "rag_kms"):
    client.delete_collection(collection_name)
