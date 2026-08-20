import { useState, useEffect } from "react";
import Sidebar from "./components/Sidebar";
import ChatView from "./components/ChatView";
import SearchView from "./components/SearchView";
import JournalView from "./components/JournalView";
import { checkHealth } from "./lib/api";

export default function App() {
  const [view, setView] = useState("chat");
  const [backendOnline, setBackendOnline] = useState(null);
  const [theme, setTheme] = useState(() => localStorage.getItem("rag-theme") || "light");

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("rag-theme", theme);
  }, [theme]);

  useEffect(() => {
    checkHealth().then(setBackendOnline);
    const interval = setInterval(() => checkHealth().then(setBackendOnline), 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex min-h-screen">
      <Sidebar
        active={view}
        onChange={setView}
        backendOnline={backendOnline}
        theme={theme}
        onToggleTheme={() => setTheme((t) => (t === "light" ? "dark" : "light"))}
      />
      <main className="h-screen flex-1 overflow-y-auto bg-[var(--color-canvas)]">
        {backendOnline === false && (
          <div className="border-b border-[var(--color-status-warn)]/40 bg-[var(--color-status-warn-bg)] px-8 py-2.5 text-center text-xs font-medium text-[var(--color-body)]">
            Backend injoignable — vérifie que <code className="font-mono">uvicorn</code> tourne sur le port 8000.
          </div>
        )}
        {view === "chat" && <ChatView />}
        {view === "search" && <SearchView />}
        {view === "journal" && <JournalView />}
      </main>
    </div>
  );
}