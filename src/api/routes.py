from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict
import os, shutil
from src.ingestion.loader import load_file
from src.ingestion.chunker import chunk_documents
from src.embedding.embedder import embed_chunks
from src.retrieval.vector_store import store_chunks
from src.generation.pipeline import generate_answer
from src.document_search.searcher import search_documents

router = APIRouter()
RAW_ROOT = os.path.abspath("data/raw")

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
    docs = load_file(path)
    for d in docs:
        d["metadata"]["path"] = file.filename
    chunks = chunk_documents(docs)
    chunks = embed_chunks(chunks)
    store_chunks(chunks)
    return {"message": f"{file.filename} ingested", "chunks": len(chunks)}

@router.get("/documents/{doc_path:path}")
def get_document(doc_path: str):
    full_path = os.path.abspath(os.path.join(RAW_ROOT, doc_path))
    if not full_path.startswith(RAW_ROOT) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Document introuvable")
    return FileResponse(full_path, filename=os.path.basename(full_path))

@router.get("/search")
def search_endpoint(q: str, k: int = 10):
    results = search_documents(q, k=k)
    return {"results": results}

@router.post("/query")
def query(request: QueryRequest):
    return generate_answer(request.question, k=request.k)