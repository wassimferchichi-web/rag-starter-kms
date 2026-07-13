import os
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict
from src.embedding.embedder import embed_query
from src.retrieval.vector_store import search
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

def generate_answer(question: str, k: int = 5, collection_name: str = "rag_kms") -> Dict:
    query_vec = embed_query(question)
    results = search(query_vec, k=k, collection_name=collection_name)

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

    return {
        "answer": response.content,
        "sources": [r["metadata"] for r in results]
    }