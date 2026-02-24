// frontend/src/Login.jsx
import { useState } from "react";
import { login } from "./api";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await login(email, password);
      localStorage.setItem("access_token", data.access_token);
      onLogin();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        backgroundColor: "#020617",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
        color: "#e5e7eb",
        fontFamily:
          'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "360px",
          backgroundColor: "#020617",
          borderRadius: "12px",
          border: "1px solid rgba(148,163,184,0.4)",
          padding: "18px 20px",
          boxShadow: "0 18px 40px rgba(15,23,42,0.8)",
        }}
      >
        <h1
          style={{
            fontSize: "20px",
            fontWeight: 600,
            marginBottom: "4px",
          }}
        >
          Med Consult AI
        </h1>
        <p
          style={{
            fontSize: "13px",
            color: "#9ca3af",
            marginBottom: "16px",
          }}
        >
          Log in to view your consultations, transcripts, and summaries.
        </p>

        <form onSubmit={handleSubmit}>
          <label
            style={{
              display: "block",
              fontSize: "12px",
              marginBottom: "4px",
            }}
          >
            Email
          </label>
          <input
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{
              width: "100%",
              borderRadius: "8px",
              border: "1px solid rgba(148,163,184,0.7)",
              backgroundColor: "#020617",
              color: "#e5e7eb",
              padding: "6px 8px",
              fontSize: "13px",
              marginBottom: "10px",
            }}
          />

          <label
            style={{
              display: "block",
              fontSize: "12px",
              marginBottom: "4px",
            }}
          >
            Password
          </label>
          <input
            type="password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{
              width: "100%",
              borderRadius: "8px",
              border: "1px solid rgba(148,163,184,0.7)",
              backgroundColor: "#020617",
              color: "#e5e7eb",
              padding: "6px 8px",
              fontSize: "13px",
              marginBottom: "10px",
            }}
          />

          {error && (
            <div
              style={{
                fontSize: "12px",
                color: "#fbbf24",
                marginBottom: "8px",
              }}
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              borderRadius: "999px",
              border: "none",
              padding: "8px 12px",
              fontSize: "13px",
              fontWeight: 500,
              background: "linear-gradient(135deg, #16a34a, #22c55e)",
              color: "#052e16",
              cursor: loading ? "default" : "pointer",
              opacity: loading ? 0.7 : 1,
              marginTop: "4px",
            }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p
          style={{
            fontSize: "11px",
            color: "#9ca3af",
            marginTop: "10px",
          }}
        >
          For your FYP demo, you can pre‑create a doctor user via a signup
          endpoint or a script.
        </p>
      </div>
    </div>
  );
}
