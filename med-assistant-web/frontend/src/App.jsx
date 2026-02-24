// frontend/src/App.jsx
import { useEffect, useState } from "react";
import Login from "./Login";
import { fetchConsultations, createConsultation } from "./api";

function Dashboard({ onLogout }) {
  const [consultations, setConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    fetchConsultations()
      .then(setConsultations)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setError("");
    try {
      const created = await createConsultation(title || "New consultation");
      setConsultations((prev) => [...prev, created]);
      setTitle("");
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#020617",
        color: "#e5e7eb",
        padding: "24px",
        fontFamily:
          'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}
    >
      <div
        style={{
          maxWidth: "680px",
          margin: "0 auto",
          backgroundColor: "#020617",
          borderRadius: "12px",
          border: "1px solid rgba(148,163,184,0.4)",
          padding: "16px 18px",
          boxShadow: "0 18px 40px rgba(15,23,42,0.8)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "10px",
          }}
        >
          <div>
            <h1
              style={{
                fontSize: "20px",
                fontWeight: 600,
                marginBottom: "4px",
              }}
            >
              Med Consult AI – Dashboard
            </h1>
            <p
              style={{
                fontSize: "13px",
                color: "#9ca3af",
              }}
            >
              View and create consultations linked to your online meetings.
            </p>
          </div>
          <button
            onClick={onLogout}
            style={{
              borderRadius: "999px",
              border: "1px solid rgba(148,163,184,0.7)",
              backgroundColor: "#020617",
              color: "#e5e7eb",
              fontSize: "11px",
              padding: "4px 10px",
              cursor: "pointer",
            }}
          >
            Log out
          </button>
        </div>

        <form
          onSubmit={handleCreate}
          style={{
            display: "flex",
            gap: "8px",
            marginBottom: "12px",
          }}
        >
          <input
            style={{
              flex: 1,
              borderRadius: "8px",
              border: "1px solid rgba(148,163,184,0.7)",
              backgroundColor: "#020617",
              color: "#e5e7eb",
              padding: "6px 8px",
              fontSize: "13px",
            }}
            placeholder="Consultation title"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
          <button
            type="submit"
            style={{
              borderRadius: "999px",
              border: "none",
              padding: "6px 12px",
              fontSize: "13px",
              fontWeight: 500,
              background: "linear-gradient(135deg, #16a34a, #22c55e)",
              color: "#052e16",
              cursor: "pointer",
            }}
          >
            New
          </button>
        </form>

        {error && (
          <div
            style={{
              marginBottom: "8px",
              fontSize: "12px",
              color: "#fbbf24",
            }}
          >
            Error: {error}
          </div>
        )}

        {loading ? (
          <div style={{ fontSize: "14px", color: "#cbd5f5" }}>Loading…</div>
        ) : consultations.length === 0 ? (
          <div style={{ fontSize: "14px", color: "#cbd5f5" }}>
            No consultations yet. Create the first one above.
          </div>
        ) : (
          <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
            {consultations.map((c) => (
              <li
                key={c.id}
                style={{
                  borderRadius: "8px",
                  border: "1px solid rgba(148,163,184,0.6)",
                  backgroundColor: "#020617",
                  padding: "8px 10px",
                  marginBottom: "6px",
                  fontSize: "13px",
                }}
              >
                <div style={{ fontWeight: 500 }}>{c.title}</div>
                <div
                  style={{
                    fontSize: "11px",
                    color: "#9ca3af",
                    marginTop: "2px",
                  }}
                >
                  ID: {c.id} · Created at:{" "}
                  {new Date(c.created_at).toLocaleString()}
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(
    !!localStorage.getItem("access_token")
  );

  const handleLogin = () => {
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    setIsLoggedIn(false);
  };

  if (!isLoggedIn) {
    return <Login onLogin={handleLogin} />;
  }

  return <Dashboard onLogout={handleLogout} />;
}

export default App;
