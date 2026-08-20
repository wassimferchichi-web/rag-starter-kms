import re
from sentence_transformers import CrossEncoder
from typing import List, Dict

_model = None

REFERENCE_PATTERN = re.compile(r"\b[A-Z]{2,6}(?:-[A-Z0-9]{2,6}){1,3}\b")

# Poids du boost lexical relatif au score (normalisé) du cross-encoder.
# A ajuster empiriquement : trop haut et ça ignore la pertinence sémantique,
# trop bas et ça ne corrige plus rien pour les codes/références exactes.
LEXICAL_WEIGHT = 0.5

# Filtrage par seuil de score dynamique — RÉACTIVÉ (2026-08), recalibré.
# Un premier réglage (ratio=0.5, minimum=2) avait sur-coupé après le retrait
# du recouvrement lexical générique ci-dessus (scores du cross-encoder seul
# beaucoup plus tranchés que prévu, coupant presque tout à 2 résultats).
# Nouveau réglage volontairement plus tolérant : ne coupe que les candidats
# vraiment très faibles, et garde un minimum de 3 (pas 2) pour ne jamais
# affamer le LLM en contexte, même dans le pire cas.
MIN_SCORE_RATIO = 0.2
MIN_RESULTS = 3


def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    return _model


def _lexical_boost(query: str, text: str) -> float:
    """Score complémentaire au cross-encoder, limité à la correspondance de
    code exact (référence, version). Un ancien composant de recouvrement de
    mots-clés génériques a été retiré : sur des documents où plusieurs lignes
    de tableau partagent le même titre en préfixe (ex. toutes les lignes de
    'Procédure de Traitement des Réclamations Clients'), ce recouvrement
    générique gonflait artificiellement TOUS les chunks du document de façon
    quasi uniforme (via les mots du titre), noyant le signal au lieu de
    distinguer les chunks vraiment pertinents des autres — constaté sur
    RAGAS (context_precision) le 2026-08."""
    text_lower = text.lower()
    boost = 0.0
    for code in REFERENCE_PATTERN.findall(query):
        if code.lower() in text_lower:
            boost += 1.0
    return boost


def rerank(query: str, candidates: List[Dict], top_k: int) -> List[Dict]:
    if not candidates:
        return []

    pairs = [(query, c["text"]) for c in candidates]
    raw_scores = list(get_reranker().predict(pairs))

    # Normalisation min-max sur le pool pour que le boost lexical soit
    # comparable en échelle au score du cross-encoder (logits bruts sinon).
    lo, hi = min(raw_scores), max(raw_scores)
    rng = (hi - lo) if hi > lo else 1.0
    normalized = [(s - lo) / rng for s in raw_scores]

    combined = [
        norm + LEXICAL_WEIGHT * _lexical_boost(query, c["text"])
        for norm, c in zip(normalized, candidates)
    ]

    scored = list(zip(candidates, combined))
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    if not top:
        return []

    best_score = top[0][1]
    cutoff = best_score * MIN_SCORE_RATIO if best_score > 0 else 0
    filtered = [c for c, s in top if s >= cutoff]

    if len(filtered) < MIN_RESULTS:
        filtered = [c for c, _ in top[:MIN_RESULTS]]

    return filtered