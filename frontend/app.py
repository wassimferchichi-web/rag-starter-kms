import streamlit as st
import requests
import threading
import queue
import time
import html
import csv
import json
from pathlib import Path
from urllib.parse import quote

API_URL = "http://127.0.0.1:8000"
QA_LOG_PATH = Path("data/logs/qa_log.csv")

def read_qa_log():
    if not QA_LOG_PATH.exists():
        return []
    with open(QA_LOG_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def delete_qa_log_row(row_index):
    """Supprime une ligne par sa position d'origine dans le fichier (avant tri
    d'affichage) et réécrit le CSV en entier — le journal reste petit, pas
    besoin d'une écriture incrémentale ici."""
    rows = read_qa_log()
    if 0 <= row_index < len(rows):
        del rows[row_index]
    fieldnames = list(rows[0].keys()) if rows else ["timestamp", "question", "n_sources", "sources", "answer_preview"]
    with open(QA_LOG_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

st.set_page_config(page_title="RAG Starter KMS", page_icon="📄", layout="wide")
st.title("RAG Starter KMS")
st.caption("Système de questions-réponses intelligent — SFM Technologies")

st.markdown("""
<style>
.chat-row { display: flex; margin: 14px 0; }
.chat-row.user { justify-content: flex-start; }
.chat-row.assistant { justify-content: flex-end; }
.chat-bubble { max-width: 70%; padding: 12px 18px; border-radius: 18px; line-height: 1.5; font-size: 15px; }
.chat-bubble.user { background-color: #f0f2f6; color: #262730; border-bottom-left-radius: 4px; }
.chat-bubble.assistant { background-color: #fee2e2; color: #262730; border-bottom-right-radius: 4px; }
</style>
""", unsafe_allow_html=True)

def render_bubble(role, content):
    safe_content = html.escape(content).replace("\n", "<br>")
    st.markdown(f'<div class="chat-row {role}"><div class="chat-bubble {role}">{safe_content}</div></div>', unsafe_allow_html=True)

def render_sources(sources, key_prefix):
    if not sources:
        return
    spacer, content_col = st.columns([1, 3])
    with content_col:
        st.markdown("**Sources :**")
        for idx, source in enumerate(sources):
            label = source_label(source)
            c1, c2 = st.columns([5, 1])
            with c1:
                if source.get("status") == "obsolete":
                    st.warning(f"⚠️ Document obsolète — {label}")
                else:
                    st.info(label)
            with c2:
                if "path" in source:
                    doc_url = f"{API_URL}/documents/{quote(source['path'])}"
                    st.link_button("Ouvrir", doc_url, key=f"{key_prefix}_{idx}")

def source_label(meta):
    if "sheet" in meta and "row" in meta:
        return f"📄 {meta['source']} — Feuille {meta['sheet']}, ligne {meta['row']}"
    if "table" in meta and "row" in meta:
        return f"📄 {meta['source']} — Tableau {meta['table']}, ligne {meta['row']}"
    return f"📄 {meta['source']} — Page {meta['page']}"

def run_in_thread(target, result_queue):
    t = threading.Thread(target=target, args=(result_queue,), daemon=True)
    t.start()
    return t

def init_state(prefix):
    for key, default in [(f"{prefix}_running", False), (f"{prefix}_cancelled", False), (f"{prefix}_queue", None), (f"{prefix}_history", [])]:
        if key not in st.session_state:
            st.session_state[key] = default

# ─────────────────────────────────────────────────────────
# Gain rapide #3 — Mode "Préparation d'audit" (parcours 9.2)
# Questions suggérées reprenant le parcours documenté par
# l'équipe qualité : filtrer les NC/actions ouvertes,
# vérifier la politique qualité et les fiches processus.
# ─────────────────────────────────────────────────────────
AUDIT_PREP_QUESTIONS = [
    "Quelle est la politique qualité actuellement en vigueur ?",
    "Quelles sont les fiches de processus disponibles ?",
    "Quel est le contenu du dernier rapport de revue de direction ?",
    "Quelles sont les procédures liées au traitement des non-conformités ?",
    "Quelle est la fréquence des audits internes et qui les réalise ?",
]

def process_question(user_input):
    """Traite une question, qu'elle vienne du chat libre ou d'une suggestion
    du mode Préparation d'audit — même logique dans les deux cas."""
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    render_bubble("user", user_input)

    history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages[:-1]][-6:]

    with st.spinner("Recherche en cours..."):
        try:
            r = requests.post(f"{API_URL}/query", json={"question": user_input, "k": 5, "history": history}, timeout=120)
            if r.status_code == 200:
                data = r.json()
                answer, sources = data["answer"], data["sources"]
            else:
                answer, sources = "Erreur lors de la requête.", []
        except Exception as e:
            answer, sources = f"Erreur de connexion : {e}", []

    render_bubble("assistant", answer)
    render_sources(sources, key_prefix=f"open_new_{len(st.session_state.chat_messages)}")

    st.session_state.chat_messages.append({"role": "assistant", "content": answer, "sources": sources})

tab1, tab2, tab3 = st.tabs(["💬 Q&R", "🔍 Recherche documentaire", "📋 Journal Q/R"])

with tab1:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    st.subheader("Assistant SFM")
    st.caption("Posez une question, puis continuez la conversation naturellement — l'assistant garde le contexte des échanges précédents.")

    with st.expander("🎯 Mode Préparation d'audit — questions suggérées", expanded=len(st.session_state.chat_messages) == 0):
        st.caption("Reprend le parcours de préparation d'audit : cliquez pour poser directement la question.")
        cols = st.columns(2)
        for i, q in enumerate(AUDIT_PREP_QUESTIONS):
            with cols[i % 2]:
                if st.button(q, key=f"audit_q_{i}", use_container_width=True):
                    st.session_state.pending_question = q
                    st.rerun()

    if st.button("Effacer la conversation"):
        st.session_state.chat_messages = []
        st.rerun()

    for msg_idx, msg in enumerate(st.session_state.chat_messages):
        render_bubble(msg["role"], msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            render_sources(msg["sources"], key_prefix=f"open_{msg_idx}")

    user_input = st.chat_input("Posez votre question...")

    # Une question suggérée en attente a priorité sur le chat libre du même run
    if st.session_state.pending_question:
        question_to_process = st.session_state.pending_question
        st.session_state.pending_question = None
        process_question(question_to_process)
    elif user_input:
        process_question(user_input)

with tab2:
    init_state("search")
    st.subheader("Recherche documentaire")
    st.caption("Recherche sémantique directe dans les documents, sans génération par IA — utile pour vérifier vite le contenu source.")

    with st.form(key="search_form"):
        search_query = st.text_input("Rechercher", placeholder="Ex: audit interne, non-conformité, habilitations...")
        col_a, col_b = st.columns(2)
        with col_a:
            # Gain rapide #1 — Filtrage par statut du document (EF-DOC-02)
            statut_choice = st.selectbox(
                "Statut du document",
                options=["Tous", "En vigueur", "Obsolète", "En révision"],
                index=0,
            )
        with col_b:
            # Gain rapide #4 — Filtrage par clause ISO (EF-GEN-04)
            clause_choice = st.text_input(
                "Clause ISO (optionnel)",
                placeholder="Ex: 8.4, 9.2, 6.2...",
                help="Détection heuristique — approximative, pas un champ structuré.",
            )
        search_clicked = st.form_submit_button("Rechercher", type="primary", disabled=st.session_state.search_running)

    STATUS_MAP = {"Tous": None, "En vigueur": "en_vigueur", "Obsolète": "obsolete", "En révision": "en_revision"}

    col_cancel2, col_clear2 = st.columns([1, 1])
    with col_cancel2:
        cancel_clicked2 = st.button("Annuler ", disabled=not st.session_state.search_running)
    with col_clear2:
        clear_clicked2 = st.button("Effacer l'historique ", disabled=st.session_state.search_running)

    if search_clicked and search_query and not st.session_state.search_running:
        q2 = queue.Queue()
        statut_param = STATUS_MAP[statut_choice]
        clause_param = clause_choice.strip() or None

        def task2(result_queue, search_query=search_query, statut_param=statut_param, clause_param=clause_param):
            try:
                params = {"q": search_query, "k": 10}
                if statut_param:
                    params["statut"] = statut_param
                if clause_param:
                    params["clause"] = clause_param
                r = requests.get(f"{API_URL}/search", params=params, timeout=120)
                result_queue.put(("ok", r))
            except Exception as e:
                result_queue.put(("error", e))
        run_in_thread(task2, q2)
        st.session_state.search_queue = q2
        st.session_state.search_running = True
        st.session_state.search_cancelled = False
        st.rerun()

    if cancel_clicked2:
        st.session_state.search_cancelled = True
        st.session_state.search_running = False
        st.session_state.search_history = []
        st.rerun()

    if clear_clicked2:
        st.session_state.search_history = []
        st.rerun()

    if st.session_state.search_running:
        st.info("Recherche en cours...")
        try:
            status, payload = st.session_state.search_queue.get_nowait()
            st.session_state.search_running = False
            if not st.session_state.search_cancelled:
                if status == "ok" and payload.status_code == 200:
                    results = payload.json()["results"]
                    st.session_state.search_history.insert(0, {"query": search_query, "results": results})
                else:
                    st.session_state.search_history.insert(0, {"query": search_query, "results": []})
            st.rerun()
        except queue.Empty:
            time.sleep(0.4)
            st.rerun()

    for entry_idx, entry in enumerate(st.session_state.search_history):
        st.markdown(f"**Recherche : {entry['query']}**")
        if not entry["results"]:
            st.info("Aucun résultat trouvé.")
        for res_idx, r in enumerate(entry["results"]):
            meta = r["metadata"]
            label = source_label(meta)
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    if meta.get("status") == "obsolete":
                        st.markdown(f"**⚠️ {label} — Document obsolète**")
                    else:
                        st.markdown(f"**{label}**")
                    if meta.get("iso_clause"):
                        st.caption(f"§ Clause ISO {meta['iso_clause']}")
                    st.write(r["text"])
                with col2:
                    if "path" in meta:
                        doc_url = f"{API_URL}/documents/{quote(meta['path'])}"
                        st.link_button("Ouvrir", doc_url, key=f"search_open_{entry_idx}_{res_idx}")

with tab3:
    st.subheader("Journal des questions/réponses")
    st.caption("Traçabilité horodatée de toutes les questions posées via l'onglet Q&R — EF-GEN-02 / ENF-SEC-05.")

    col_refresh, col_download = st.columns([1, 1])
    with col_refresh:
        if st.button("🔄 Actualiser"):
            st.rerun()
    with col_download:
        if QA_LOG_PATH.exists():
            with open(QA_LOG_PATH, "rb") as f:
                st.download_button(
                    "⬇️ Télécharger le journal complet (.csv)",
                    data=f.read(),
                    file_name="qa_log.csv",
                    mime="text/csv",
                )

    rows = read_qa_log()

    if not rows:
        st.info("Aucune question n'a encore été journalisée. Posez une question dans l'onglet Q&R pour voir apparaître une entrée ici.")
    else:
        st.metric("Questions journalisées", len(rows))

        # Tri par horodatage décroissant pour l'affichage, tout en gardant
        # l'index d'origine dans le fichier pour cibler la bonne ligne à supprimer.
        rows_sorted = sorted(enumerate(rows), key=lambda item: item[1].get("timestamp", ""), reverse=True)

        for original_idx, row in rows_sorted:
            with st.container(border=True):
                col_content, col_delete = st.columns([10, 1])
                with col_content:
                    st.markdown(f"**{row.get('question', '')}**")
                    st.caption(f"🕒 {row.get('timestamp', '')}  ·  {row.get('n_sources', '0')} source(s)")
                    with st.expander("Aperçu de la réponse"):
                        st.write(row.get("answer_preview", ""))

                    raw_sources = row.get("sources", "")
                    try:
                        parsed_sources = json.loads(raw_sources) if raw_sources else []
                    except (json.JSONDecodeError, TypeError):
                        parsed_sources = None

                    if parsed_sources:
                        st.markdown("**Sources :**")
                        for s_idx, s in enumerate(parsed_sources):
                            sc1, sc2 = st.columns([6, 1])
                            with sc1:
                                label = source_label(s)
                                if s.get("status") == "obsolete":
                                    st.warning(f"⚠️ {label}")
                                else:
                                    st.caption(label)
                            with sc2:
                                if s.get("path"):
                                    doc_url = f"{API_URL}/documents/{quote(s['path'])}"
                                    st.link_button("Ouvrir", doc_url, key=f"journal_open_{original_idx}_{s_idx}")
                    elif parsed_sources is None and raw_sources:
                        # Entrée journalisée avant l'ajout de l'accès direct aux sources —
                        # ancien format texte, pas de bouton "Ouvrir" possible dessus.
                        st.caption(f"Sources (ancien format) : {raw_sources}")
                with col_delete:
                    if st.button("🗑️", key=f"del_qa_{original_idx}", help="Supprimer cette entrée du journal"):
                        delete_qa_log_row(original_idx)
                        st.rerun()