// panel.js

const loginView = document.getElementById('login-view');
const appView = document.getElementById('app-view');
const loginBtn = document.getElementById('login-btn');

loginBtn.addEventListener('click', () => {
  chrome.tabs.create({ url: 'http://localhost:5173/' });
});

/* Permissions Management */
const permsIcon = document.getElementById('perms-icon');
const permsPopup = document.getElementById('perms-popup');
const micStatus = document.getElementById('mic-status');
const managePermsBtn = document.getElementById('manage-perms');
let currentMicPermission = 'prompt';

async function refreshPermissions() {
  try {
    const micPerm = await navigator.permissions.query({ name: 'microphone' });
    updatePermsUI(micPerm.state);
    micPerm.onchange = () => updatePermsUI(micPerm.state);
  } catch (e) {
    console.error('Permission query failed', e);
  }
}

function updatePermsUI(state) {
  currentMicPermission = state;
  const statusSubText = document.querySelector('#perms-popup p');

  if (state === 'granted') {
    permsIcon.classList.remove('missing');
    permsIcon.classList.add('granted');
    permsIcon.textContent = '🎙️';
    micStatus.textContent = 'Granted';
    micStatus.className = 'perms-channel-status perms-status-granted';

    if (managePermsBtn) {
      managePermsBtn.textContent = 'Manage Permissions';
      managePermsBtn.className = 'btn manage-perms-btn bg-red';
    }
    if (statusSubText) {
      statusSubText.innerHTML = 'Microphone is active. Click to manage settings.<br/><br/><strong>Tab Audio:</strong> When you press "Start Capture", ensure you select a tab and check the "Also share tab audio" box.';
    }

    if (startBtn) startBtn.disabled = statusLabel.textContent === 'Recording' || statusLabel.textContent === 'Processing';
  } else {
    permsIcon.classList.remove('granted');
    permsIcon.classList.add('missing');
    permsIcon.textContent = '!';
    micStatus.textContent = state === 'denied' ? 'Blocked' : 'Inactive';
    micStatus.className = 'perms-channel-status perms-status-missing';

    if (managePermsBtn) {
      managePermsBtn.textContent = 'Enable Microphone Access';
      managePermsBtn.className = 'btn manage-perms-btn bg-green';
    }
    if (statusSubText) {
      statusSubText.textContent = 'Microphone is inactive. Press to enable microphone.';
    }

    if (startBtn) startBtn.disabled = true;
  }
}

permsIcon.addEventListener('click', (e) => {
  e.stopPropagation();
  permsPopup.classList.toggle('active');
});

document.addEventListener('click', (e) => {
  if (!permsPopup.contains(e.target) && e.target !== permsIcon) {
    permsPopup.classList.remove('active');
  }
});

managePermsBtn.addEventListener('click', () => {
  chrome.runtime.openOptionsPage();
});

