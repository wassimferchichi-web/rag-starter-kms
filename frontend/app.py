import streamlit as st
import requests
import threading
import queue
import time
from urllib.parse import quote

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RAG Starter KMS", page_icon="🤖", layout="wide")
st.title("🤖 RAG Starter KMS")
st.caption("Système de questions-réponses intelligent — SFM Technologies")

def source_label(meta):
    if "sheet" in meta and "row" in meta:
        return f"📄 {meta['source']} — Feuille {meta['sheet']}, ligne {meta['row']}"
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
    init_state("qr")
    st.subheader("Posez votre question")
    question = st.text_input("Votre question", placeholder="Ex: Quel est le processus qualité ?")
    k = 8

    col_send, col_cancel, col_clear = st.columns([1, 1, 1])
    with col_send:
        send_clicked = st.button("Envoyer", type="primary", disabled=st.session_state.qr_running)
    with col_cancel:
        cancel_clicked = st.button("Annuler", disabled=not st.session_state.qr_running)
    with col_clear:
        clear_clicked = st.button("Effacer l'historique", disabled=st.session_state.qr_running)

    if send_clicked and question and not st.session_state.qr_running:
        q = queue.Queue()
        def task(result_queue, question=question):
            try:
                r = requests.post(f"{API_URL}/query", json={"question": question, "k": k}, timeout=120)
                result_queue.put(("ok", r))
            except Exception as e:
                result_queue.put(("error", e))
        run_in_thread(task, q)
        st.session_state.qr_queue = q
        st.session_state.qr_running = True
        st.session_state.qr_cancelled = False
        st.rerun()

    if cancel_clicked:
        st.session_state.qr_cancelled = True
        st.session_state.qr_running = False
        st.session_state.qr_history = []
        st.rerun()

    if clear_clicked:
        st.session_state.qr_history = []
        st.rerun()

    if st.session_state.qr_running:
        st.info("Recherche en cours...")
        try:
            status, payload = st.session_state.qr_queue.get_nowait()
            st.session_state.qr_running = False
            if not st.session_state.qr_cancelled:
                if status == "ok" and payload.status_code == 200:
                    data = payload.json()
                    st.session_state.qr_history.insert(0, {"question": question, "answer": data["answer"], "sources": data["sources"]})
                else:
                    st.session_state.qr_history.insert(0, {"question": question, "answer": "Erreur lors de la requête.", "sources": []})
            st.rerun()
        except queue.Empty:
            time.sleep(0.4)
            st.rerun()

    for item in st.session_state.qr_history:
        with st.container(border=True):
            st.markdown(f"**Q : {item['question']}**")
            st.write(item["answer"])
            if item["sources"]:
                st.markdown("Sources :")
                for source in item["sources"]:
                    label = source_label(source)
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.info(label)
                    with col2:
                        if "path" in source:
                            doc_url = f"{API_URL}/documents/{quote(source['path'])}"
                            st.link_button("Ouvrir", doc_url)

with tab2:
    init_state("search")
    st.subheader("Recherche documentaire")
    st.caption("Recherche sémantique directe dans les documents, sans génération par IA — utile pour vérifier vite le contenu source.")
    search_query = st.text_input("Rechercher", placeholder="Ex: audit interne, non-conformité, habilitations...")

    col_send2, col_cancel2, col_clear2 = st.columns([1, 1, 1])
    with col_send2:
        search_clicked = st.button("Rechercher", type="primary", disabled=st.session_state.search_running)
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

    for entry in st.session_state.search_history:
        st.markdown(f"**Recherche : {entry['query']}**")
        if not entry["results"]:
            st.info("Aucun résultat trouvé.")
        for r in entry["results"]:
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
                        st.link_button("Ouvrir", doc_url)