import { FileText, ExternalLink, AlertTriangle } from "lucide-react";
import { documentUrl } from "../lib/api";

function sourceLabel(meta) {
  if (meta.sheet && meta.row) return `${meta.source} · Feuille ${meta.sheet}, ligne ${meta.row}`;
  if (meta.table && meta.row) return `${meta.source} · Tableau ${meta.table}, ligne ${meta.row}`;
  return `${meta.source} · Page ${meta.page ?? "?"}`;
}

export default function SourceChip({ source }) {
  const isObsolete = source.status === "obsolete";
  return (
    <div
      className={`group flex items-center gap-3 rounded-lg border-l-[3px] bg-[var(--color-canvas)] px-4 py-3 text-sm transition-all ${isObsolete
        ? "border-l-[var(--color-status-warn)] bg-[var(--color-status-warn-bg)]"
        : "border-l-[var(--color-status-ok)]/70 hover:border-l-[var(--color-status-ok)]"
        }`}
    >
      {isObsolete ? (
        <AlertTriangle size={16} className="shrink-0 text-[var(--color-status-warn)]" />
      ) : (
        <FileText size={16} className="shrink-0 text-[var(--color-muted)]" />
      )}
      <span className="min-w-0 flex-1 font-mono text-[13px] tracking-tight text-[var(--color-body)]">
        {sourceLabel(source)}
      </span>
      {isObsolete && (
        <span className="shrink-0 rounded-full bg-[var(--color-status-warn)]/20 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[var(--color-status-warn)]">
          Obsolète
        </span>
      )}
      {source.path && (
        <a
          href={documentUrl(source.path)}
          target="_blank"
          rel="noreferrer"
          className="shrink-0 flex items-center gap-1 rounded-md px-2.5 py-1.5 text-[13px] font-medium text-[var(--color-muted)] opacity-0 transition-opacity group-hover:opacity-100 hover:bg-[var(--color-surface)] hover:text-[var(--color-coral-600)]"
        >
          Ouvrir <ExternalLink size={12} />
        </a>
      )}
    </div>
  );
}