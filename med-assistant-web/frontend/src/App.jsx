// frontend/src/App.jsx
import { useEffect, useState } from "react";

const API_URL = "http://localhost:8000";

function App() {
  const [backendMessage, setBackendMessage] = useState("Loading...");
  const [health, setHealth] = useState(null);

  useEffect(() => {
    // Fetch welcome message from backend
    fetch(`${API_URL}/`)
      .then((res) => res.json())
      .then((data) => setBackendMessage(data.message))
      .catch(() => setBackendMessage("Unable to reach backend"));

    // Fetch health check
    fetch(`${API_URL}/health`)
      .then((res) => res.json())
      .then((data) => setHealth(data.status))
      .catch(() => setHealth("error"));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-slate-900/80 border border-slate-700/70 rounded-xl px-6 py-5 shadow-2xl">
        <h1 className="text-xl font-semibold text-slate-50 mb-2">
          Med Consult AI – Web App
        </h1>
        <p className="text-sm text-slate-300 mb-4">
          This app will become the **brains** of your AI medical assistant,
          showing transcripts, summaries, and insights from online consultations.
        </p>

        <div className="mt-3 rounded-lg border border-slate-700 bg-slate-950/60 px-4 py-3">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs tracking-wide text-slate-400 uppercase">
              Welcome
            </span>
            <span
              className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                health === "ok"
                  ? "border-emerald-500/60 bg-emerald-500/10 text-emerald-300"
                  : "border-amber-500/60 bg-amber-500/10 text-amber-200"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  health === "ok" ? "bg-emerald-400" : "bg-amber-400"
                }`}
              ></span>
              Backend {health === "ok" ? "online" : "checking"}
            </span>
          </div>
          <div className="text-sm text-slate-100">{backendMessage}</div>
        </div>

        <p className="mt-4 text-xs text-slate-400">
          Next steps: add pages for consultations, transcripts, and AI-generated
          notes, and connect this app to your Chrome extension audio pipeline.
        </p>
      </div>
    </div>
  );
}

export default App;
