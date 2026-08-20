import re
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict, Optional

# Gain rapide #4 (EF-GEN-04, chapitre 10 — matrice de couverture ISO).
# Détecte des mentions de clause ISO 9001 du type "§8.4.1", "clause 8.7",
# "article 9.3", et les normalise au niveau majeur.mineur (8.4.1 -> 8.4)
# car c'est le niveau de granularité habituellement utilisé pour filtrer
# (les corpus SFM eux-mêmes nomment leurs fichiers "§8.4.1", "Clause 6.2"...).
# Limite assumée : un seul chunk peut légitimement toucher plusieurs
# clauses ("§8.2.1 à §8.2.4") — on ne retient que la première détectée,
# comme pour la détection de statut (heuristique, pas un champ structuré).
ISO_CLAUSE_PATTERN = re.compile(
    r"(?:§\s?|\bclause\s+n?°?\s*|\barticle\s+)(\d{1,2}(?:\.\d{1,2}){0,3})",
    re.IGNORECASE,
)


def normalize_clause(raw: str) -> str:
    """Ramène une clause détectée ou saisie par l'utilisateur au niveau
    majeur.mineur : '8.4.1' -> '8.4', '9' reste '9'."""
    parts = raw.strip().split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else parts[0]


def detect_iso_clause(text: str) -> Optional[str]:
    match = ISO_CLAUSE_PATTERN.search(text)
    if not match:
        return None
    return normalize_clause(match.group(1))


def chunk_documents(documents: List[Dict], chunk_size: int = 500, chunk_overlap: int = 50) -> List[Dict]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap, separators=["\n\n", "\n", ".", " ", ""])
    chunks = []
    for doc in documents:
        splits = splitter.split_text(doc["text"])
        for i, split in enumerate(splits):
            iso_clause = detect_iso_clause(split) or ""  # ChromaDB rejette None
            chunks.append({"text": split, "metadata": {**doc["metadata"], "chunk_index": i, "iso_clause": iso_clause}})
    return chunks