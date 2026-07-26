import os
import time
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from src.embedding.embedder import embed_query
from src.retrieval.vector_store import search
from src.retrieval.reranker import rerank
from src.generation.prompt import build_prompt

MODELS = [
    "llama-3.3-70b-versatile",
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3-32b",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "moonshotai/kimi-k2-instruct",
    "gemma2-9b-it",
]

QUESTIONS = [
    "Quels sont les postes clés de SFM ?",
    "Qui approuve le rapport de revue de direction ?",
]

def get_context(question, k=8, candidate_pool=25):
    query_vec = embed_query(question)
    candidates = search(query_vec, k=candidate_pool)
    return rerank(question, candidates, top_k=k)

def ask_model(model_name, question, results):
    messages = build_prompt(question, results)
    llm = ChatGroq(model=model_name, temperature=0, api_key=os.getenv("GROQ_API_KEY"))
    try:
        start = time.time()
        response = llm.invoke([
            SystemMessage(content=messages[0]["content"]),
            HumanMessage(content=messages[1]["content"])
        ])
        elapsed = time.time() - start
        return response.content, elapsed, None
    except Exception as e:
        return None, None, str(e)

def main():
    output_lines = []
    for question in QUESTIONS:
        header = f"\n{'=' * 80}\nQUESTION : {question}\n{'=' * 80}"
        print(header)
        output_lines.append(header)

        results = get_context(question)

        for model in MODELS:
            print(f"\n--- {model} ---")
            answer, elapsed, error = ask_model(model, question, results)
            if error:
                block = f"\n--- {model} ---\nERREUR : {error}"
                print(f"ERREUR : {error}")
            else:
                block = f"\n--- {model} ---\n({elapsed:.1f}s)\n{answer}"
                print(f"({elapsed:.1f}s)")
                print(answer)
            output_lines.append(block)
            time.sleep(3)

    with open("model_comparison.md", "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))
    print("\n\nRésultats sauvegardés dans model_comparison.md")

if __name__ == "__main__":
    main()