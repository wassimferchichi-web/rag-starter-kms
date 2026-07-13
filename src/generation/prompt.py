from typing import List, Dict

SYSTEM_PROMPT = """Tu es l'assistant documentaire interne de SFM Technologies.
Réponds uniquement à partir du contexte fourni ci-dessous, extrait des documents de l'entreprise.
Si le contexte ne permet pas de répondre à la question, dis clairement que l'information n'est pas disponible dans les documents fournis.
Ne mentionne jamais que tu es un modèle de langage. Réponds en français, de façon claire et concise.
Cite les sources (nom du document et page) pertinentes à la fin de ta réponse."""

def build_context(results: List[Dict]) -> str:
    blocks = []
    for r in results:
        meta = r["metadata"]
        source = meta["source"]
        if "sheet" in meta and "row" in meta:
            location = f"feuille {meta['sheet']}, ligne {meta['row']}"
        else:
            location = f"page {meta['page']}"
        blocks.append(f"[Source: {source}, {location}]\n{r['text']}")
    return "\n\n---\n\n".join(blocks)

def build_prompt(question: str, results: List[Dict]) -> List[Dict]:
    context = build_context(results)
    user_prompt = f"""Contexte documentaire :

{context}

Question : {question}

Réponse :"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]