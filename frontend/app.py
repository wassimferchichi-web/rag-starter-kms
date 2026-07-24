import streamlit as st
import requests
import threading
import queue
import time
import html
from urllib.parse import quote

API_URL = "http://127.0.0.1:8000"

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

tab1, tab2 = st.tabs(["💬 Q&R", "🔍 Recherche documentaire"])

with tab1:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    st.subheader("Assistant SFM")
    st.caption("Posez une question, puis continuez la conversation naturellement — l'assistant garde le contexte des échanges précédents.")

    if st.button("Effacer la conversation"):
        st.session_state.chat_messages = []
        st.rerun()

    for msg_idx, msg in enumerate(st.session_state.chat_messages):
        render_bubble(msg["role"], msg["content"])
        if msg["role"] == "assistant" and msg.get("sources"):
            render_sources(msg["sources"], key_prefix=f"open_{msg_idx}")

    user_input = st.chat_input("Posez votre question...")

    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        render_bubble("user", user_input)

        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.chat_messages[:-1]][-6:]

        with st.spinner("Recherche en cours..."):
            try:
                r = requests.post(f"{API_URL}/query", json={"question": user_input, "k": 8, "history": history}, timeout=120)
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

with tab2:
    init_state("search")
    st.subheader("Recherche documentaire")
    st.caption("Recherche sémantique directe dans les documents, sans génération par IA — utile pour vérifier vite le contenu source.")

    with st.form(key="search_form"):
        search_query = st.text_input("Rechercher", placeholder="Ex: audit interne, non-conformité, habilitations...")
        search_clicked = st.form_submit_button("Rechercher", type="primary", disabled=st.session_state.search_running)

    col_cancel2, col_clear2 = st.columns([1, 1])
    with col_cancel2:
        cancel_clicked2 = st.button("Annuler ", disabled=not st.session_state.search_running)
    with col_clear2:
        clear_clicked2 = st.button("Effacer l'historique ", disabled=st.session_state.search_running)

    if search_clicked and search_query and not st.session_state.search_running:
        q2 = queue.Queue()
        def task2(result_queue, search_query=search_query):
            try:
                r = requests.get(f"{API_URL}/search", params={"q": search_query, "k": 10}, timeout=120)
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
                    st.markdown(f"**{label}**")
                    st.write(r["text"])
                with col2:
                    if "path" in meta:
                        doc_url = f"{API_URL}/documents/{quote(meta['path'])}"
                        st.link_button("Ouvrir", doc_url, key=f"search_open_{entry_idx}_{res_idx}")