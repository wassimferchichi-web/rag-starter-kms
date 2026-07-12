import os

os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
os.makedirs("src/ingestion", exist_ok=True)
os.makedirs("src/embedding", exist_ok=True)
os.makedirs("src/retrieval", exist_ok=True)
os.makedirs("src/api", exist_ok=True)
os.makedirs("frontend", exist_ok=True)

files = {}

files["src/ingestion/loader.py"] = '''import fitz
import os
from typing import List, Dict

def load_pdf(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")
    documents = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        documents.append({"text": text, "metadata": {"source": os.path.basename(file_path), "page": page_num + 1, "total_pages": len(doc)}})
    doc.close()
    return documents

def load_folder(folder_path: str) -> List[Dict]:
    all_docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            all_docs.extend(load_pdf(os.path.join(folder_path, filename)))
    return all_docs
'''

files["src/ingestion/chunker.py"] = '''from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict

def chunk_documents(documents: List[Dict], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\\n\\n", "\\n", ".", " ", ""])
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["text"])
        for i, split in enumerate(splits):
            chunks.append({"text": split, "metadata": {**doc["metadata"], "chunk_index": i}})
    return chunks
'''

files["src/embedding/embedder.py"] = '''from sentence_transformers import SentenceTransformer
from typing import List, Dict

model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

def embed_chunks(chunks: List[Dict]) -> List[Dict]:
    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)
    for i, chunk in enumerate(chunks):
        chunk["embedding"] = embeddings[i].tolist()
    return chunks

def embed_query(query: str) -> List[float]:
    return model.encode(query).tolist()
'''

files["src/retrieval/vector_store.py"] = '''import chromadb
from typing import List, Dict

client = chromadb.PersistentClient(path="data/chroma_db")

def get_collection(name: str = "rag_kms"):
    return client.get_or_create_collection(name=name)

def store_chunks(chunks: List[Dict], collection_name: str = "rag_kms"):
    collection = get_collection(collection_name)
    collection.add(
        ids=[f"{c['metadata']['source']}_p{c['metadata']['page']}_c{c['metadata']['chunk_index']}" for c in chunks],
        embeddings=[c["embedding"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks]
    )

def search(query_embedding: List[float], k: int = 5, collection_name: str = "rag_kms") -> List[Dict]:
    collection = get_collection(collection_name)
    results = collection.query(query_embeddings=[query_embedding], n_results=k)
    return [{"text": results["documents"][0][i], "metadata": results["metadatas"][0][i], "score": results["distances"][0][i]} for i in range(len(results["documents"][0]))]

def reset_collection(collection_name: str = "rag_kms"):
    client.delete_collection(collection_name)
'''

files["src/api/routes.py"] = '''from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict
import os, shutil
from src.ingestion.loader import load_pdf
from src.ingestion.chunker import chunk_documents
from src.embedding.embedder import embed_chunks, embed_query
from src.retrieval.vector_store import store_chunks, search

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    k: int = 5

@router.get("/health")
def health():
    return {"status": "ok", "service": "RAG Starter KMS"}

@router.post("/ingest")
def ingest(file: UploadFile = File(...)):
    path = f"data/raw/{file.filename}"
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    docs = load_pdf(path)
    chunks = chunk_documents(docs)
    chunks = embed_chunks(chunks)
    store_chunks(chunks)
    return {"message": f"{file.filename} ingested", "chunks": len(chunks)}

@router.post("/query")
def query(request: QueryRequest):
    query_vec = embed_query(request.question)
    results = search(query_vec, k=request.k)
    context = "\\n\\n".join([f"[{r['metadata']['source']} p.{r['metadata']['page']}] {r['text']}" for r in results])
    return {"answer": context, "sources": [r["metadata"] for r in results]}
'''

files["src/api/main.py"] = '''from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="RAG Starter KMS", version="1.0.0")
app.include_router(router)
'''

files["frontend/app.py"] = '''import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RAG Starter KMS", page_icon="🤖", layout="wide")
st.title("🤖 RAG Starter KMS")
st.caption("Système de questions-réponses intelligent — SFM Technologies")

tab1, tab2 = st.tabs(["💬 Q&R", "📄 Ingérer un document"])

with tab1:
    st.subheader("Posez votre question")
    question = st.text_input("Votre question", placeholder="Ex: Quel est le processus qualité ?")
    k = st.slider("Nombre de sources", 1, 10, 5)
    if st.button("Envoyer", type="primary"):
        if question:
            with st.spinner("Recherche en cours..."):
                response = requests.post(f"{API_URL}/query", json={"question": question, "k": k})
                if response.status_code == 200:
                    data = response.json()
                    st.markdown("### Réponse")
                    st.write(data["answer"])
                    st.markdown("### Sources")
                    for source in data["sources"]:
                        st.info(f"📄 {source['source']} — Page {source['page']}")
                else:
                    st.error("Erreur lors de la requête")

with tab2:
    st.subheader("Ingérer un document PDF")
    uploaded_file = st.file_uploader("Choisir un fichier PDF", type=["pdf"])
    if uploaded_file and st.button("Ingérer", type="primary"):
        with st.spinner("Ingestion en cours..."):
            response = requests.post(f"{API_URL}/ingest", files={"file": uploaded_file})
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ {data['message']} — {data['chunks']} chunks créés")
            else:
                st.error("Erreur lors de l'ingestion")
'''

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"✅ {path}")

print("\nTous les fichiers restaurés avec succès !")