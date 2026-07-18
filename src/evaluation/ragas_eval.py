import os
import requests
from dotenv import load_dotenv
load_dotenv()

from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import HuggingfaceEmbeddings
from ragas.metrics import faithfulness, context_precision, context_recall, AnswerRelevancy
from langchain_openai import ChatOpenAI

API_URL = "http://127.0.0.1:8000"
K = 4

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

def get_answer_and_contexts(question: str):
    query_response = requests.post(f"{API_URL}/query", json={"question": question, "k": K}, timeout=120)
    query_response.raise_for_status()
    answer = query_response.json()["answer"]

    search_response = requests.get(f"{API_URL}/search", params={"q": question, "k": K}, timeout=120)
    search_response.raise_for_status()
    contexts = [r["text"] for r in search_response.json()["results"]]

    return answer, contexts

def main():
    questions, answers, contexts_list, ground_truths = [], [], [], []

    for item in TEST_SET:
        print(f"Traitement : {item['question']}")
        answer, contexts = get_answer_and_contexts(item["question"])
        questions.append(item["question"])
        answers.append(answer)
        contexts_list.append(contexts)
        ground_truths.append(item["ground_truth"])

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts_list,
        "ground_truth": ground_truths
    })

    evaluator_llm = LangchainLLMWrapper(ChatOpenAI(
        base_url="https://api.groq.com/openai/v1",
        api_key=os.getenv("GROQ_API_KEY"),
        model=os.getenv("LLM_MODEL", "llama-3.3-70b-versatile"),
        temperature=0
    ))
    evaluator_embeddings = HuggingfaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    answer_relevancy = AnswerRelevancy(strictness=1)

    print("Évaluation RAGAS en cours...")
    run_config = RunConfig(timeout=300, max_retries=4, max_wait=120, max_workers=2)
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=run_config
    )

    print(result)
    df = result.to_pandas()
    df.to_csv("ragas_results.csv", index=False)
    print("Résultats détaillés sauvegardés dans ragas_results.csv")

if __name__ == "__main__":
    main()