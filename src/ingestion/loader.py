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
    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return [{"text": text, "metadata": {"source": os.path.basename(file_path), "page": 1, "total_pages": 1}}]

def load_xlsx(file_path: str) -> List[Dict]:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    documents = []
    for sheet in wb.sheetnames:
        ws = wb[sheet]
        rows = []
        for row in ws.iter_rows(values_only=True):
            row_text = " | ".join([str(cell) for cell in row if cell is not None])
            if row_text.strip():
                rows.append(row_text)
        if rows:
            documents.append({"text": "\n".join(rows), "metadata": {"source": os.path.basename(file_path), "page": 1, "total_pages": 1, "sheet": sheet}})
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
                print(f"Chargement : {filename}")
                all_docs.extend(load_file(file_path))
    return all_docs