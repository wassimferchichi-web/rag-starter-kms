from fastapi import APIRouter, UploadFile, File
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
    context = "\n\n".join([f"[{r['metadata']['source']} p.{r['metadata']['page']}] {r['text']}" for r in results])
    return {"answer": context, "sources": [r["metadata"] for r in results]}