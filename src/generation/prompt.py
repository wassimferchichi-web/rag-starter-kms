from typing import List, Dict

SYSTEM_PROMPT = """Tu es l'assistant documentaire interne de SFM Technologies.
Réponds uniquement à partir du contexte fourni ci-dessous, extrait des documents de l'entreprise. Chaque extrait est numéroté entre crochets, par exemple [1].
Si le contexte ne permet pas de répondre à la question, dis clairement que l'information n'est pas disponible dans les documents fournis.
Ne mentionne jamais que tu es un modèle de langage. Réponds en français, de façon claire et concise. Ne cite pas les sources dans le corps de ta réponse.
Termine impérativement ta réponse par une dernière ligne, seule, au format exact :
SOURCES_UTILISEES: n,n,n
où n,n,n sont les numéros des extraits que tu as réellement utilisés pour répondre. Si aucun extrait n'a été utile, écris SOURCES_UTILISEES: aucune"""

def build_context(results: List[Dict]) -> str:
    blocks = []
    for i, r in enumerate(results, start=1):
        meta = r["metadata"]
        source = meta["source"]
        if "sheet" in meta and "row" in meta:
            location = f"feuille {meta['sheet']}, ligne {meta['row']}"
        else:
            location = f"page {meta['page']}"
        blocks.append(f"[{i}] Source: {source}, {location}\n{r['text']}")
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