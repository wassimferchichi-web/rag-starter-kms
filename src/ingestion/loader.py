import fitz
import os
from typing import List, Dict
from docx import Document
import openpyxl

def load_pdf(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")
    documents = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if text:
            documents.append({"text": text, "metadata": {"source": os.path.basename(file_path), "page": page_num + 1, "total_pages": len(doc)}})
    doc.close()
    return documents

def load_docx(file_path: str) -> List[Dict]:
    doc = Document(file_path)
    documents = []
    source = os.path.basename(file_path)

    paragraph_blocks = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    if paragraph_blocks:
        documents.append({
            "text": "\n".join(paragraph_blocks),
            "metadata": {"source": source, "page": 1, "total_pages": 1}
        })

    for table_num, table in enumerate(doc.tables, start=1):
        headers = [cell.text.strip() for cell in table.rows[0].cells] if table.rows else []
        for row_num, row in enumerate(table.rows[1:] if len(table.rows) > 1 else table.rows, start=1):
            cells = [cell.text.strip() for cell in row.cells]
            pairs = []
            for header, cell in zip(headers, cells):
                if cell:
                    pairs.append(f"{header}: {cell}" if header else cell)
            if not pairs:
                pairs = [c for c in cells if c]
            if pairs:
                documents.append({
                    "text": " | ".join(pairs),
                    "metadata": {"source": source, "page": 1, "total_pages": 1, "table": table_num, "row": row_num}
                })

    return documents

def load_xlsx(file_path: str) -> List[Dict]:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    documents = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            continue
        headers = [str(h).strip() if h is not None else "" for h in rows[0]]
        for row_num, row in enumerate(rows[1:], start=2):
            pairs = []
            for header, cell in zip(headers, row):
                if cell is not None and str(cell).strip():
                    pairs.append(f"{header}: {cell}" if header else str(cell))
            if pairs:
                row_text = " | ".join(pairs)
                documents.append({
                    "text": row_text,
                    "metadata": {"source": os.path.basename(file_path), "page": 1, "total_pages": 1, "sheet": sheet, "row": row_num}
                })
    return documents

def load_file(file_path: str) -> List[Dict]:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return load_pdf(file_path)
    elif ext == ".docx":
        return load_docx(file_path)
    elif ext == ".xlsx":
        return load_xlsx(file_path)
    return []

def load_folder(folder_path: str) -> List[Dict]:
    all_docs = []
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            if filename.endswith((".pdf", ".docx", ".xlsx")):
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, folder_path).replace(os.sep, "/")
                print(f"Chargement : {filename}")
                docs = load_file(file_path)
                for d in docs:
                    d["metadata"]["path"] = rel_path
                all_docs.extend(docs)
    return all_docs