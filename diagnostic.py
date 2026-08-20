import sys
sys.path.insert(0, ".")

from src.embedding.embedder import embed_query
from src.retrieval.hybrid_search import hybrid_search
from src.retrieval.reranker import rerank
from src.document_search.searcher import _dedupe_results

query = "SMQ-FOR-092-A"
query_vec = embed_query(query)

candidates = hybrid_search(query, query_vec, candidate_pool=25)
print(f"1. Après hybrid_search (fusion dense+BM25) : {len(candidates)} candidats")

reranked = rerank(query, candidates, top_k=5)
print(f"2. Après rerank (top_k=5)                   : {len(reranked)} candidats")

deduped = _dedupe_results(reranked)
print(f"3. Après dedup                              : {len(deduped)} candidats")

if len(deduped) < len(reranked):
    print()
    print("Clés de dédup des résultats AVANT dedup (pour voir lesquels sont traités comme doublons) :")
    for r in reranked:
        m = r["metadata"]
        key = (m.get("source"), m.get("page"), m.get("table"), m.get("row"), m.get("sheet"))
        print(f"  {key}  ->  {r['text'][:70]}")