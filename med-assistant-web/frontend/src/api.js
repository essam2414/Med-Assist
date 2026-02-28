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

export async function fetchCurrentUser() {
  const res = await fetch(`${API_URL}/auth/me`, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to fetch user details");
  return res.json();
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

export async function createConsultation(title, patient_id = null) {
  const res = await fetch(`${API_URL}/consultations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ title, patient_id }),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to create consultation");
  return res.json();
}

export async function deleteConsultation(id) {
  const res = await fetch(`${API_URL}/consultations/${id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to delete consultation");
  return res.json();
}

export async function fetchActiveConsultation() {
  const res = await fetch(`${API_URL}/consultations/active`, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to load active consultation");
  return res.json();
}

export async function updateConsultationStatus(id, status) {
  const res = await fetch(`${API_URL}/consultations/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ status }),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to update consultation");
  return res.json();
}

export async function fetchPatients() {
  const res = await fetch(`${API_URL}/patients`, {
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) throw new Error("Failed to load patients");
  return res.json();
}

export async function createPatient(patientData) {
  const res = await fetch(`${API_URL}/patients`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(patientData),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to create patient");
  }
  return res.json();
}

export async function updatePatient(id, patientData) {
  const res = await fetch(`${API_URL}/patients/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(patientData),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to update patient");
  }
  return res.json();
}

export async function deletePatient(id) {
  const res = await fetch(`${API_URL}/patients/${id}`, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to delete patient");
  }
  return res.json();
}
