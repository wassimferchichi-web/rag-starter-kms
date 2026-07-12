import fitz
import os
from typing import List, Dict

<<<<<<< HEAD

=======
>>>>>>> feature/retrieval
def load_pdf(file_path: str) -> List[Dict]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Fichier introuvable : {file_path}")
    documents = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
<<<<<<< HEAD
        documents.append({
            "text": text,
            "metadata": {
                "source": os.path.basename(file_path),
                "page": page_num + 1,
                "total_pages": len(doc),
            }
        })
    doc.close()
    return documents


=======
        documents.append({"text": text, "metadata": {"source": os.path.basename(file_path), "page": page_num + 1, "total_pages": len(doc)}})
    doc.close()
    return documents

>>>>>>> feature/retrieval
def load_folder(folder_path: str) -> List[Dict]:
    all_docs = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
<<<<<<< HEAD
            file_path = os.path.join(folder_path, filename)
            print(f"Chargement : {filename}")
            all_docs.extend(load_pdf(file_path))
=======
            all_docs.extend(load_pdf(os.path.join(folder_path, filename)))
>>>>>>> feature/retrieval
    return all_docs
