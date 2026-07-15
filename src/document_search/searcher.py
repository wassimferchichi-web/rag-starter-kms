from typing import List, Dict
from src.embedding.embedder import embed_query
from src.retrieval.vector_store import search
from src.retrieval.reranker import rerank

def search_documents(query: str, k: int = 10, candidate_pool: int = 20, collection_name: str = "rag_kms") -> List[Dict]:
    query_vec = embed_query(query)
    candidates = search(query_vec, k=candidate_pool, collection_name=collection_name)
    return rerank(query, candidates, top_k=k)