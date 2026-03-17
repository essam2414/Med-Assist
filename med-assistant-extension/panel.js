// panel.js — Med Assist Live Insights

let API_BASE = 'http://localhost:8000';
let DASHBOARD_URL = 'http://localhost:5173';

// Load saved URLs from storage
chrome.storage.local.get(['backendUrl', 'dashboardUrl'], (res) => {
  if (res.backendUrl)   API_BASE       = res.backendUrl;
  if (res.dashboardUrl) DASHBOARD_URL  = res.dashboardUrl;
});

// ─── View elements ───────────────────────────────────────────────
const loginView   = document.getElementById('login-view');
const waitingView = document.getElementById('waiting-view');
const activeView  = document.getElementById('active-view');

// Consultation card elements
const consultTitle   = document.getElementById('consult-title');
const statusBadge    = document.getElementById('status-badge');
const metaPatient    = document.getElementById('meta-patient');
const patientName    = document.getElementById('patient-name');
const consultTime    = document.getElementById('consult-time');
const liveBadge      = document.getElementById('live-badge');
const finishedBadge  = document.getElementById('finished-badge');

// Insights area
const insightsList   = document.getElementById('insights-list');
const emptyState     = document.getElementById('empty-state');
const insightCount   = document.getElementById('insight-count');

// Buttons
const loginBtn       = document.getElementById('login-btn');
const settingsBtn    = document.getElementById('settings-btn');

// ─── State ──────────────────────────────────────────────────────
let consultationPollInterval  = null;
let insightsPollInterval      = null;
let currentConsultation       = null;
let renderedInsightIds        = new Set();

// ─── View switcher ───────────────────────────────────────────────
function showView(name) {
  [loginView, waitingView, activeView].forEach(v => v.classList.remove('active'));
  document.getElementById(`${name}-view`).classList.add('active');
}

// ─── Auth ────────────────────────────────────────────────────────
function checkAuth() {
  chrome.cookies.get({ url: 'http://localhost', name: 'logged_in' }, (c1) => {
    chrome.cookies.get({ url: 'http://127.0.0.1', name: 'logged_in' }, (c2) => {
      const authed = (c1 && c1.value === '1') || (c2 && c2.value === '1');
      if (authed) {
        startConsultationPolling();
      } else {
        stopAllPolling();
        showView('login');
      }
    });
  });
}

// ─── Consultation polling ────────────────────────────────────────
function startConsultationPolling() {
  // If we have an active consultation already, go straight to insights
  if (currentConsultation && currentConsultation.status === 'draft') {
    showView('active');
    startInsightsPolling(currentConsultation.id);
    return;
  }
  showView('waiting');
  pollForActiveConsultation();
  if (!consultationPollInterval) {
    consultationPollInterval = setInterval(pollForActiveConsultation, 8000);
  }
}

async function pollForActiveConsultation() {
  try {
    const res = await fetch(`${API_BASE}/consultations/active`, {
      credentials: 'include'
    });
    if (res.status === 401) { checkAuth(); return; }
    if (!res.ok) return;

    const data = await res.json();
    if (data && data.id) {
      clearInterval(consultationPollInterval);
      consultationPollInterval = null;
      
      // If this is a different consultation than what we last knew about, clear state
      if (!currentConsultation || currentConsultation.id !== data.id) {
        clearInsightsState();
      }

      currentConsultation = data;
      renderConsultationCard(data);
      showView('active');
      startInsightsPolling(data.id);
    }
  } catch (e) {
    console.error('Consultation poll error:', e);
  }
}

// ─── Consultation card ───────────────────────────────────────────
function renderConsultationCard(c) {
  consultTitle.textContent = c.title || `Consultation ${c.id}`;

  if (c.patient && (c.patient.name || c.patient.display_id)) {
    patientName.textContent = c.patient.name
      ? `${c.patient.name} (${c.patient.display_id})`
      : c.patient.display_id;
    metaPatient.style.display = 'flex';
  } else {
    metaPatient.style.display = 'none';
  }

  if (c.created_at) {
    const d = new Date(c.created_at);
    consultTime.textContent = `Started ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`;
  }

  if (c.status === 'draft') {
    statusBadge.textContent = 'Active';
    statusBadge.className = 'status-badge status-active';
    liveBadge.style.display = 'flex';
    finishedBadge.style.display = 'none';
  } else {
    statusBadge.textContent = 'Finished';
    statusBadge.className = 'status-badge status-finished';
    liveBadge.style.display = 'none';
    finishedBadge.style.display = 'flex';
  }
}

