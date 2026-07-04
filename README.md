# RAG Starter KMS

> Système de questions-réponses intelligent sur corpus interne SFM Technologies  
> Réponses sourcées avec citations de documents — zéro hallucination

**Stagiaire :** Wassim Ferchichi — École Polytechnique de Tunisie  
**Encadrante :** Mme Maroua Salhi  
**Entreprise :** SFM Technologies  
**Période :** Été 2026

---

## Stack technique

| Couche | Outil |
|--------|-------|
| Ingestion | PyMuPDF + RecursiveCharacterTextSplitter |
| Embedding | paraphrase-multilingual-MiniLM-L12-v2 |
| Vector Store | ChromaDB |
| Orchestration | LangChain |
| LLM | Groq API — llama-3.3-70b-versatile |
| Backend | FastAPI + Pydantic |
| UI | Streamlit |
| Évaluation | RAGAS |

---

## Structure du projet

```
rag-starter-kms/
├── src/
│   ├── ingestion/       # PyMuPDF — parsing et chunking des documents
│   ├── embedding/       # Modèle d'embedding multilingue
│   ├── retrieval/       # Recherche vectorielle ChromaDB
│   ├── generation/      # Pipeline LangChain + Groq LLM
│   ├── api/             # FastAPI endpoints
│   └── evaluation/      # Métriques RAGAS
├── frontend/            # Interface Streamlit
├── data/
│   ├── raw/             # Documents originaux (PDF, Word)
│   └── processed/       # Chunks indexés
├── tests/               # Tests unitaires pytest
├── notebooks/           # Expérimentations Jupyter
├── docs/                # Documentation technique
├── scripts/             # Scripts utilitaires (ingest, reset DB...)
├── .env.example         # Variables d'environnement (template)
├── requirements.txt     # Dépendances Python
└── README.md
```

---

## Installation

```bash
# 1. Cloner le repo
git clone https://github.com/wassimferchichi/rag-starter-kms.git
cd rag-starter-kms

# 2. Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Configurer les variables d'environnement
cp .env.example .env
# Remplir GROQ_API_KEY dans .env

# 5. Lancer le backend
uvicorn src.api.main:app --reload

# 6. Lancer l'interface
streamlit run frontend/app.py
```

---

## Variables d'environnement

```env
GROQ_API_KEY=your_groq_api_key_here
CHROMA_DB_PATH=./data/chroma_db
EMBEDDING_MODEL=paraphrase-multilingual-MiniLM-L12-v2
LLM_MODEL=llama-3.3-70b-versatile
CHUNK_SIZE=500
CHUNK_OVERLAP=50
TOP_K_RESULTS=5
```

---

## Branches

| Branche | Rôle |
|---------|------|
| `main` | Code stable validé |
| `develop` | Intégration en cours |
| `feature/ingestion` | Pipeline ingestion docs |
| `feature/retrieval` | Recherche vectorielle |
| `feature/api` | Endpoints FastAPI |
| `feature/ui` | Interface Streamlit |
| `feature/evaluation` | Métriques RAGAS |

---

## Évaluation (RAGAS)

| Métrique | Description | Cible |
|----------|-------------|-------|
| Faithfulness | Réponse fidèle aux sources | > 0.85 |
| Answer Relevancy | Réponse pertinente à la question | > 0.80 |
| Context Recall | Bons passages récupérés | > 0.75 |
| Context Precision | Passages utiles parmi récupérés | > 0.80 |

---

## Roadmap

- [x] Semaine 1 — Cadrage & setup environnement
- [ ] Semaine 2 — Pipeline ingestion (PyMuPDF + chunking)
- [ ] Semaine 3 — Indexation & retrieval (ChromaDB)
- [ ] Semaine 4 — Intégration LLM + pipeline E2E
- [ ] Semaine 5 — Retrieval avancé (reranking, hybrid search)
- [ ] Semaine 6 — Interface utilisateur (Streamlit)
- [ ] Semaine 7 — Évaluation RAGAS & tests
- [ ] Semaine 8 — Documentation & livraison finale
