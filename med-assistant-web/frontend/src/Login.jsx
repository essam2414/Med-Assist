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
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "16px",
      }}
    >
      <div
        className="glass-panel animate-fade-in"
        style={{
          width: "100%",
          maxWidth: "400px",
          padding: "40px 32px",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
        }}
      >
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <h1
            className="text-gradient"
            style={{
              fontSize: "28px",
              fontWeight: 700,
              margin: "0 0 8px 0",
              letterSpacing: "-0.02em",
            }}
          >
            Med Consult AI
          </h1>
          <p
            style={{
              fontSize: "15px",
              color: "#94a3b8",
              margin: 0,
            }}
          >
            Welcome back. Please sign in to your account.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ width: "100%", display: "flex", flexDirection: "column", gap: "20px" }} className="animate-fade-in stagger-1">
          <div>
            <label
              style={{
                display: "block",
                fontSize: "13px",
                fontWeight: 500,
                color: "#cbd5e1",
                marginBottom: "8px",
              }}
            >
              Email Address
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="doctor@med.ai"
              style={{
                width: "100%",
                boxSizing: "border-box",
                borderRadius: "8px",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                backgroundColor: "rgba(15, 23, 42, 0.6)",
                color: "#f8fafc",
                padding: "12px 16px",
                fontSize: "14px",
                outline: "none",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => e.target.style.borderColor = "#3b82f6"}
              onBlur={(e) => e.target.style.borderColor = "rgba(148, 163, 184, 0.2)"}
            />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: "13px",
                fontWeight: 500,
                color: "#cbd5e1",
                marginBottom: "8px",
              }}
            >
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: "100%",
                boxSizing: "border-box",
                borderRadius: "8px",
                border: "1px solid rgba(148, 163, 184, 0.2)",
                backgroundColor: "rgba(15, 23, 42, 0.6)",
                color: "#f8fafc",
                padding: "12px 16px",
                fontSize: "14px",
                outline: "none",
                transition: "border-color 0.2s",
              }}
              onFocus={(e) => e.target.style.borderColor = "#3b82f6"}
              onBlur={(e) => e.target.style.borderColor = "rgba(148, 163, 184, 0.2)"}
            />
          </div>

          {error && (
            <div
              className="animate-fade-in"
              style={{
                fontSize: "13px",
                color: "#ef4444",
                backgroundColor: "rgba(239, 68, 68, 0.1)",
                border: "1px solid rgba(239, 68, 68, 0.2)",
                borderRadius: "6px",
                padding: "10px 12px",
                textAlign: "center",
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
              borderRadius: "8px",
              border: "none",
              padding: "12px 16px",
              fontSize: "15px",
              fontWeight: 600,
              background: "var(--primary-gradient)",
              color: "white",
              cursor: loading ? "default" : "pointer",
              opacity: loading ? 0.7 : 1,
              marginTop: "8px",
              boxShadow: "0 4px 14px 0 rgba(59, 130, 246, 0.39)",
            }}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p
          className="animate-fade-in stagger-2"
          style={{
            fontSize: "12px",
            color: "#64748b",
            marginTop: "32px",
            textAlign: "center",
          }}
        >
          Protected portal for medical professionals.
        </p>
      </div>
    </div>
  );
}
