// frontend/src/api.js
const API_URL = "http://localhost:8000";

export async function fetchConsultations() {
  const res = await fetch(`${API_URL}/consultations`);
  if (!res.ok) throw new Error("Failed to load consultations");
  return res.json();
}

export async function createConsultation(title) {
  const res = await fetch(`${API_URL}/consultations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error("Failed to create consultation");
  return res.json();
}
