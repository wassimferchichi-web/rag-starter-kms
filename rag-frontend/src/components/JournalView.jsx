import { useState, useEffect, useCallback } from "react";
import { RotateCw, Download, Trash2, ChevronDown, Inbox } from "lucide-react";
import SourceChip from "./SourceChip";

const API_URL = "http://127.0.0.1:8000";

export default function JournalView() {
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expanded, setExpanded] = useState(null);
    const [error, setError] = useState(null);

    const load = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetch(`${API_URL}/journal`);
            if (!res.ok) throw new Error();
            const data = await res.json();
            setEntries(data.entries || []);
        } catch {
            setError("Impossible de contacter le backend. Vérifie que uvicorn tourne sur le port 8000.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => { load(); }, [load]);

    async function handleDelete(id) {
        setEntries((prev) => prev.filter((e) => e.id !== id));
        try {
            const res = await fetch(`${API_URL}/journal/${id}`, { method: "DELETE" });
            if (!res.ok) throw new Error();
        } catch {
            load();
        }
    }

    return (
        <div className="mx-auto max-w-[1100px] px-8 py-10">
            <header className="mb-7 flex items-start justify-between gap-4">
                <div>
                    <h1 className="font-serif text-[28px] font-semibold tracking-tight text-[var(--color-body)]">
                        Journal des questions
                    </h1>
                    <p className="mt-1.5 text-[15px] text-[var(--color-muted)]">
                        Traçabilité horodatée de toutes les questions posées via l'assistant.
                    </p>
                </div>
                <div className="flex shrink-0 gap-2">
                    <button
                        onClick={load}
                        className="flex items-center gap-1.5 rounded-xl border border-[var(--color-line)] bg-[var(--color-surface)] px-4 py-2.5 text-[13.5px] font-medium text-[var(--color-body)] transition-colors hover:border-[var(--color-coral-500)]"
                    >
                        <RotateCw size={14} /> Actualiser
                    </button>

                    <a
                        href={`${API_URL}/journal/download`}
                        className="flex items-center gap-1.5 rounded-xl bg-[var(--color-coral-500)] px-4 py-2.5 text-[13.5px] font-medium text-white transition-colors hover:bg-[var(--color-coral-600)]"
                    >
                        <Download size={14} /> Télécharger le CSV
                    </a>
                </div>
            </header>

            {error && (
                <div className="mb-5 rounded-xl border border-[var(--color-status-warn)]/40 bg-[var(--color-status-warn-bg)] px-5 py-3 text-[15px] text-[var(--color-body)]">
                    {error}
                </div>
            )}

            {!loading && !error && entries.length === 0 && (
                <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-[var(--color-line)] bg-[var(--color-surface)] py-16 text-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--color-canvas)]">
                        <Inbox size={20} className="text-[var(--color-muted)]" />
                    </div>
                    <p className="max-w-xs text-[15px] text-[var(--color-muted)]">
                        Aucune question journalisée pour l'instant. Pose une question dans l'onglet Assistant.
                    </p>
                </div>
            )}

            {entries.length > 0 && (
                <div className="mb-4 text-[13.5px] font-medium text-[var(--color-muted)]">
                    {entries.length} question{entries.length > 1 ? "s" : ""} journalisée{entries.length > 1 ? "s" : ""}
                </div>
            )}

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                {entries.map((entry) => {
                    const isOpen = expanded === entry.id;
                    return (
                        <div
                            key={entry.id}
                            className={`overflow-hidden rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] shadow-card transition-shadow hover:shadow-card-hover rise-in ${isOpen ? "lg:col-span-2" : ""
                                }`}
                        >
                            <div className="flex items-start justify-between gap-3 p-5">
                                <div className="min-w-0 flex-1">
                                    <div className="text-[16px] font-semibold text-[var(--color-body)]">{entry.question}</div>
                                    <div className="mt-2 font-mono text-[12.5px] text-[var(--color-muted)]">
                                        {entry.timestamp} · {entry.n_sources} source{Number(entry.n_sources) > 1 ? "s" : ""}
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDelete(entry.id)}
                                    title="Supprimer cette entrée"
                                    className="shrink-0 rounded-lg p-2.5 text-[var(--color-muted)] transition-colors hover:bg-[var(--color-status-warn-bg)] hover:text-[var(--color-status-warn)]"
                                >
                                    <Trash2 size={17} />
                                </button>
                            </div>

                            <button
                                onClick={() => setExpanded(isOpen ? null : entry.id)}
                                className="flex w-full items-center gap-1.5 border-t border-[var(--color-line)] px-5 py-3 text-[13.5px] font-medium text-[var(--color-body)] transition-colors hover:bg-[var(--color-canvas)] hover:text-[var(--color-coral-600)]"
                            >
                                <ChevronDown size={14} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
                                {isOpen ? "Masquer l'aperçu" : "Aperçu de la réponse"}
                            </button>

                            {isOpen && (
                                <div className="space-y-3 border-t border-[var(--color-line)] bg-[var(--color-canvas)] p-5 rise-in">
                                    <p className="text-[15px] leading-relaxed text-[var(--color-body)]">{entry.answer_preview}</p>
                                    {entry.sources?.length > 0 && (
                                        <div className="space-y-2">
                                            {entry.sources.map((s, j) => (
                                                <SourceChip key={j} source={s} />
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    );
                })}
            </div>
        </div>
    );
}