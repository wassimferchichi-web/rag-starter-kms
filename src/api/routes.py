from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict
import os, shutil
from src.ingestion.loader import load_file
from src.ingestion.chunker import chunk_documents
from src.embedding.embedder import embed_chunks
from src.retrieval.vector_store import store_chunks
from src.generation.pipeline import generate_answer

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
    docs = load_file(path)
    chunks = chunk_documents(docs)
    chunks = embed_chunks(chunks)
    store_chunks(chunks)
    return {"message": f"{file.filename} ingested", "chunks": len(chunks)}

@router.post("/query")
def query(request: QueryRequest):
    return generate_answer(request.question, k=request.k)