from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="RAG Starter KMS", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

@app.on_event("startup")
def warm_up_models():
    from src.embedding.embedder import embed_query
    from src.retrieval.reranker import rerank
    embed_query("test")
    rerank("test", [{"text": "test", "metadata": {}}], top_k=1)
