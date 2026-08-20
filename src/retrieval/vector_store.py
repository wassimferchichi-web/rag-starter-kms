import chromadb
import uuid
from typing import List, Dict, Optional

client = chromadb.PersistentClient(path="data/chroma_db")

def get_collection(name: str = "rag_kms"):
    return client.get_or_create_collection(name=name)

def store_chunks(chunks: List[Dict], collection_name: str = "rag_kms"):
    collection = get_collection(collection_name)
    collection.add(
        ids=[str(uuid.uuid4()) for _ in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks]
    )

def search(query_embedding: List[float], k: int = 5, collection_name: str = "rag_kms",
           where: Optional[Dict] = None) -> List[Dict]:
    """
    `where` : filtre ChromaDB sur les métadonnées, ex. {"status": "obsolete"}.
    Gain rapide #1 (filtrage par statut du document, EF-DOC-02) : passer
    where={"status": <valeur>} pour ne récupérer que les documents dans cet état.

    `id` est inclus dans chaque résultat : c'est la clé utilisée pour fusionner
    ce retrieval dense avec le retrieval lexical BM25 (Reciprocal Rank Fusion).
    """
    collection = get_collection(collection_name)
    query_kwargs = {"query_embeddings": [query_embedding], "n_results": k}
    if where:
        query_kwargs["where"] = where
    results = collection.query(**query_kwargs)
    return [
        {
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "score": results["distances"][0][i],
        }
        for i in range(len(results["documents"][0]))
    ]

def get_all_documents(collection_name: str = "rag_kms") -> Dict[str, List]:
    """
    Récupère tout le corpus (ids, textes, métadonnées) — utilisé pour construire
    l'index BM25 en mémoire (recherche lexicale), qui n'a pas d'équivalent
    natif dans ChromaDB (fait pour la recherche vectorielle, pas par mots-clés).
    """
    collection = get_collection(collection_name)
    result = collection.get(include=["documents", "metadatas"])
    return {"ids": result["ids"], "documents": result["documents"], "metadatas": result["metadatas"]}

def reset_collection(collection_name: str = "rag_kms"):
    client.delete_collection(collection_name)