function checkAuthStatus() {
  chrome.cookies.get({ url: 'http://localhost', name: 'logged_in' }, (cookie1) => {
    chrome.cookies.get({ url: 'http://127.0.0.1', name: 'logged_in' }, (cookie2) => {
      if ((cookie1 && cookie1.value === '1') || (cookie2 && cookie2.value === '1')) {
        loginView.style.display = 'none';
        appView.style.display = 'flex';
        refreshPermissions();
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

// Initial check
checkAuthStatus();

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
const transcriptBox = document.getElementById('transcripts-container');

let mediaStream = null;
let micStream = null;
let liveAudio = null;
let audioContext = null;

let mediaRecorderTab = null;
let mediaRecorderMic = null;
let tabRecordedChunks = [];
let micRecordedChunks = [];
let tabBlob = null;
let micBlob = null;
let tabBlobUrl = null;
let micBlobUrl = null;
let recordingTabId = null;

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

  startBtn.disabled = currentMicPermission !== 'granted';
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
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
  if (liveAudio) {
    liveAudio.pause();
    liveAudio.srcObject = null;
    liveAudio = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (recordingTabId) {
    chrome.tabs.update(recordingTabId, { muted: false }).catch(() => { });
    recordingTabId = null;
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
  statusEl.textContent = 'Starting capture…';

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
        video: { displaySurface: 'browser' },
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
    mediaStream.getVideoTracks().forEach(track => track.stop());

    // 2. Capture Microphone with Acoustic Echo Cancellation
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    // 3. Mute to prevent physical iteration, pipe to internal audio renderer
    recordingTabId = tab.id;
    await chrome.tabs.update(recordingTabId, { muted: true });

    liveAudio = new Audio();
    liveAudio.srcObject = mediaStream;
    liveAudio.volume = 1;
    liveAudio.play();

    // 4. Record the specific streams independently!
    tabRecordedChunks = [];
    micRecordedChunks = [];
    tabBlob = null;
    micBlob = null;

    if (tabBlobUrl) { URL.revokeObjectURL(tabBlobUrl); tabBlobUrl = null; }
    if (micBlobUrl) { URL.revokeObjectURL(micBlobUrl); micBlobUrl = null; }
    transcribeBtn.disabled = true;

    // Start Tab Recorder
    mediaRecorderTab = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
    mediaRecorderTab.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) tabRecordedChunks.push(e.data);
    };
    mediaRecorderTab.onstop = () => {
      tabBlob = new Blob(tabRecordedChunks, { type: 'audio/webm' });
      checkBlobsReady();
    };

    // Start Mic Recorder
    mediaRecorderMic = new MediaRecorder(micStream, { mimeType: 'audio/webm' });
    mediaRecorderMic.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) micRecordedChunks.push(e.data);
    };
    mediaRecorderMic.onstop = () => {
      micBlob = new Blob(micRecordedChunks, { type: 'audio/webm' });
      checkBlobsReady();
    };

    mediaRecorderTab.start();
    mediaRecorderMic.start();

    setStateRecording();
    resetProgress();
  } catch (err) {
    console.error('Error starting capture:', err);
    setStateIdle('Error starting capture: ' + err.message);
    cleanupStream();
  }
});

function checkBlobsReady() {
  if (tabBlob && micBlob) {
    cleanupStream(); // Stream cleanup done after both blobs are ready
    tabBlobUrl = URL.createObjectURL(tabBlob);
    micBlobUrl = URL.createObjectURL(micBlob);

    audioEl.src = tabBlobUrl;
    // Note: We use the tab audio duration to represent the whole clip since they start/stop together
    transcribeBtn.disabled = false;
    setStateReady();
  }
}

stopBtn.addEventListener('click', () => {
  let isRecording = false;
  if (mediaRecorderTab && mediaRecorderTab.state !== 'inactive') {
    mediaRecorderTab.stop();
    isRecording = true;
  }
  if (mediaRecorderMic && mediaRecorderMic.state !== 'inactive') {
    mediaRecorderMic.stop();
    isRecording = true;
  }
  if (isRecording) {
    setStateProcessing();
    statusEl.textContent = 'Stopping capture and finalising audio…';
  }
});

playBtn.addEventListener('click', () => {
  if (tabBlobUrl) {
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

  if (!tabBlob || !micBlob) {
    alert("Audio is not fully recorded yet.");
    return;
  }

  transcribeBtn.disabled = true;
  const originalText = transcribeBtn.innerHTML;
  transcribeBtn.innerHTML = '<span class="btn-icon">⏳</span> Transcribing...';

  const formData = new FormData();
  formData.append('audio_file', tabBlob, 'tab_recording.webm');
  formData.append('mic_file', micBlob, 'mic_recording.webm');
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
    transcriptBox.style.display = 'flex';

    if (Array.isArray(data)) {
      data.forEach(segment => {
        const entry = document.createElement('div');
        entry.className = 'transcript-entry';
        let timeStr = formatTime(segment.start_time || 0);
        entry.innerHTML = `
              <div class="transcript-speaker">${segment.speaker || 'Speaker'} <span style="color:var(--text-muted); font-weight:normal;">[${timeStr}]</span></div>
              <div class="transcript-text">${segment.text}</div>
            `;
        transcriptBox.appendChild(entry);
      })
    } else {
      const entry = document.createElement('div');
      entry.className = 'transcript-entry';
      let timeStr = formatTime(data.start_time || 0);
      entry.innerHTML = `
          <div class="transcript-speaker">${data.speaker || 'Speaker'} <span style="color:var(--text-muted); font-weight:normal;">[${timeStr}]</span></div>
          <div class="transcript-text">${data.text}</div>
        `;
      transcriptBox.appendChild(entry);
    }
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
