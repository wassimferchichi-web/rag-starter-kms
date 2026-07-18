# RAG Starter KMS

> Système de questions-réponses intelligent sur le corpus documentaire interne de SFM Technologies
> Réponses sourcées avec citations précises (document, page, ligne) — le système dit explicitement quand il ne sait pas.

**Stagiaire :** Wassim Ferchichi — École Polytechnique de Tunisie
**Encadrante :** Mme Maroua Salhi
**Entreprise :** SFM Technologies
**Période :** Été 2026

---

## Fonctionnalités

- **Ingestion multi-format** : PDF, Word (`.docx`, y compris le contenu des tableaux) et Excel (`.xlsx`, découpé ligne par ligne)
- **Recherche sémantique + reranking** : récupération par embeddings puis reclassement par cross-encoder pour une meilleure précision
- **Génération de réponses (Groq / Llama 3.3 70B)** avec citation explicite des seules sources réellement utilisées
- **Recherche documentaire pure** : consultation directe des passages pertinents sans passer par le LLM
- **Téléchargement des documents sources** depuis l'interface
- **Historique de conversation** et annulation d'une recherche en cours
- **Évaluation objective (RAGAS)** : faithfulness, answer relevancy, context precision, context recall

---

## Architecture

```
Documents (PDF/DOCX/XLSX)
        │
        ▼
   Ingestion (loader.py) — extraction multi-format, tableaux ligne par ligne
        │
        ▼
   Chunking (chunker.py) — découpage récursif par caractères
        │
        ▼
   Embedding (embedder.py) — paraphrase-multilingual-MiniLM-L12-v2
        │
        ▼
   ChromaDB (vector_store.py) — stockage vectoriel local, IDs uuid4
        │
        ▼
   Recherche (search) → pool de candidats élargi
        │
        ▼
   Reranking (reranker.py) — cross-encoder multilingue, classement final
        │
        ├──► Génération (pipeline.py) — Groq Llama 3.3 70B, citations filtrées
        │
        └──► Recherche documentaire (searcher.py) — résultats bruts, sans LLM
```

---

## Stack technique

| Couche | Outil |
|---|---|
| Ingestion | PyMuPDF (PDF), python-docx (Word), openpyxl (Excel) |
| Chunking | LangChain `RecursiveCharacterTextSplitter` |
| Embedding | `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers) |
| Reranking | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` |
| Vector Store | ChromaDB (local, persistant) |
| LLM | Groq API — `llama-3.3-70b-versatile` (via `langchain-groq`) |
| Backend | FastAPI |
| UI | Streamlit |
| Évaluation | RAGAS (environnement virtuel isolé, voir plus bas) |

---

## Structure du projet

```
rag-starter-kms/
├── src/
│   ├── ingestion/         # loader.py (multi-format), chunker.py
│   ├── embedding/         # embedder.py
│   ├── retrieval/         # vector_store.py, reranker.py
│   ├── generation/        # pipeline.py, prompt.py
│   ├── document_search/   # searcher.py — recherche pure sans LLM
│   ├── api/                # main.py, routes.py (FastAPI)
│   └── evaluation/        # ragas_eval.py
├── frontend/
│   └── app.py              # interface Streamlit
├── data/
│   ├── raw/                 # documents sources (non versionné)
│   └── chroma_db/           # base vectorielle (non versionné)
├── ingest_all.py            # ingestion en masse de data/raw
├── requirements.txt          # dépendances de l'application
├── requirements-eval.txt     # dépendances de l'évaluation (environnement séparé)
├── .env.example
└── README.md
```

---

## Installation

```bash
git clone https://github.com/wassimferchichi-web/rag-starter-kms.git
cd rag-starter-kms

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# Créer .env à partir du template et renseigner GROQ_API_KEY
cp .env.example .env
```

Placer les documents à indexer dans `data/raw/` (sous-dossiers autorisés), puis :

```bash
python ingest_all.py
```

Lancer l'application (deux terminaux) :

```bash
uvicorn src.api.main:app --reload
```
```bash
streamlit run frontend/app.py
```

---

## Variables d'environnement

Seules ces variables sont réellement lues par le code (voir `.env.example`) :

```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
LLM_TEMPERATURE=0
```

Les autres paramètres (taille des chunks, chemin ChromaDB, nombre de sources récupérées) sont actuellement codés en dur dans les modules concernés plutôt que configurables — voir le commentaire dans `.env.example` pour le détail des emplacements.

---

## Évaluation (RAGAS)

L'évaluation RAGAS nécessite des versions de `langchain` incompatibles avec celles utilisées par l'application principale. Elle tourne donc dans un **environnement virtuel séparé** :

```bash
python -m venv venv-eval
venv-eval\Scripts\activate
pip install -r requirements-eval.txt
```

Avec l'application déjà lancée (`uvicorn` + `streamlit`, ou au minimum `uvicorn`), dans ce second environnement :

```bash
python src/evaluation/ragas_eval.py
```

Le script interroge l'API en conditions réelles (HTTP), calcule les métriques via un juge LLM (Groq, endpoint compatible OpenAI), et sauvegarde le détail dans `ragas_results.csv`.

| Métrique | Description |
|---|---|
| Faithfulness | La réponse s'appuie-t-elle fidèlement sur les documents, sans invention ? |
| Answer Relevancy | La réponse correspond-elle vraiment à la question posée ? |
| Context Precision | Les passages récupérés sont-ils pertinents ? |
| Context Recall | L'information nécessaire a-t-elle bien été retrouvée ? |

**Limite connue** : le tier gratuit de Groq impose un quota journalier de tokens qui peut être atteint lors d'évaluations répétées dans la même journée (le script fait plusieurs appels LLM par question). En cas d'erreur `rate_limit_exceeded`, attendre le renouvellement du quota avant de relancer.

---

## Limites connues

- Échantillon de test RAGAS volontairement restreint (quelques questions) — à enrichir pour une évaluation statistiquement plus robuste
- Reranking et embedding tournent en local sur CPU (pas de GPU) — latence à prendre en compte sur de gros volumes
- Historique de conversation en mémoire de session Streamlit uniquement, non persisté
- Pas de gestion multi-utilisateur ni d'authentification

---

## Pistes d'amélioration futures

- Rendre les paramètres de chunking/retrieval configurables via `.env`
- Élargir et systématiser le jeu de test RAGAS
- Ajouter une authentification pour un déploiement multi-utilisateur
- Explorer un hybrid search (mot-clé + sémantique) pour les requêtes très spécifiques (références de documents, codes SMQ-FOR-XXX)