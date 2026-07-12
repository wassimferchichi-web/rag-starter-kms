import fitz
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
        documents.append({
            "text": text,
            "metadata": {
                "source": os.path.basename(file_path),
                "page": page_num + 1,
                "total_pages": len(doc)
            }
        })
    doc.close()
    return documents

def load_folder(folder_path: str) -> List[Dict]:
    all_docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            all_docs.extend(load_pdf(os.path.join(folder_path, filename)))
    return all_docs