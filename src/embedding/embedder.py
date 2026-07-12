from sentence_transformers import SentenceTransformer
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
