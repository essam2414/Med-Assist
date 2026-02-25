// frontend/src/api.js
const API_URL = "http://localhost:8000";

export async function login(email, password) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
    credentials: "include",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = data.detail || "Login failed";
    throw new Error(detail);
  }
  return res.json(); // { access_token, token_type }
}

export async function logout() {
  const res = await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  return res.json().catch(() => ({}));
}

export async function fetchConsultations() {
  const res = await fetch(`${API_URL}/consultations`, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to load consultations");
  return res.json();
}

export async function createConsultation(title) {
  const res = await fetch(`${API_URL}/consultations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ title }),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to create consultation");
  return res.json();
}
