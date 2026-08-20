const API_URL = "http://127.0.0.1:8000";

async function handle(res) {
    if (!res.ok) {
        const text = await res.text().catch(() => "");
        throw new Error(`Erreur ${res.status} : ${text || res.statusText}`);
    }
    return res.json();
}

export async function askQuestion(question, history = [], k = 5) {
    const res = await fetch(`${API_URL}/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, history, k }),
    });
    return handle(res);
}

export async function searchDocuments(q, { k = 10, statut, clause } = {}) {
    const params = new URLSearchParams({ q, k: String(k) });
    if (statut) params.set("statut", statut);
    if (clause) params.set("clause", clause);
    const res = await fetch(`${API_URL}/search?${params.toString()}`);
    return handle(res);
}

export function documentUrl(path) {
    return `${API_URL}/documents/${encodeURIComponent(path)}`;
}

export async function checkHealth() {
    try {
        const res = await fetch(`${API_URL}/health`, { signal: AbortSignal.timeout(3000) });
        return res.ok;
    } catch {
        return false;
    }
}