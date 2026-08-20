import re
from typing import List, Dict, Optional
from rank_bm25 import BM25Okapi
from src.retrieval.vector_store import search as dense_search, get_all_documents

WORD_PATTERN = re.compile(r"\w+", re.UNICODE)

# Motif de code exact (référence documentaire, clause ISO) — mêmes critères
# que dans reranker.py. Sert à décider QUAND activer BM25 : le lexical aide
# sur les codes exacts, mais dégrade la précision sur les questions en
# langage naturel ordinaires (trop de faux positifs à recouvrement de mots
# communs). Constaté empiriquement : ne pas l'activer par défaut partout.
CODE_LIKE_PATTERN = re.compile(r"\b[A-Z]{2,6}(?:-[A-Z0-9]{2,6}){1,3}\b|§\s?\d")

# Constante standard de la littérature (Cormack et al., 2009) pour le
# Reciprocal Rank Fusion — pas une valeur à retuner en priorité, elle est
# volontairement peu sensible au réglage fin.
RRF_K = 60

_bm25_index = None
_bm25_ids = None
_bm25_documents = None
_bm25_metadatas = None


def _tokenize(text: str) -> List[str]:
    return WORD_PATTERN.findall(text.lower())


def _get_bm25_index(collection_name: str = "rag_kms"):
    """Index BM25 en mémoire, construit une fois par processus (comme le
    modèle cross-encoder dans reranker.py) — ChromaDB n'a pas d'équivalent
    natif pour la recherche lexicale par mots-clés."""
    global _bm25_index, _bm25_ids, _bm25_documents, _bm25_metadatas
    if _bm25_index is None:
        corpus = get_all_documents(collection_name)
        _bm25_ids = corpus["ids"]
        _bm25_documents = corpus["documents"]
        _bm25_metadatas = corpus["metadatas"]
        tokenized_corpus = [_tokenize(doc) for doc in _bm25_documents]
        _bm25_index = BM25Okapi(tokenized_corpus)
    return _bm25_index


def _metadata_matches(meta: Dict, where: Optional[Dict]) -> bool:
    """Réplique en Python la sémantique du `where` ChromaDB (égalité simple,
    ou {"$and": [...]}) pour filtrer les résultats BM25 de la même façon
    que le filtrage appliqué côté retrieval dense."""
    if not where:
        return True
    if "$and" in where:
        return all(_metadata_matches(meta, cond) for cond in where["$and"])
    return all(meta.get(key) == value for key, value in where.items())


def _bm25_search(query: str, k: int, collection_name: str = "rag_kms",
                  where: Optional[Dict] = None) -> List[Dict]:
    index = _get_bm25_index(collection_name)
    scores = index.get_scores(_tokenize(query))

    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for i in ranked:
        if scores[i] <= 0:
            break  # BM25 trié décroissant : score <= 0 = plus aucun terme en commun
        meta = _bm25_metadatas[i]
        if not _metadata_matches(meta, where):
            continue
        results.append({"id": _bm25_ids[i], "text": _bm25_documents[i], "metadata": meta, "score": float(scores[i])})
        if len(results) >= k:
            break
    return results


def hybrid_search(query: str, query_embedding: List[float], candidate_pool: int = 35,
                   collection_name: str = "rag_kms", where: Optional[Dict] = None) -> List[Dict]:
    """
    Fusionne recherche dense et BM25 SEULEMENT si la requête contient un motif
    de type code exact (référence documentaire, clause ISO) — sinon, dense
    seul. Constaté empiriquement (RAGAS) : activer BM25 sur des questions en
    langage naturel ordinaires dégrade context_precision (trop de chunks
    médiocres mais partageant un mot courant remontent via la fusion RRF).
    BM25 reste un vrai gain ciblé sur les codes exacts, pas un gain général.
    """
    if not CODE_LIKE_PATTERN.search(query):
        return dense_search(query_embedding, k=candidate_pool, collection_name=collection_name, where=where)

    dense_results = dense_search(query_embedding, k=candidate_pool, collection_name=collection_name, where=where)
    sparse_results = _bm25_search(query, k=candidate_pool, collection_name=collection_name, where=where)

    rrf_scores: Dict[str, float] = {}
    pool: Dict[str, Dict] = {}

    for rank, r in enumerate(dense_results, start=1):
        rrf_scores[r["id"]] = rrf_scores.get(r["id"], 0.0) + 1.0 / (RRF_K + rank)
        pool[r["id"]] = r

    for rank, r in enumerate(sparse_results, start=1):
        rrf_scores[r["id"]] = rrf_scores.get(r["id"], 0.0) + 1.0 / (RRF_K + rank)
        pool.setdefault(r["id"], r)

    fused_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
    return [pool[cid] for cid in fused_ids[:candidate_pool]]