// ─── Insights polling ────────────────────────────────────────────
function startInsightsPolling(consultationId) {
  stopInsightsPolling();
  fetchAndRenderInsights(consultationId);
  insightsPollInterval = setInterval(async () => {
    try {
      // Re-check consultation status each cycle
      const res = await fetch(`${API_BASE}/consultations/active`, { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        if (data && data.id === consultationId) {
          // Still active — update card, fetch insights
          currentConsultation = data;
          renderConsultationCard(data);
          await fetchAndRenderInsights(consultationId);
        } else if (data && data.id && data.id !== consultationId) {
          // A DIFFERENT consultation is now active
          handleConsultationEnded(consultationId);
        } else {
          // No active consultation
          handleConsultationEnded(consultationId);
        }
      } else if (res.status === 404) {
        handleConsultationEnded(consultationId);
      }
    } catch (e) {
      console.error('Insight poll error:', e);
    }
  }, 5000);
}

async function handleConsultationEnded(consultationId) {
  stopInsightsPolling();
  // Do one final insights fetch so the last update is captured
  await fetchAndRenderInsights(consultationId);
  
  if (currentConsultation && currentConsultation.id === consultationId) {
    currentConsultation.status = 'completed';
    renderConsultationCard(currentConsultation);
  }

  // Start polling for a new consultation
  setTimeout(() => {
    // Only reset if we are still looking at the same (now ended) consultation
    if (currentConsultation && currentConsultation.id === consultationId) {
      clearInsightsState();
      startConsultationPolling();
    }
  }, 10000); // reduced to 10s
}

function clearInsightsState() {
  renderedInsightIds.clear();
  insightsList.innerHTML = '';
  insightsList.appendChild(emptyState);
  emptyState.style.display = 'block';
  insightCount.textContent = '0 updates';
  currentConsultation = null;
}

function stopInsightsPolling() {
  if (insightsPollInterval) {
    clearInterval(insightsPollInterval);
    insightsPollInterval = null;
  }
}

function stopAllPolling() {
  if (consultationPollInterval) { clearInterval(consultationPollInterval); consultationPollInterval = null; }
  stopInsightsPolling();
  clearInsightsState();
}

async function fetchAndRenderInsights(consultationId) {
  try {
    const res = await fetch(`${API_BASE}/insights/live/${consultationId}`, {
      credentials: 'include'
    });
    if (!res.ok) return;
    const insights = await res.json();
    renderInsights(insights);
  } catch (e) {
    console.error('Insights fetch error:', e);
  }
}

// ─── Render insights (newest first, only append new ones) ────────
function renderInsights(insights) {
  if (!insights || insights.length === 0) return;

  // Count label
  insightCount.textContent = `${insights.length} update${insights.length !== 1 ? 's' : ''}`;
  emptyState.style.display = 'none';

  // Only insert insights we haven't rendered yet, maintaining newest-first order
  const newInsights = insights.filter(i => !renderedInsightIds.has(i.id));
  if (newInsights.length === 0) return;

  newInsights.forEach(insight => {
    renderedInsightIds.add(insight.id);
    const card = buildInsightCard(insight, insights.indexOf(insight) + 1);
    // Prepend so newest is at top
    const firstCard = insightsList.querySelector('.insight-card');
    if (firstCard) {
      insightsList.insertBefore(card, firstCard);
    } else {
      insightsList.appendChild(card);
    }
  });
}

function buildInsightCard(insight, updateNumber) {
  const card = document.createElement('div');
  card.className = 'insight-card';
  card.dataset.id = insight.id;

  const time = new Date(insight.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  const header = document.createElement('div');
  header.className = 'insight-card-header';
  header.innerHTML = `
    <span class="insight-update-label">Update ${updateNumber}</span>
    <span style="display:flex;align-items:center;gap:8px">
      <span class="insight-time">${time}</span>
      <svg class="insight-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
    </span>
  `;

  const body = document.createElement('div');
  body.className = 'insight-body';

  const fields = [
    { key: 'summary',             label: 'Summary',                labelClass: 'label-summary'     },
    { key: 'key_points',          label: 'New Problems',           labelClass: 'label-problems'    },
    { key: 'suggested_questions', label: 'Suggestions to Consider', labelClass: 'label-suggestions' },
    { key: 'risk_flags',          label: 'Risks / Context',        labelClass: 'label-risks'       },
  ];

  fields.forEach(({ key, label, labelClass }) => {
    const value = insight[key];
    if (!value || !value.trim()) return;
    const section = document.createElement('div');
    section.className = 'insight-section';
    section.innerHTML = `
      <div class="insight-section-label ${labelClass}">${label}</div>
      <div class="insight-section-text">${escapeHtml(value.trim())}</div>
    `;
    body.appendChild(section);
  });

  // Collapse toggle
  header.addEventListener('click', () => card.classList.toggle('collapsed'));

  card.appendChild(header);
  card.appendChild(body);
  return card;
}

function escapeHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// ─── Buttons ─────────────────────────────────────────────────────
loginBtn.addEventListener('click', () => {
  chrome.storage.local.get(['backendUrl'], (res) => {
    const url = res.backendUrl || 'http://localhost:5173';
    chrome.tabs.create({ url });
  });
});

settingsBtn.addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

// ─── Auth listeners ───────────────────────────────────────────────
window.addEventListener('focus', checkAuth);

if (chrome.cookies) {
  chrome.cookies.onChanged.addListener((change) => {
    if (change.cookie.name === 'logged_in') checkAuth();
  });
}

if (chrome.tabs) {
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url &&
        (tab.url.includes('localhost') || tab.url.includes('127.0.0.1'))) {
      checkAuth();
    }
  });
}

// ─── Init ────────────────────────────────────────────────────────
checkAuth();
