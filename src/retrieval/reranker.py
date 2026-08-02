from sentence_transformers import CrossEncoder
from typing import List, Dict

_model = None

def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    return _model

def rerank(query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
    if not candidates:
        return []
    pairs = [(query, c["text"]) for c in candidates]
    scores = get_reranker().predict(pairs)
    scored = list(zip(candidates, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:top_k]]