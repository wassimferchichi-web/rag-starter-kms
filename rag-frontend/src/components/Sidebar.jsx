import { MessageSquare, Search, ScrollText, ShieldCheck, Sun, Moon } from "lucide-react";

const NAV = [
    { id: "chat", label: "Assistant", icon: MessageSquare },
    { id: "search", label: "Recherche", icon: Search },
    { id: "journal", label: "Journal", icon: ScrollText },
];

export default function Sidebar({ active, onChange, backendOnline, theme, onToggleTheme }) {
    return (
        <aside className="flex h-screen w-72 shrink-0 flex-col bg-[var(--color-sidebar)] px-4 py-6">
            <div className="mb-1 flex items-center gap-3 px-2">
                <img src="/logo.png" alt="SFM Technologies" className="h-10 w-auto rounded-md bg-white p-1" />
                <div>
                    <div className="font-serif text-[17px] font-semibold text-white leading-tight">RAG Starter KMS</div>
                    <div className="text-[13px] text-[var(--color-sidebar-muted)] leading-tight">SFM Technologies</div>
                </div>
            </div>

            <div className="my-5 h-px bg-[var(--color-sidebar-line)]" />

            <nav className="flex flex-col gap-1">
                <div className="mb-1 px-3 text-[11px] font-semibold uppercase tracking-widest text-[var(--color-sidebar-muted)]">
                    Navigation
                </div>
                {NAV.map(({ id, label, icon: Icon }) => {
                    const isActive = active === id;
                    return (
                        <button
                            key={id}
                            onClick={() => onChange(id)}
                            className={`relative flex items-center gap-3 rounded-lg px-3 py-3 text-[15px] font-medium transition-all ${isActive
                                    ? "bg-white/10 text-white"
                                    : "text-[var(--color-sidebar-muted)] hover:bg-white/5 hover:text-white"
                                }`}
                        >
                            {isActive && (
                                <span className="absolute left-0 top-1/2 h-4 w-[3px] -translate-y-1/2 rounded-r-full bg-[var(--color-coral-500)]" />
                            )}
                            <Icon size={19} strokeWidth={isActive ? 2.4 : 2} />
                            {label}
                        </button>
                    );
                })}
            </nav>

            <div className="mt-auto space-y-3">
                <button
                    onClick={onToggleTheme}
                    className="flex w-full items-center gap-3 rounded-lg border border-[var(--color-sidebar-line)] px-3 py-3 text-[14px] font-medium text-[var(--color-sidebar-muted)] transition-all hover:bg-white/5 hover:text-white"
                >
                    {theme === "light" ? <Moon size={17} /> : <Sun size={17} />}
                    {theme === "light" ? "Mode sombre" : "Mode clair"}
                </button>

                <div className="flex items-start gap-2.5 rounded-lg border border-[var(--color-sidebar-line)] bg-white/[0.03] px-3 py-3">
                    <ShieldCheck size={17} className="mt-0.5 shrink-0 text-[var(--color-status-ok)]" />
                    <p className="text-[12.5px] leading-snug text-[var(--color-sidebar-muted)]">
                        Chaque réponse est sourcée et vérifiable, document, page et ligne exacts.
                    </p>
                </div>

                <div className="flex items-center gap-2 rounded-lg border border-[var(--color-sidebar-line)] px-3 py-2.5">
                    <span
                        className={`h-2.5 w-2.5 shrink-0 rounded-full ${backendOnline ? "bg-[var(--color-status-ok)]" : "bg-[var(--color-status-warn)] pulse-dot"
                            }`}
                    />
                    <span className="text-[13px] text-[var(--color-sidebar-muted)]">
                        {backendOnline === null ? "Vérification…" : backendOnline ? "Backend en ligne" : "Backend hors ligne"}
                    </span>
                </div>
            </div>
        </aside>
    );
}