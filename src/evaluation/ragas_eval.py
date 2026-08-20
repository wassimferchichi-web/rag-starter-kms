import os
import csv
import time
import requests
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import HuggingfaceEmbeddings
from ragas.metrics import faithfulness, context_precision, context_recall, AnswerRelevancy
from langchain_openai import ChatOpenAI

API_URL = "http://127.0.0.1:8000"
K = 5
RESULTS_PATH = Path(__file__).resolve().parent.parent.parent / "ragas_results.csv"
METRIC_COLUMNS = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
CSV_COLUMNS = ["question", "answer", "contexts", "ground_truth"] + METRIC_COLUMNS

SLEEP_BETWEEN_QUESTIONS = 20

TEST_SET = [
    {
        "question": "Quel est le délai de traitement d'une réclamation client ?",
        "ground_truth": "L'accusé de réception est envoyé sous 48h ouvrées après réception de la réclamation, et le délai global de traitement doit être inférieur ou égal à 15 jours ouvrés."
    },
    {
        "question": "Qui approuve le rapport de revue de direction ?",
        "ground_truth": "Le rapport de revue de direction est approuvé par la Direction Générale."
    },
    {
        "question": "Quel est le taux cible de réalisation des actions issues de la revue de direction ?",
        "ground_truth": "Le taux de réalisation des actions doit être supérieur ou égal à 80% au terme des délais fixés. Si le taux est inférieur à 80%, une non-conformité doit être ouverte."
    },
    {
        "question": "À quelle fréquence les accès sont-ils revus dans la procédure propriété client ?",
        "ground_truth": "Les accès font l'objet d'une revue trimestrielle, avec un PV de revue produit dans les 5 jours après la fin de chaque trimestre."
    },
    {
        "question": "Quel est le taux cible de documents approuvés dans les délais dans la gestion documentaire ?",
        "ground_truth": "Le taux de documents approuvés dans les délais doit être supérieur ou égal à 95%, mesuré trimestriellement."
    },
    {
        "question": "Quelle est la référence et la version du Programme d'Audit Interne Annuel 2026 ?",
        "ground_truth": "La référence est SMQ-FOR-092-A, version V02, émis en juin 2026."
    },
]


class DailyQuotaExhausted(Exception):
    """Levée quand Groq indique explicitement un dépassement de quota par JOUR (TPD), pas par minute."""
    pass


def classify_error(msg: str) -> str:
    lower = msg.lower()
    if "per day" in lower or "tpd" in lower:
        return "QUOTA_JOUR"
    if "per minute" in lower or "tpm" in lower or "429" in msg or "rate_limit" in lower:
        return "QUOTA_MINUTE"
    return "ERREUR"


def get_answer_and_contexts(question: str):
    query_response = requests.post(f"{API_URL}/query", json={"question": question, "k": K}, timeout=120)
    query_response.raise_for_status()
    answer = query_response.json()["answer"]

    search_response = requests.get(f"{API_URL}/search", params={"q": question, "k": K}, timeout=120)
    search_response.raise_for_status()
    contexts = [r["text"] for r in search_response.json()["results"]]

    return answer, contexts


def load_already_done() -> set:
    if not RESULTS_PATH.exists():
        return set()
    done = set()
    with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if all(row.get(m, "").strip() != "" for m in METRIC_COLUMNS):
                done.add(row["question"])
    return done


def append_row(row: dict):
    file_exists = RESULTS_PATH.exists()
    with open(RESULTS_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def build_evaluators():
    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("LLM_MODEL", "openai/gpt-oss-120b"),
        temperature=0
    ))
    evaluator_embeddings = HuggingfaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    answer_relevancy = AnswerRelevancy(strictness=1)
    return evaluator_llm, evaluator_embeddings, answer_relevancy


def evaluate_one_question(item, evaluator_llm, evaluator_embeddings, answer_relevancy):
    try:
        answer, contexts = get_answer_and_contexts(item["question"])
    except Exception as e:
        row = {"question": item["question"], "answer": "", "contexts": [], "ground_truth": item["ground_truth"]}
        for m in METRIC_COLUMNS:
            row[m] = ""
        return row, f"ERREUR_API: {str(e)[:200]}"

    dataset = Dataset.from_dict({
        "question": [item["question"]],
        "answer": [answer],
        "contexts": [contexts],
        "ground_truth": [item["ground_truth"]],
    })

    run_config = RunConfig(timeout=300, max_retries=4, max_wait=60, max_workers=1)

    try:
        result = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
            run_config=run_config,
            raise_exceptions=True,
        )
        scores = result.to_pandas().iloc[0]
        row = {
            "question": item["question"],
            "answer": answer,
            "contexts": contexts,
            "ground_truth": item["ground_truth"],
        }
        for m in METRIC_COLUMNS:
            row[m] = scores.get(m, "")
        return row, None

    except Exception as e:
        msg = str(e)
        error_type = classify_error(msg)
        row = {
            "question": item["question"],
            "answer": answer,
            "contexts": contexts,
            "ground_truth": item["ground_truth"],
        }
        for m in METRIC_COLUMNS:
            row[m] = ""
        return row, f"{error_type}: {msg[:200]}"


def main():
    already_done = load_already_done()
    if already_done:
        print(f"Reprise : {len(already_done)}/{len(TEST_SET)} questions déjà évaluées avec succès, on les saute.")

    remaining = [item for item in TEST_SET if item["question"] not in already_done]
    if not remaining:
        print("Toutes les questions ont déjà été évaluées avec succès. Rien à faire.")
        return

    evaluator_llm, evaluator_embeddings, answer_relevancy = build_evaluators()

    failures = []
    stopped_early = False
    for i, item in enumerate(remaining):
        print(f"[{i+1}/{len(remaining)}] {item['question']}")
        row, error = evaluate_one_question(item, evaluator_llm, evaluator_embeddings, answer_relevancy)
        append_row(row)

        if error:
            print(f"   -> ÉCHEC : {error}")
            failures.append((item["question"], error))

            if error.startswith("QUOTA_JOUR"):
                print("\n   Quota JOURNALIER Groq épuisé. Arrêt du script maintenant : continuer")
                print("   ne ferait qu'échouer sur les questions restantes sans résultat.")
                print("   Relance le script demain, il reprendra automatiquement où il s'est arrêté.")
                stopped_early = True
                break
        else:
            print("   -> OK")

        if i < len(remaining) - 1:
            time.sleep(SLEEP_BETWEEN_QUESTIONS)

    print("\n--- Résumé ---")
    with open(RESULTS_PATH, newline="", encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))
    for m in METRIC_COLUMNS:
        vals = [float(r[m]) for r in all_rows if r[m].strip() != ""]
        n_missing = len(all_rows) - len(vals)
        mean = sum(vals) / len(vals) if vals else float("nan")
        flag = "  <-- ATTENTION, échantillon réduit" if n_missing > 0 else ""
        print(f"{m}: {len(vals)}/{len(all_rows)} présents, moyenne={mean:.3f}{flag}")

    if stopped_early:
        print(f"\nArrêt anticipé pour quota journalier. Relance le script pour continuer où il s'est arrêté.")
    elif failures:
        print(f"\n{len(failures)} question(s) en échec cette session. Relance le script pour réessayer uniquement celles-ci.")

    print(f"\nRésultats dans {RESULTS_PATH.resolve()}")


if __name__ == "__main__":
    main()