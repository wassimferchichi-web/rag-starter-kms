import os
import re
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict
from src.embedding.embedder import embed_query
from src.retrieval.hybrid_search import hybrid_search
from src.retrieval.reranker import rerank
from src.generation.prompt import build_prompt, build_condense_messages

_llm = None

def get_llm() -> ChatGroq:
    global _llm
    if _llm is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY manquant dans l'environnement")
        model = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")
        temperature = float(os.getenv("LLM_TEMPERATURE", 0))
        _llm = ChatGroq(model=model, temperature=temperature, api_key=api_key)
    return _llm

def _source_key(meta: Dict) -> tuple:
    """Clé d'identité d'une source pour la déduplication : deux chunks qui
    pointent vers le même emplacement physique (même fichier, même page/
    tableau+ligne/feuille+ligne) sont la même source aux yeux de l'utilisateur,
    même s'ils ont des chunk_index ou des uuid ChromaDB différents."""
    return (
        meta.get("source"),
        meta.get("page"),
        meta.get("table"),
        meta.get("row"),
        meta.get("sheet"),
    )

def _dedupe_sources(metadatas: List[Dict]) -> List[Dict]:
    seen = set()
    deduped = []
    for meta in metadatas:
        key = _source_key(meta)
        if key not in seen:
            seen.add(key)
            deduped.append(meta)
    return deduped

def parse_used_sources(raw_answer: str, results: List[Dict]) -> tuple:
    match = re.search(r"SOURCES_UTILISEES:\s*(.+)\s*$", raw_answer, re.IGNORECASE)
    if not match:
        return raw_answer.strip(), _dedupe_sources([r["metadata"] for r in results])

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
        return clean_answer, _dedupe_sources([r["metadata"] for r in results])

    return clean_answer, _dedupe_sources(used_sources)

def condense_question(question: str, history: List[Dict]) -> str:
    messages = build_condense_messages(question, history)
    llm = get_llm()
    response = llm.invoke([
        SystemMessage(content=messages[0]["content"]),
        HumanMessage(content=messages[1]["content"])
    ])
    return response.content.strip()

_answer_cache = {}

def generate_answer(question: str, history: List[Dict] = None, k: int = 5, candidate_pool: int = 35, collection_name: str = "rag_kms") -> Dict:
    history = history or []

    if not history:
        cache_key = (question.strip().lower(), k, collection_name)
        if cache_key in _answer_cache:
            return _answer_cache[cache_key]

    standalone_question = condense_question(question, history) if history else question

    query_vec = embed_query(standalone_question)
    candidates = hybrid_search(standalone_question, query_vec, candidate_pool=candidate_pool, collection_name=collection_name)
    results = rerank(standalone_question, candidates, top_k=k)

    if not results:
        return {
            "answer": "Aucun document pertinent n'a été trouvé pour répondre à cette question.",
            "sources": []
        }

    messages = build_prompt(question, results, history=history)
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
    if not history:
        cache_key = (question.strip().lower(), k, collection_name)
        _answer_cache[cache_key] = result
    return result