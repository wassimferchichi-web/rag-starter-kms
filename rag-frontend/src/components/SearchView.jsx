import { useState } from "react";
import { Search as SearchIcon, Loader2, FileText, AlertTriangle } from "lucide-react";
import { searchDocuments, documentUrl } from "../lib/api";

const STATUS_OPTIONS = [
    { value: "", label: "Tous" },
    { value: "en_vigueur", label: "En vigueur" },
    { value: "obsolete", label: "Obsolète" },
    { value: "en_revision", label: "En révision" },
];

function resultLabel(meta) {
    if (meta.sheet && meta.row) return `${meta.source} · Feuille ${meta.sheet}, ligne ${meta.row}`;
    if (meta.table && meta.row) return `${meta.source} · Tableau ${meta.table}, ligne ${meta.row}`;
    return `${meta.source} · Page ${meta.page ?? "?"}`;
}

function ResultSkeleton() {
    return (
        <div className="rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-5">
            <div className="skeleton mb-3 h-4 w-2/3 rounded" />
            <div className="skeleton mb-1.5 h-3 w-full rounded" />
            <div className="skeleton h-3 w-4/5 rounded" />
        </div>
    );
}

export default function SearchView() {
    const [query, setQuery] = useState("");
    const [statut, setStatut] = useState("");
    const [clause, setClause] = useState("");
    const [results, setResults] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    async function handleSearch(e) {
        e.preventDefault();
        if (!query.trim() || loading) return;
        setLoading(true);
        setError(null);
        try {
            const data = await searchDocuments(query, { k: 10, statut: statut || undefined, clause: clause || undefined });
            setResults(data.results || []);
        } catch {
            setError("Impossible de contacter le backend. Vérifie que uvicorn tourne sur le port 8000.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="mx-auto max-w-[1100px] px-8 py-10">
            <header className="mb-7">
                <h1 className="font-serif text-[28px] font-semibold tracking-tight text-[var(--color-body)]">
                    Recherche documentaire
                </h1>
                <p className="mt-1.5 text-[15px] text-[var(--color-muted)]">
                    Recherche sémantique directe, sans génération par IA — utile pour vérifier vite le contenu source.
                </p>
            </header>

            <form onSubmit={handleSearch} className="mb-7 rounded-2xl border border-[var(--color-line)] bg-[var(--color-surface)] p-6 shadow-card">
                <label className="mb-2 block text-[14px] font-semibold text-[var(--color-body)]">Rechercher</label>
                <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ex : audit interne, non-conformité, habilitations…"
                    className="mb-5 w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-canvas)] px-4 py-3 text-[15px] text-[var(--color-body)] outline-none transition-colors focus:border-[var(--color-coral-500)] focus:bg-[var(--color-surface)]"
                />

                <div className="mb-5 grid grid-cols-2 gap-4">
                    <div>
                        <label className="mb-2 block text-[14px] font-semibold text-[var(--color-body)]">Statut du document</label>
                        <select
                            value={statut}
                            onChange={(e) => setStatut(e.target.value)}
                            className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-canvas)] px-4 py-3 text-[15px] text-[var(--color-body)] outline-none focus:border-[var(--color-coral-500)] focus:bg-[var(--color-surface)]"
                        >
                            {STATUS_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                        </select>
                    </div>
                    <div>
                        <label className="mb-2 block text-[14px] font-semibold text-[var(--color-body)]">
                            Clause ISO <span className="font-normal text-[var(--color-muted)]">(optionnel)</span>
                        </label>
                        <input
                            value={clause}
                            onChange={(e) => setClause(e.target.value)}
                            placeholder="Ex : 8.4, 9.2, 6.2…"
                            className="w-full rounded-xl border border-[var(--color-line)] bg-[var(--color-canvas)] px-4 py-3 text-[15px] text-[var(--color-body)] outline-none focus:border-[var(--color-coral-500)] focus:bg-[var(--color-surface)]"
                        />
                    </div>
                </div>

                <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="flex items-center gap-2 rounded-xl bg-[var(--color-coral-500)] px-5 py-3 text-[15px] font-semibold text-white shadow-[0_4px_12px_rgba(242,100,59,0.3)] transition-all hover:bg-[var(--color-coral-600)] hover:shadow-[0_6px_16px_rgba(242,100,59,0.4)] disabled:opacity-40 disabled:shadow-none"
                >
                    {loading ? <Loader2 size={17} className="animate-spin" /> : <SearchIcon size={17} />}
                    Rechercher
                </button>
            </form>

            {error && (
                <div className="mb-5 rounded-xl border border-[var(--color-status-warn)]/40 bg-[var(--color-status-warn-bg)] px-5 py-3 text-[15px] text-[var(--color-body)]">
                    {error}
                </div>
            )}

            {loading && (
                <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
                    <ResultSkeleton /><ResultSkeleton /><ResultSkeleton /><ResultSkeleton />
                </div>
            )}

            {!loading && results !== null && (
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                    {results.length === 0 && (
                        <p className="col-span-full rounded-2xl border border-dashed border-[var(--color-line)] bg-[var(--color-surface)] px-5 py-12 text-center text-[15px] text-[var(--color-muted)]">
                            Aucun résultat trouvé.
                        </p>
                    )}
                    {results.map((r, i) => {
                        const isObsolete = r.metadata?.status === "obsolete";
                        return (
                            <div
                                key={i}
                                className={`rounded-2xl border bg-[var(--color-surface)] p-5 shadow-card transition-all hover:-translate-y-0.5 hover:shadow-card-hover rise-in ${isObsolete ? "border-[var(--color-status-warn)]/30" : "border-[var(--color-line)]"
                                    }`}
                            >
                                <div className="mb-3 flex items-start justify-between gap-3">
                                    <div className="flex items-start gap-2.5">
                                        {isObsolete ? (
                                            <AlertTriangle size={17} className="mt-0.5 shrink-0 text-[var(--color-status-warn)]" />
                                        ) : (
                                            <FileText size={17} className="mt-0.5 shrink-0 text-[var(--color-muted)]" />
                                        )}
                                        <div>
                                            <div className="font-mono text-[13.5px] font-medium tracking-tight text-[var(--color-body)]">
                                                {resultLabel(r.metadata)}
                                            </div>
                                            {r.metadata?.iso_clause && (
                                                <div className="mt-1.5 inline-block rounded-full bg-[var(--color-coral-100)] px-2.5 py-1 text-[12px] font-semibold text-[var(--color-coral-600)]">
                                                    § Clause ISO {r.metadata.iso_clause}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                    {r.metadata?.path && (
                                        <a
                                            href={documentUrl(r.metadata.path)}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="shrink-0 rounded-lg border border-[var(--color-line)] px-3.5 py-2 text-[13px] font-medium text-[var(--color-body)] transition-colors hover:border-[var(--color-coral-500)] hover:text-[var(--color-coral-600)]"
                                        >
                                            Ouvrir
                                        </a>
                                    )}
                                </div>
                                <p className="text-[14.5px] leading-relaxed text-[var(--color-body)]">{r.text}</p>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}