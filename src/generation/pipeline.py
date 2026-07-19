import os
import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict
from src.embedding.embedder import embed_query
from src.retrieval.vector_store import search
from src.retrieval.reranker import rerank
from src.generation.prompt import build_prompt

_llm = None

def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY manquant dans l'environnement")
        model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
        temperature = float(os.getenv("LLM_TEMPERATURE", 0))
        _llm = ChatGroq(model=model, temperature=temperature, api_key=api_key)
    return _llm

def parse_used_sources(raw_answer: str, results: List[Dict]) -> tuple:
    match = re.search(r"SOURCES_UTILISEES:\s*(.+)\s*$", raw_answer, re.IGNORECASE)
    if not match:
        return raw_answer.strip(), [r["metadata"] for r in results]

    clean_answer = raw_answer[:match.start()].strip()
    used_part = match.group(1).strip().lower()

    if used_part in ("aucune", "none", "aucun"):
        return clean_answer, []

    indices = re.findall(r"\d+", used_part)
    used_sources = []
    for idx_str in indices:
        idx = int(idx_str) - 1
        if 0 <= idx < len(results):
            used_sources.append(results[idx]["metadata"])

    if not used_sources:
        return clean_answer, [r["metadata"] for r in results]

    return clean_answer, used_sources

_answer_cache = {}

def generate_answer(question: str, k: int = 8, candidate_pool: int = 35, collection_name: str = "rag_kms") -> Dict:
    cache_key = (question.strip().lower(), k, collection_name)
    if cache_key in _answer_cache:
        return _answer_cache[cache_key]

    query_vec = embed_query(question)
    candidates = search(query_vec, k=candidate_pool, collection_name=collection_name)
    results = rerank(question, candidates, top_k=k)

    if not results:
        return {
            "answer": "Aucun document pertinent n'a été trouvé pour répondre à cette question.",
            "sources": []
        }

    messages = build_prompt(question, results)
    langchain_messages = [
        SystemMessage(content=messages[0]["content"]),
        HumanMessage(content=messages[1]["content"])
    ]

    llm = get_llm()
    response = llm.invoke(langchain_messages)

    clean_answer, used_sources = parse_used_sources(response.content, results)

    result = {
        "answer": clean_answer,
        "sources": used_sources
    }
    _answer_cache[cache_key] = result
    return result