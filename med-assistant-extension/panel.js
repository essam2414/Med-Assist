// panel.js

const loginView = document.getElementById('login-view');
const appView = document.getElementById('app-view');
const loginBtn = document.getElementById('login-btn');

loginBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:5173/' });
});

function checkAuthStatus() {
  chrome.cookies.get({ url: 'http://localhost', name: 'logged_in' }, (cookie1) => {
    chrome.cookies.get({ url: 'http://127.0.0.1', name: 'logged_in' }, (cookie2) => {
      if ((cookie1 && cookie1.value === '1') || (cookie2 && cookie2.value === '1')) {
        loginView.style.display = 'none';
        appView.style.display = 'flex';
      } else {
        loginView.style.display = 'flex';
        appView.style.display = 'none';
      }
    });
  });
}

// Initial check
checkAuthStatus();

// Add listeners to detect login state changes efficiently
window.addEventListener('focus', checkAuthStatus);

if (chrome.tabs) {
  chrome.tabs.onActivated.addListener(checkAuthStatus);
  chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url && (tab.url.includes('localhost') || tab.url.includes('127.0.0.1'))) {
      checkAuthStatus();
    }
  });
}

if (chrome.cookies) {
  chrome.cookies.onChanged.addListener((changeInfo) => {
    if (changeInfo.cookie.name === 'logged_in') {
      checkAuthStatus();
    }
  });
}

const statusEl = document.getElementById('status');
const statusDot = document.getElementById('status-dot');
const statusLabel = document.getElementById('status-label');

const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const playBtn = document.getElementById('play');
const audioEl = document.getElementById('player');

const bar = document.getElementById('audio-bar');
const barFill = document.getElementById('audio-bar-fill');
const timeCurrent = document.getElementById('time-current');
const timeDuration = document.getElementById('time-duration');

const transcribeBtn = document.getElementById('transcribe');
const consultationSelect = document.getElementById('consultation-select');
const transcriptBox = document.getElementById('transcript-box');

let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordedBlobUrl = null;
let audioContext = null;
let sourceNode = null;

function formatTime(seconds) {
  if (!isFinite(seconds)) return '0:00';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60)
    .toString()
    .padStart(2, '0');
  return `${m}:${s}`;
}

function setStateIdle(message) {
  statusEl.textContent =
    message ||
    'Not capturing. Open this on a tab with an active call or video.';
  statusDot.classList.remove('active');
  statusDot.classList.add('idle');
  statusLabel.textContent = 'Idle';

  startBtn.disabled = false;
  stopBtn.disabled = true;
}

function setStateRecording() {
  statusEl.textContent =
    'Capturing tab audio… stop when the consultation segment is complete.';
  statusDot.classList.remove('idle');
  statusDot.classList.add('active');
  statusLabel.textContent = 'Recording';

  startBtn.disabled = true;
  stopBtn.disabled = false;
  playBtn.disabled = true;
}

function setStateProcessing() {
  statusEl.textContent = 'Processing recording…';
  statusDot.classList.remove('active');
  statusDot.classList.add('idle');
  statusLabel.textContent = 'Processing';

  startBtn.disabled = true;
  stopBtn.disabled = true;
}

function setStateReady() {
  statusEl.textContent =
    'Recording ready. Play it back or send it to your AI backend.';
  statusDot.classList.remove('active');
  statusDot.classList.add('idle');
  statusLabel.textContent = 'Ready';

  startBtn.disabled = false;
  stopBtn.disabled = true;
  playBtn.disabled = false;
}

