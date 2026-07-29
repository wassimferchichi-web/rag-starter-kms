from sentence_transformers import CrossEncoder
from typing import List, Dict

_model = None

def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    return _model

def rerank(query: str, candidates: List[Dict], top_k: int, threshold: float = 0.3, min_keep: int = 2) -> List[Dict]:
    if not candidates:
        return []
    pairs = [(query, c["text"]) for c in candidates]
    scores = get_reranker().predict(pairs)
    scored = list(zip(candidates, scores))
    scored.sort(key=lambda x: x[1], reverse=True)

    all_scores = [s for _, s in scored]
    lo, hi = min(all_scores), max(all_scores)
    span = hi - lo if hi != lo else 1

    top = scored[:top_k]
    filtered = [c for c, s in top if (s - lo) / span >= threshold]
    if len(filtered) < min_keep:
        filtered = [c for c, _ in top[:min_keep]]
    return filtered