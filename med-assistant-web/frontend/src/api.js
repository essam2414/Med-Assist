// frontend/src/api.js
const API_URL = "http://localhost:8000";

export async function login(email, password) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = data.detail || "Login failed";
    throw new Error(detail);
  }
  return res.json(); // { access_token, token_type }
}

function authHeaders() {
  const token = localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function fetchConsultations() {
  const res = await fetch(`${API_URL}/consultations`, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
  });
  if (!res.ok) throw new Error("Failed to load consultations");
  return res.json();
}

export async function createConsultation(title) {
  const res = await fetch(`${API_URL}/consultations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
    },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create consultation");
  return res.json();
}
