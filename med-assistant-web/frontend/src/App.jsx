// frontend/src/App.jsx
import { useEffect, useState } from "react";
import Login from "./Login";
import { fetchConsultations, createConsultation, logout } from "./api";

function Dashboard({ onLogout }) {
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [expandedId, setExpandedId] = useState(null);

  const loadData = () => {
    fetchConsultations()
      .then(setConsultations)
      .catch((err) => {
        if (err.message === "unauthorized") {
          onLogout();
        } else {
          setError(err.message);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();

    // Poll for updates every 3 seconds
    const intervalId = setInterval(() => {
      loadData();
    }, 3000);

    return () => clearInterval(intervalId);
  }, [onLogout]);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const created = await createConsultation(title || "New consultation");
      setConsultations((prev) => [created, ...prev]);
      setTitle("");
    } catch (err) {
      if (err.message === "unauthorized") {
        onLogout();
      } else {
        setError(err.message);
      }
    }
  };

  // Calculate stats for the welcome summary
  const totalConsultations = consultations.length;
  const totalTranscripts = consultations.reduce(
    (acc, c) => acc + (c.transcripts?.length || 0),
    0
  );
  const totalInsights = consultations.filter((c) => c.insights).length;

  const handleToggleExpand = (id) => {
    setExpandedId((prevId) => (prevId === id ? null : id));
  };

  const formatTime = (seconds) => {
    if (!isFinite(seconds)) return '0:00';
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div style={{ padding: "32px 24px", width: "100%", maxWidth: "1200px", margin: "0 auto", boxSizing: "border-box" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "40px" }} className="animate-fade-in">
        <div>
          <h1 style={{ fontSize: "36px", fontWeight: 700, margin: "0 0 8px 0" }}>
            Welcome back <span className="text-gradient">Doctor</span>
          </h1>
          <p style={{ color: "#94a3b8", margin: 0, fontSize: "16px" }}>
            Here is an overview of your recent patient consultations.
          </p>
        </div>
        <button
          onClick={onLogout}
          className="glass-panel"
          style={{
            padding: "8px 16px",
            color: "#e2e8f0",
            backgroundColor: "rgba(30, 41, 59, 0.4)",
            border: "1px solid rgba(148, 163, 184, 0.2)",
            borderRadius: "999px",
            fontSize: "14px",
            fontWeight: 500,
            cursor: "pointer",
          }}
        >
          Sign Out
        </button>
      </div>

      {/* Stats Overview */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "24px", marginBottom: "40px" }} className="animate-fade-in stagger-1">
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>Total Consultations</div>
          <div style={{ fontSize: "36px", fontWeight: 700, color: "#f8fafc" }}>{loading ? "-" : totalConsultations}</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>Transcript Moments</div>
          <div style={{ fontSize: "36px", fontWeight: 700, color: "#f8fafc" }}>{loading ? "-" : totalTranscripts}</div>
        </div>
        <div className="glass-panel" style={{ padding: "24px", display: "flex", flexDirection: "column", gap: "8px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.05em" }}>Insights Generated</div>
          <div style={{ fontSize: "36px", fontWeight: 700, color: "#f8fafc" }}>{loading ? "-" : totalInsights}</div>
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ display: "grid", gridTemplateColumns: "minmax(0, 1fr)", gap: "24px" }} className="animate-fade-in stagger-2">
        <div className="glass-panel" style={{ padding: "32px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px", flexWrap: "wrap", gap: "16px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 600, margin: 0, color: "#f8fafc" }}>Recent Consultations</h2>

            <form onSubmit={handleCreate} style={{ display: "flex", gap: "12px", width: "100%", maxWidth: "400px" }}>
              <input
                style={{
                  flex: 1,
                  padding: "10px 16px",
                  borderRadius: "8px",
                  border: "1px solid rgba(148, 163, 184, 0.2)",
                  backgroundColor: "rgba(15, 23, 42, 0.4)",
                  color: "#f8fafc",
                  fontSize: "14px",
                  outline: "none"
                }}
                placeholder="New consultation title..."
                value={title}
                onChange={(e) => setTitle(e.target.value)}
              />
              <button
                type="submit"
                style={{
                  background: "var(--primary-gradient)",
                  border: "none",
                  padding: "10px 20px",
                  borderRadius: "8px",
                  color: "white",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: "pointer",
                  boxShadow: "0 4px 12px rgba(59, 130, 246, 0.3)",
                }}
              >
                Create
              </button>
            </form>
          </div>

          {error && (
            <div style={{ padding: "12px", backgroundColor: "rgba(239, 68, 68, 0.1)", border: "1px solid rgba(239, 68, 68, 0.2)", borderRadius: "8px", color: "#ef4444", marginBottom: "24px", fontSize: "14px" }}>
              {error}
            </div>
          )}

          {loading ? (
            <div style={{ textAlign: "center", padding: "48px", color: "#64748b" }}>Loading your data...</div>
          ) : consultations.length === 0 ? (
            <div style={{ textAlign: "center", padding: "64px", border: "1px dashed rgba(148, 163, 184, 0.2)", borderRadius: "12px", color: "#64748b" }}>
              No consultations found. Start by creating a new one above.
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {consultations.map((c, index) => (
                <div key={c.id} className="animate-fade-in" style={{ animationDelay: `${(index % 5 + 3) * 0.1}s` }}>
                  <div
                    onClick={() => handleToggleExpand(c.id)}
                    style={{
                      padding: "20px",
                      backgroundColor: "rgba(30, 41, 59, 0.4)",
                      border: "1px solid rgba(148, 163, 184, 0.1)",
                      borderRadius: expandedId === c.id ? "12px 12px 0 0" : "12px",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      flexWrap: "wrap",
                      gap: "16px",
                      cursor: "pointer",
                      transition: "all 0.2s ease"
                    }}
                  >
                    <div>
                      <h3 style={{ margin: "0 0 6px 0", fontSize: "16px", fontWeight: 600, color: "#f1f5f9" }}>{c.title}</h3>
                      <div style={{ display: "flex", gap: "16px", fontSize: "13px", color: "#94a3b8" }}>
                        <span>Started: {new Date(c.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}</span>
                      </div>
                    </div>

                    <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
                      {c.transcripts?.length > 0 ? (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(59, 130, 246, 0.1)", color: "#60a5fa", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(59, 130, 246, 0.2)" }}>
                          {c.transcripts.length} Moments
                        </span>
                      ) : (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(148, 163, 184, 0.05)", color: "#64748b", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                          No Recording
                        </span>
                      )}

                      {c.insights ? (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(16, 185, 129, 0.1)", color: "#34d399", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(16, 185, 129, 0.2)" }}>
                          Insight Ready
                        </span>
                      ) : (
                        <span style={{ padding: "4px 10px", backgroundColor: "rgba(148, 163, 184, 0.05)", color: "#64748b", borderRadius: "999px", fontSize: "12px", fontWeight: 500, border: "1px solid rgba(148, 163, 184, 0.1)" }}>
                          Processing
                        </span>
                      )}

                      <span style={{ marginLeft: "8px", color: "#94a3b8", transform: expandedId === c.id ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.2s ease" }}>
                        ▼
                      </span>
                    </div>
                  </div>

                  {expandedId === c.id && (
                    <div style={{
                      padding: "20px",
                      backgroundColor: "rgba(15, 23, 42, 0.6)",
                      border: "1px solid rgba(148, 163, 184, 0.1)",
                      borderTop: "none",
                      borderRadius: "0 0 12px 12px",
                    }}>
                      <h4 style={{ margin: "0 0 16px 0", fontSize: "14px", fontWeight: 600, color: "#e2e8f0" }}>Transcripts</h4>
                      {c.transcripts && c.transcripts.length > 0 ? (
                        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                          {[...c.transcripts].sort((a, b) => a.start_time - b.start_time).map((t) => (
                            <div key={t.id} style={{ display: "flex", gap: "12px", fontSize: "14px" }}>
                              <div style={{ color: "#3b82f6", fontWeight: 500, minWidth: "80px" }}>
                                {t.speaker}
                                <div style={{ fontSize: "12px", color: "#94a3b8", fontWeight: "normal" }}>
                                  [{formatTime(t.start_time)}]
                                </div>
                              </div>
                              <div style={{ color: "#f8fafc", lineHeight: "1.5", flex: 1, backgroundColor: "rgba(255,255,255,0.02)", padding: "10px 14px", borderRadius: "8px", border: "1px solid rgba(255,255,255,0.05)" }}>
                                {t.text}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ color: "#94a3b8", fontSize: "14px", fontStyle: "italic" }}>
                          No transcripts available for this consultation.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    document.cookie.includes("logged_in=1")
  );

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (e) { }
    document.cookie = "logged_in=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}

export default App;
