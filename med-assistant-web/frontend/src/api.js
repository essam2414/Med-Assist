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

export async function signup(name, email, password) {
  const res = await fetch(`${API_URL}/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const detail = data.detail || "Signup failed";
    throw new Error(detail);
  }
  return res.json();
}

export async function logout() {
  const res = await fetch(`${API_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  });
  return res.json().catch(() => ({}));
}

export async function changePassword(current_password, new_password) {
  const res = await fetch(`${API_URL}/auth/change-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ current_password, new_password }),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to change password");
  }
  return res.json();
}

export async function deleteAccount() {
  const res = await fetch(`${API_URL}/auth/me`, {
    method: "DELETE",
    credentials: "include",
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to delete account");
  }
  return res.json();
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

export async function updateUserProfile(data) {
  const res = await fetch(`${API_URL}/auth/me`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify(data),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to update profile");
  }
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

export async function createConsultation(title, patient_id = null, about = null) {
  const res = await fetch(`${API_URL}/consultations`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ title, patient_id, about }),
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

export async function fetchChatSessions() {
  const res = await fetch(`${API_URL}/api/chat/sessions`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });
  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error("Failed to load sessions");
  return res.json();
}

export async function createChatSession(title) {
  const res = await fetch(`${API_URL}/api/chat/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ title }),
  });
  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error("Failed to create session");
  return res.json();
}

export async function fetchChatSession(id) {
  const res = await fetch(`${API_URL}/api/chat/sessions/${id}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });
  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error("Failed to load session");
  return res.json();
}

export async function deleteChatSession(id) {
  const res = await fetch(`${API_URL}/api/chat/sessions/${id}`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
  });
  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error("Failed to delete session");
  return res.json();
}

export async function sendChatMessage(sessionId, message) {
  const res = await fetch(`${API_URL}/api/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ message }),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to send chat message");
  }
  return res.json();
}

export async function joinMeetingWithBot(consultationId, meetingUrl) {
  const res = await fetch(`${API_URL}/recall/join?consultation_id=${consultationId}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
    body: JSON.stringify({ meeting_url: meetingUrl }),
  });
  if (res.status === 401) {
    throw new Error("unauthorized");
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to join meeting with bot");
  }
  return res.json();
}

export async function disconnectBot(consultation_id) {
  const res = await fetch(`${API_URL}/recall/disconnect?consultation_id=${consultation_id}`, {
    method: "POST",
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
    throw new Error(data.detail || "Failed to disconnect bot");
  }
  return res.json();
}
export async function checkServerStatus() {
  const res = await fetch(`${API_URL}/health`);
  if (!res.ok) throw new Error("Server error");
  return res.json();
}

export async function generateConsultationInsights(consultationId) {
  const res = await fetch(`${API_URL}/insights/generate/${consultationId}`, {
    method: "GET",
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
    throw new Error(data.detail || "Failed to generate AI insights");
  }
  return res.json();
}

export async function fetchLiveInsights(consultationId) {
  const res = await fetch(`${API_URL}/insights/live/${consultationId}`, {
    method: "GET",
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
    throw new Error(data.detail || "Failed to fetch live insights");
  }
  return res.json();
}

// AI Analytics
export async function fetchWeeklyAnalytics(dateParam = null, generate = false) {
  let url = `${API_URL}/api/ai-analytics/weekly`;
  const params = new URLSearchParams();
  if (dateParam) params.append('target_date', dateParam);
  if (generate) params.append('generate', 'true');
  
  const queryString = params.toString();
  if (queryString) url += `?${queryString}`;
  
  const res = await fetch(url, {
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
    throw new Error(data.detail || "Failed to fetch weekly analytics");
  }
  return res.json();
}

