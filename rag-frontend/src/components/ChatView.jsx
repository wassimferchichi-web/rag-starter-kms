import { useState, useRef, useEffect } from "react";
import { Send, Trash2, Sparkles, Loader2, ShieldCheck, Clock, Lightbulb } from "lucide-react";
import { askQuestion } from "../lib/api";
import SourceChip from "./SourceChip";

const AUDIT_PREP_QUESTIONS = [
    "Quelle est la politique qualité actuellement en vigueur ?",
    "Quelles sont les fiches de processus disponibles ?",
    "Quel est le contenu du dernier rapport de revue de direction ?",
    "Quelles sont les procédures liées au traitement des non-conformités ?",
    "Quelle est la fréquence des audits internes et qui les réalise ?",
];

const API_URL = "http://127.0.0.1:8000";

function RecentActivity({ refreshKey }) {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`${API_URL}/journal`)
            .then((r) => r.json())
            .then((data) => setEntries((data.entries || []).slice(0, 5)))
            .catch(() => setEntries([]))
            .finally(() => setLoading(false));
    }, [refreshKey]);

    return (
        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-card">
            <div className="mb-4 flex items-center gap-2 text-[14px] font-semibold text-[var(--color-body)]">
                <Clock size={16} className="text-[var(--color-coral-500)]" />
                Activité récente
            </div>
            {loading && <div className="skeleton h-16 rounded-lg" />}
            {!loading && entries.length === 0 && (
                <p className="text-[13px] text-[var(--color-muted)]">Aucune question posée pour l'instant.</p>
            )}
            <div className="space-y-2.5">
                {entries.map((e) => (
                    <div key={e.id} className="rounded-lg bg-[var(--color-canvas)] px-3 py-2.5">
                        <p className="text-[13px] font-medium leading-snug text-[var(--color-body)]">{e.question}</p>
                        <p className="mt-1 font-mono text-[11px] text-[var(--color-muted)]">{e.timestamp}</p>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default function ChatView() {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [refreshKey, setRefreshKey] = useState(0);
    const bottomRef = useRef(null);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, loading]);

    async function send(question) {
        if (!question.trim() || loading) return;
        setError(null);
        const userMsg = { role: "user", content: question };
        const nextMessages = [...messages, userMsg];
        setMessages(nextMessages);
        setInput("");
        setLoading(true);

        const history = nextMessages
            .slice(0, -1)
            .map((m) => ({ role: m.role, content: m.content }))
            .slice(-6);

        try {
            const data = await askQuestion(question, history, 5);
            setMessages((prev) => [...prev, { role: "assistant", content: data.answer, sources: data.sources || [] }]);
            setRefreshKey((k) => k + 1);
        } catch {
            setError("Impossible de contacter le backend. Vérifie que uvicorn tourne sur le port 8000.");
            setMessages((prev) => prev.slice(0, -1));
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="flex h-screen gap-6 px-8 py-8">
            {/* Colonne principale — chat */}
            <div className="flex flex-1 flex-col">
                <header className="mb-5 shrink-0">
                    <h1 className="font-serif text-[28px] font-semibold tracking-tight text-[var(--color-body)]">
                        Assistant qualité
                    </h1>
                    <p className="mt-1.5 text-[15px] text-[var(--color-muted)]">
                        Posez une question, puis continuez la conversation naturellement.
                    </p>
                </header>

                <div className="flex flex-1 flex-col overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] shadow-card">
                    <div className="flex-1 space-y-5 overflow-y-auto p-6">
                        {messages.length === 0 && (
                            <div className="rise-in">
                                <div className="mb-4 flex items-center gap-2.5 text-[15px] font-semibold text-[var(--color-body)]">
                                    <Sparkles size={17} className="text-[var(--color-coral-500)]" />
                                    Préparation d'audit — questions suggérées
                                </div>
                                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                                    {AUDIT_PREP_QUESTIONS.map((q) => (
                                        <button
                                            key={q}
                                            onClick={() => send(q)}
                                            className="rounded-xl border border-[var(--color-line)] bg-[var(--color-canvas)] px-4 py-3.5 text-left text-[14px] leading-snug text-[var(--color-body)] transition-all hover:-translate-y-0.5 hover:border-[var(--color-coral-500)] hover:bg-[var(--color-coral-100)]/40 hover:shadow-card"
                                        >
                                            {q}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {messages.map((m, i) =>
                            m.role === "user" ? (
                                <div key={i} className="flex justify-end rise-in">
                                    <div className="max-w-[80%] rounded-2xl rounded-br-md bg-[var(--color-coral-500)] px-5 py-3.5 text-[15.5px] leading-relaxed text-white">
                                        {m.content}
                                    </div>
                                </div>
                            ) : (
                                <div key={i} className="rise-in">
                                    <div className="overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] shadow-card">
                                        <div className="flex items-center gap-2 border-b border-[var(--color-line)] bg-[var(--color-status-ok-bg)] px-5 py-2.5">
                                            <ShieldCheck size={15} className="text-[var(--color-status-ok)]" />
                                            <span className="text-[12px] font-semibold uppercase tracking-wide text-[var(--color-status-ok)]">
                                                Réponse vérifiée
                                            </span>
                                            <span className="ml-auto text-[12px] text-[var(--color-muted)]">
                                                {m.sources?.length || 0} source{m.sources?.length > 1 ? "s" : ""}
                                            </span>
                                        </div>
                                        <div className="px-5 py-4 text-[15.5px] leading-relaxed text-[var(--color-body)]">
                                            {m.content}
                                        </div>
                                        {m.sources?.length > 0 && (
                                            <div className="space-y-2 border-t border-[var(--color-line)] bg-[var(--color-canvas)] p-4">
                                                {m.sources.map((s, j) => (
                                                    <SourceChip key={j} source={s} />
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )
                        )}

                        {loading && (
                            <div className="flex w-fit items-center gap-2.5 rounded-2xl rounded-bl-md border border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-3.5 text-[14.5px] text-[var(--color-muted)] shadow-card">
                                <Loader2 size={16} className="animate-spin text-[var(--color-coral-500)]" />
                                Recherche en cours…
                            </div>
                        )}

                        {error && (
                            <div className="rounded-xl border border-[var(--color-status-warn)]/40 bg-[var(--color-status-warn-bg)] px-5 py-3 text-[14.5px] text-[var(--color-body)]">
                                {error}
                            </div>
                        )}
                        <div ref={bottomRef} />
                    </div>

                    <div className="shrink-0 border-t border-[var(--color-line)] bg-[var(--color-canvas)] p-4">
                        {messages.length > 0 && (
                            <button
                                onClick={() => setMessages([])}
                                className="mb-3 flex items-center gap-1.5 text-[13px] font-medium text-[var(--color-muted)] hover:text-[var(--color-body)]"
                            >
                                <Trash2 size={14} /> Effacer la conversation
                            </button>
                        )}
                        <form
                            onSubmit={(e) => {
                                e.preventDefault();
                                send(input);
                            }}
                            className="flex items-center gap-2 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface)] p-2 shadow-float transition-shadow focus-within:border-[var(--color-coral-500)]"
                        >
                            <input
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="Posez votre question…"
                                className="flex-1 bg-transparent px-3 py-2.5 text-[15px] outline-none placeholder:text-[var(--color-muted)]"
                            />
                            <button
                                type="submit"
                                disabled={loading || !input.trim()}
                                className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[var(--color-coral-500)] text-white shadow-[0_2px_8px_rgba(242,100,59,0.4)] transition-all hover:bg-[var(--color-coral-600)] disabled:opacity-30 disabled:shadow-none"
                            >
                                <Send size={16} />
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            {/* Colonne latérale droite — remplit l'espace avec du contenu utile */}
            <div className="hidden w-80 shrink-0 flex-col gap-5 overflow-y-auto pt-[68px] lg:flex">
                <RecentActivity refreshKey={refreshKey} />

                <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5 shadow-card">
                    <div className="mb-3 flex items-center gap-2 text-[14px] font-semibold text-[var(--color-body)]">
                        <Lightbulb size={16} className="text-[var(--color-coral-500)]" />
                        Bon à savoir
                    </div>
                    <ul className="space-y-2.5 text-[13px] leading-snug text-[var(--color-muted)]">
                        <li>Chaque réponse cite ses sources — cliquez "Ouvrir" pour vérifier le document d'origine.</li>
                        <li>Un badge orange signale qu'une source est obsolète.</li>
                        <li>La conversation garde le contexte des échanges précédents.</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}