function cleanupStream() {
  if (sourceNode) {
    sourceNode.disconnect();
    sourceNode = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
}

function resetProgress() {
  barFill.style.width = '0%';
  timeCurrent.textContent = '0:00';
  timeDuration.textContent = '0:00';
}

function loadConsultations() {
  fetch('http://localhost:8000/consultations/', {
    headers: {},
    credentials: 'include'
  })
    .then(res => res.json())
    .then(data => {
      consultationSelect.innerHTML = '<option value="">Select a consultation</option>';
      if (Array.isArray(data)) {
        data.forEach(c => {
          const opt = document.createElement('option');
          opt.value = c.id;
          opt.textContent = c.title || `Consultation ${c.id}`;
          consultationSelect.appendChild(opt);
        });
      }
    })
    .catch(err => {
      console.error('Failed to load consultations:', err);
      consultationSelect.innerHTML = '<option value="">Error loading consultations</option>';
    });
}

// Call loadConsultations after initial auth check if logged in
function checkAuthStatus() {
  chrome.cookies.get({ url: 'http://localhost', name: 'logged_in' }, (cookie1) => {
    chrome.cookies.get({ url: 'http://127.0.0.1', name: 'logged_in' }, (cookie2) => {
      if ((cookie1 && cookie1.value === '1') || (cookie2 && cookie2.value === '1')) {
        loginView.style.display = 'none';
        appView.style.display = 'flex';
        // Only load if we haven't loaded yet
        if (consultationSelect.options.length <= 1) {
          loadConsultations();
        }
      } else {
        loginView.style.display = 'flex';
        appView.style.display = 'none';
      }
    });
  });
}

function displayTranscripts(transcripts) {
  if (!transcripts || transcripts.length === 0) {
    transcriptBox.style.display = 'none';
    return;
  }

  transcriptBox.style.display = 'flex';
  transcriptBox.innerHTML = '';

  // Sort transcripts by start time
  const sorted = [...transcripts].sort((a, b) => a.start_time - b.start_time);

  sorted.forEach(t => {
    const entry = document.createElement('div');
    entry.className = 'transcript-entry';

    let timeStr = formatTime(t.start_time);

    entry.innerHTML = `
      <div class="transcript-speaker">${t.speaker || 'Speaker'} <span style="color:var(--text-muted); font-weight:normal;">[${timeStr}]</span></div>
      <div class="transcript-text">${t.text}</div>
    `;
    transcriptBox.appendChild(entry);
  });

  transcriptBox.scrollTop = transcriptBox.scrollHeight;
}

consultationSelect.addEventListener('change', () => {
  const consultationId = consultationSelect.value;
  if (!consultationId) {
    displayTranscripts([]);
    return;
  }

  // Fetch transcripts for this consultation
  fetch(`http://localhost:8000/consultations/`, { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
      const consultation = data.find(c => c.id == consultationId);
      if (consultation && consultation.transcripts) {
        displayTranscripts(consultation.transcripts);
      } else {
        displayTranscripts([]);
      }
    })
    .catch(console.error);
});

startBtn.addEventListener('click', async () => {
  setStateProcessing();
  statusEl.textContent = 'Requesting permission and starting capture…';

  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      lastFocusedWindow: true
    });

    if (tab && tab.url && tab.url.startsWith('chrome://')) {
      setStateIdle('Cannot capture chrome:// pages. Try a normal website tab.');
      return;
    }

    try {
      mediaStream = await navigator.mediaDevices.getDisplayMedia({
        audio: true,
        video: {
          displaySurface: 'browser'
        },
        preferCurrentTab: false
      });
    } catch (e) {
      if (e.name === 'NotAllowedError') {
        setStateIdle('Permission denied or window closed. Capture was cancelled.');
        return;
      }
      throw e;
    }

    const audioTrack = mediaStream.getAudioTracks()[0];
    if (!audioTrack) {
      mediaStream.getTracks().forEach(track => track.stop());
      setStateIdle('Please check "Share audio" when selecting a tab or screen.');
      return;
    }

    // Stop video tracks since we only want audio
    mediaStream.getVideoTracks().forEach(track => track.stop());

    const audioStream = new MediaStream([audioTrack]);

    audioContext = new AudioContext();
    sourceNode = audioContext.createMediaStreamSource(audioStream);

    recordedChunks = [];
    resetProgress();

    mediaRecorder = new MediaRecorder(audioStream, {
      mimeType: 'audio/webm'
    });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'audio/webm' });

      if (recordedBlobUrl) {
        URL.revokeObjectURL(recordedBlobUrl);
      }

      recordedBlobUrl = URL.createObjectURL(blob);
      audioEl.src = recordedBlobUrl;

      transcribeBtn.disabled = false;

      cleanupStream();
      setStateReady();
    };

    mediaRecorder.start();
    setStateRecording();
  } catch (err) {
    console.error('Error starting capture:', err);
    setStateIdle('Error starting capture: ' + err.message);
    cleanupStream();
  }
});

stopBtn.addEventListener('click', () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    setStateProcessing();
    statusEl.textContent = 'Stopping capture and finalising audio…';
    mediaRecorder.stop();
  } else {
    cleanupStream();
    setStateIdle();
  }
});

playBtn.addEventListener('click', () => {
  if (recordedBlobUrl) {
    audioEl.currentTime = 0;
    audioEl.play();
  }
});

transcribeBtn.addEventListener('click', async () => {
  const consultationId = consultationSelect.value;
  if (!consultationId) {
    alert("Please select a consultation session first.");
    return;
  }

  if (recordedChunks.length === 0) {
    alert("No audio recorded.");
    return;
  }

  transcribeBtn.disabled = true;
  const originalText = transcribeBtn.innerHTML;
  transcribeBtn.innerHTML = '<span class="btn-icon">⏳</span> Transcribing...';

  const blob = new Blob(recordedChunks, { type: 'audio/webm' });
  const formData = new FormData();
  formData.append('audio', blob, 'recording.webm');
  formData.append('consultation_id', consultationId);

  try {
    const res = await fetch('http://localhost:8000/transcripts/upload', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    const data = await res.json();

    // Add the new transcript to the display
    transcriptBox.style.display = 'flex';
    const entry = document.createElement('div');
    entry.className = 'transcript-entry';
    let timeStr = formatTime(data.start_time || 0);
    entry.innerHTML = `
      <div class="transcript-speaker">${data.speaker || 'Speaker'} <span style="color:var(--text-muted); font-weight:normal;">[${timeStr}]</span></div>
      <div class="transcript-text">${data.text}</div>
    `;
    transcriptBox.appendChild(entry);
    transcriptBox.scrollTop = transcriptBox.scrollHeight;

  } catch (e) {
    console.error('Transcription error:', e);
    alert('Transcription error: ' + e.message);
  } finally {
    transcribeBtn.disabled = false;
    transcribeBtn.innerHTML = originalText;
  }
});

// Update progress bar and times
audioEl.addEventListener('loadedmetadata', () => {
  timeDuration.textContent = formatTime(audioEl.duration);
});

audioEl.addEventListener('timeupdate', () => {
  const current = audioEl.currentTime || 0;
  const duration = audioEl.duration || 0;
  timeCurrent.textContent = formatTime(current);
  timeDuration.textContent = formatTime(duration);

  const pct = duration ? (current / duration) * 100 : 0;
  barFill.style.width = `${pct}%`;
});

// Click-to-seek
bar.addEventListener('click', (event) => {
  if (!audioEl.src || !isFinite(audioEl.duration)) return;

  const rect = bar.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const ratio = Math.min(Math.max(x / rect.width, 0), 1);
  audioEl.currentTime = ratio * audioEl.duration;
});
