import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="RAG Starter KMS", page_icon="🤖", layout="wide")
st.title("🤖 RAG Starter KMS")
st.caption("Système de questions-réponses intelligent — SFM Technologies")

tab1, tab2 = st.tabs(["💬 Q&R", "📄 Ingérer un document"])

with tab1:
    st.subheader("Posez votre question")
    question = st.text_input("Votre question", placeholder="Ex: Quel est le processus qualité ?")
    k = st.slider("Nombre de sources", 1, 10, 5)
    if st.button("Envoyer", type="primary"):
        if question:
            with st.spinner("Recherche en cours..."):
                response = requests.post(f"{API_URL}/query", json={"question": question, "k": k})
                if response.status_code == 200:
                    data = response.json()
                    st.markdown("### Réponse")
                    st.write(data["answer"])
                    st.markdown("### Sources")
                    for source in data["sources"]:
                        if "sheet" in source and "row" in source:
                            st.info(f"📄 {source['source']} — Feuille {source['sheet']}, ligne {source['row']}")
                        else:
                            st.info(f"📄 {source['source']} — Page {source['page']}")
                else:
                    st.error("Erreur lors de la requête")

with tab2:
    st.subheader("Ingérer un document PDF")
    uploaded_file = st.file_uploader("Choisir un fichier PDF", type=["pdf"])
    if uploaded_file and st.button("Ingérer", type="primary"):
        with st.spinner("Ingestion en cours..."):
            response = requests.post(f"{API_URL}/ingest", files={"file": uploaded_file})
            if response.status_code == 200:
                data = response.json()
                st.success(f"✅ {data['message']} — {data['chunks']} chunks créés")
            else:
                st.error("Erreur lors de l'ingestion")