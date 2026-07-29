# Comparaison des modèles LLM — RAG Starter KMS

Question de test utilisée : "Quels sont les postes clés de SFM ?"
(et éventuellement : "Qui approuve le rapport de revue de direction ?")

| Modèle | Fidélité (1-5) | Complétude (1-5) | Format SOURCES_UTILISEES OK ? | Vitesse ressentie | Français naturel ? | Notes |
|---|---|---|---|---|---|---|
| llama-3.3-70b-versatile (référence, déprécié) | 4 | 3 | Oui | Lent (8.3s sur Q1) | Oui | Admet ne pas avoir de liste exhaustive |
| openai/gpt-oss-120b | 5 | 5 | Oui | Rapide (2.5s / 1.0s) | Oui | Le plus complet, bien structuré, gagnant |
| openai/gpt-oss-20b | 4 | 3 | Oui | Très rapide (1.7s / 1.2s) | Oui | Moins de sources citées, moins complet |
| qwen/qwen3-32b | — | — | — | — | — | 404 : nom de modèle invalide ou non accessible |
| meta-llama/llama-4-scout-17b-16e-instruct | — | — | — | — | — | 404 : nom de modèle invalide ou non accessible |
| moonshotai/kimi-k2-instruct | — | — | — | — | — | 404 : nom de modèle invalide ou non accessible |
| gemma2-9b-it | — | — | — | — | — | Modèle officiellement retiré par Groq |

## Verdict final

Modèle retenu : **openai/gpt-oss-120b**
Raison : 3x plus rapide que l'ancien modèle, réponses plus complètes (trouve des catégories de postes clés que l'ancien modèle ratait), format de citation respecté, c'est aussi le remplacement officiellement recommandé par Groq suite à la dépréciation de llama-3.3-70b-versatile.

## Validation par évaluation RAGAS

Après migration vers `openai/gpt-oss-120b` et amélioration du chunking (préfixe du titre de document sur chaque ligne de tableau), un run complet et fiable (24/24 valeurs, aucune erreur de quota) a donné :

| Métrique | Score |
|---|---|
| Faithfulness | 1.00 |
| Answer Relevancy | 0.88 |
| Context Precision | 0.65 |
| Context Recall | 0.83 |

Faithfulness parfaite sur les 6 questions testées. Context recall parfait sur 5/6 questions ; le seul cas restant (référence de version du Programme d'Audit Interne) est un problème de chunking connu, pas un problème du modèle — confirmé par le fait que le context_recall était identique entre les deux modèles testés sur ce même cas avant le fix.