from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import os, shutil, csv, datetime, json
from pathlib import Path
from src.ingestion.loader import load_file
from src.ingestion.chunker import chunk_documents, normalize_clause
from src.embedding.embedder import embed_chunks
from src.retrieval.vector_store import store_chunks
from src.generation.pipeline import generate_answer
from src.document_search.searcher import search_documents

router = APIRouter()
RAW_ROOT = os.path.abspath("data/raw")

VALID_STATUSES = {"en_vigueur", "obsolete", "en_revision"}

QA_LOG_PATH = Path("data/logs/qa_log.csv")
QA_LOG_COLUMNS = ["timestamp", "question", "n_sources", "sources", "answer_preview"]


def log_qa(question: str, answer: str, sources: List[Dict]):
    QA_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = QA_LOG_PATH.exists()
    compact_sources = [
        {k: s.get(k) for k in ("source", "page", "table", "row", "sheet", "path", "status") if s.get(k) is not None}
        for s in sources
    ]
    row = {
        "timestamp": datetime.datetime.now().isoformat(timespec="seconds"),
        "question": question,
        "n_sources": len(sources),
        "sources": json.dumps(compact_sources, ensure_ascii=False),
        "answer_preview": answer[:200].replace("\n", " "),
    }
    with open(QA_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=QA_LOG_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def read_qa_log() -> List[Dict]:
    if not QA_LOG_PATH.exists():
        return []
    with open(QA_LOG_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_qa_log(rows: List[Dict]):
    fieldnames = list(rows[0].keys()) if rows else QA_LOG_COLUMNS
    with open(QA_LOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class QueryRequest(BaseModel):
    question: str
    k: int = 5
    history: List[Dict[str, str]] = []

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
    filename = os.path.basename(full_path)
    return FileResponse(full_path, filename=filename, content_disposition_type="inline")

@router.get("/search")
def search_endpoint(q: str, k: int = 10, statut: Optional[str] = None, clause: Optional[str] = None):
    where_clauses = []
    if statut:
        if statut not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"statut invalide, attendu parmi {sorted(VALID_STATUSES)}")
        where_clauses.append({"status": statut})
    if clause:
        where_clauses.append({"iso_clause": normalize_clause(clause)})

    if not where_clauses:
        where = None
    elif len(where_clauses) == 1:
        where = where_clauses[0]
    else:
        where = {"$and": where_clauses}

    results = search_documents(q, k=k, where=where)
    return {"results": results}

@router.post("/query")
def query(request: QueryRequest):
    result = generate_answer(request.question, history=request.history, k=request.k)
    log_qa(request.question, result.get("answer", ""), result.get("sources", []))
    return result


@router.get("/journal")
def get_journal():
    rows = read_qa_log()
    entries = []
    for idx, row in enumerate(rows):
        try:
            sources = json.loads(row.get("sources", "[]"))
        except (json.JSONDecodeError, TypeError):
            sources = []
        entries.append({
            "id": idx,
            "timestamp": row.get("timestamp", ""),
            "question": row.get("question", ""),
            "n_sources": row.get("n_sources", "0"),
            "sources": sources,
            "answer_preview": row.get("answer_preview", ""),
        })
    entries.sort(key=lambda e: e["timestamp"], reverse=True)
    return {"entries": entries}

@router.delete("/journal/{entry_id}")
def delete_journal_entry(entry_id: int):
    rows = read_qa_log()
    if not (0 <= entry_id < len(rows)):
        raise HTTPException(status_code=404, detail="Entrée introuvable")
    del rows[entry_id]
    write_qa_log(rows)
    return {"message": "Entrée supprimée"}

@router.get("/journal/download")
def download_journal():
    if not QA_LOG_PATH.exists():
        raise HTTPException(status_code=404, detail="Aucun journal disponible")
    return FileResponse(QA_LOG_PATH, filename="qa_log.csv", media_type="text/csv")