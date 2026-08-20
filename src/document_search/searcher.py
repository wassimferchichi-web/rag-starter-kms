from typing import List, Dict, Optional
from src.embedding.embedder import embed_query
from src.retrieval.hybrid_search import hybrid_search
from src.retrieval.reranker import rerank

def _result_key(r: Dict) -> tuple:
    """Même logique que _source_key dans pipeline.py : identifie un résultat
    par son emplacement physique (fichier + page/tableau+ligne/feuille+ligne),
    pas par son chunk_index — deux chunks au même endroit sont doublon."""
    meta = r.get("metadata", {})
    return (
        meta.get("source"),
        meta.get("page"),
        meta.get("table"),
        meta.get("row"),
        meta.get("sheet"),
    )

def _dedupe_results(results: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    for r in results:
        key = _result_key(r)
        if key not in seen:
            seen.add(key)
            deduped.append(r)
    return deduped

def search_documents(query: str, k: int = 10, candidate_pool: int = 25, collection_name: str = "rag_kms",
                      where: Optional[Dict] = None) -> List[Dict]:
    """
    `where` : filtre ChromaDB propagé depuis /search (ex. {"status": "obsolete"}).
    Recherche hybride (dense + BM25 lexical, fusionnés par RRF) avant le
    reranking cross-encoder — corrige la faiblesse des embeddings sur les
    termes exacts (codes de référence, acronymes, identifiants).
    """
    query_vec = embed_query(query)
    candidates = hybrid_search(query, query_vec, candidate_pool=candidate_pool, collection_name=collection_name, where=where)
    results = rerank(query, candidates, top_k=k)
    return _dedupe_results(results)