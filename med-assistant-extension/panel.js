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
const audioEl = document.getElementById('player');
const consultationSelect = document.getElementById('consultation-select');
const transcriptBox = document.getElementById('transcripts-container');

let mediaStream = null;
let micStream = null;
let liveAudio = null;
let audioContext = null;
let analyser = null;
let dataArray = null;

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
    'Capturing audio… stop when the consultation segment is complete.';
  statusDot.classList.remove('idle');
  statusDot.classList.add('active');
  statusLabel.textContent = 'Recording';

  startBtn.disabled = true;
  stopBtn.disabled = false;
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
    'Recording complete. You can now transcribe the segment.';
  statusDot.classList.remove('active');
  statusDot.classList.add('idle');
  statusLabel.textContent = 'Ready';

  startBtn.disabled = false;
  stopBtn.disabled = true;
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
    if (audioContext.state !== 'closed') {
      audioContext.close();
    }
    audioContext = null;
  }
  analyser = null;
  dataArray = null;
  if (recordingTabId) {
    chrome.tabs.update(recordingTabId, { muted: false }).catch(() => { });
    recordingTabId = null;
  }
}

function resetProgress() {
  // No-op - removed progress bar
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

let liveInterval = null;
let totalOffset = 0;
const CHUNK_INTERVAL_MS = 10000;

startBtn.addEventListener('click', async () => {
  const consultationId = consultationSelect.value;
  if (!consultationId) {
    alert("Please select a consultation session first.");
    return;
  }

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

    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    recordingTabId = tab.id;
    await chrome.tabs.update(recordingTabId, { muted: true });

    liveAudio = new Audio();
    liveAudio.srcObject = mediaStream;
    liveAudio.volume = 1;
    liveAudio.play();

    let currentChunkOffset = 0;
    let pendingTabBlob = null;
    let pendingMicBlob = null;
    let chunkHasAudio = false; // Flag to track if the current interval has speech

    // Functions to handle the chunking cycles
    const startNewChunk = () => {
      // Use localized arrays for this specific chunk
      const localTabChunks = [];
      const localMicChunks = [];

      const recorderTab = new MediaRecorder(mediaStream, { mimeType: 'audio/webm' });
      const recorderMic = new MediaRecorder(micStream, { mimeType: 'audio/webm' });

      recorderTab.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) localTabChunks.push(e.data);
      };
      recorderMic.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) localMicChunks.push(e.data);
      };

      // Capture the current offset for THIS specific chunk
      const offsetAtStart = currentChunkOffset;

      recorderTab.onstop = async () => {
        const tBlob = new Blob(localTabChunks, { type: 'audio/webm' });
        checkAndSend(tBlob, 'tab', offsetAtStart);
      };
      recorderMic.onstop = async () => {
        const mBlob = new Blob(localMicChunks, { type: 'audio/webm' });
        checkAndSend(mBlob, 'mic', offsetAtStart);
      };

      recorderTab.start();
      recorderMic.start();

      return { recorderTab, recorderMic };
    };

    const checkAndSend = async (blob, source, offset) => {
      if (source === 'tab') pendingTabBlob = blob;
      if (source === 'mic') pendingMicBlob = blob;

      if (pendingTabBlob && pendingMicBlob) {
        const t = pendingTabBlob;
        const m = pendingMicBlob;
        pendingTabBlob = null;
        pendingMicBlob = null;

        console.log(`Sending chunk to backend with offset: ${offset}`);
        await sendChunkToBackend(t, m, consultationId, offset);
      }
    };

    // Silence detection setup
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const source = audioContext.createMediaStreamSource(micStream);
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    dataArray = new Uint8Array(analyser.frequencyBinCount);

    const getVolume = () => {
      analyser.getByteFrequencyData(dataArray);
      let values = 0;
      for (let i = 0; i < dataArray.length; i++) {
        values += dataArray[i];
      }
      const volume = values / dataArray.length;
      // If volume is above threshold, mark the chunk as having audio
      if (volume > 5) chunkHasAudio = true;
      return volume;
    };

    const waitForSilenceAndCycle = () => {
      const SILENCE_THRESHOLD = 8; // Adjust based on testing
      const checkSilence = () => {
        const volume = getVolume();
        // console.log('Current volume:', volume);

        if (volume < SILENCE_THRESHOLD) {
          console.log('Silence detected, cycling recorders...');
          // 1. Stop the current ones
          if (activeRecorders.recorderTab.state === 'recording') activeRecorders.recorderTab.stop();
          if (activeRecorders.recorderMic.state === 'recording') activeRecorders.recorderMic.stop();

          // 2. Increment offset BEFORE starting the next one
          // Note: The actual chunk might be slightly longer than 10s now
          // For simplicity, we keep the increment but ideally we'd use performance.now()
          currentChunkOffset += (Date.now() - lastCycleTime) / 1000;
          lastCycleTime = Date.now();

          // 3. Start the next cycle
          const wasSufficientlyAudible = chunkHasAudio;
          chunkHasAudio = false; // Reset for next chunk
          activeRecorders = startNewChunk();
          activeRecorders.wasAudible = wasSufficientlyAudible;
        } else {
          // Still speaking, wait 500ms and check again
          setTimeout(checkSilence, 500);
        }
      };
      checkSilence();
    };

    // Keep track of the ACTIVE recorders so we can stop them in the interval
    let lastCycleTime = Date.now();
    let activeRecorders = startNewChunk();
    activeRecorders.wasAudible = false; // Initialize for the first chunk

    // Loop interval
    liveInterval = setInterval(() => {
      console.log('Interval reached, waiting for a pause to cycle...');
      waitForSilenceAndCycle();
    }, CHUNK_INTERVAL_MS);

    setStateRecording();
    resetProgress();
  } catch (err) {
    console.error('Error starting capture:', err);
    setStateIdle('Error starting capture: ' + err.message);
    cleanupStream();
  }
});

async function sendChunkToBackend(tabBlob, micBlob, consultationId, offset) {
  const formData = new FormData();
  formData.append('audio_file', tabBlob, 'tab_chunk.webm');
  formData.append('mic_file', micBlob, 'mic_chunk.webm');
  formData.append('consultation_id', consultationId);
  formData.append('offset', offset);

  try {
    const res = await fetch('http://localhost:8000/transcripts/upload', {
      method: 'POST',
      body: formData,
      credentials: 'include'
    });

    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        data.forEach(segment => addSegmentToTranscript(segment));
      } else {
        addSegmentToTranscript(data);
      }
    }
  } catch (e) {
    console.error('Live chunk error:', e);
  }
}

function addSegmentToTranscript(segment) {
  transcriptBox.style.display = 'flex';
  const entry = document.createElement('div');
  entry.className = 'transcript-entry';
  let timeStr = formatTime(segment.start_time || 0);
  entry.innerHTML = `
    <div class="transcript-speaker">${segment.speaker || 'Speaker'} <span style="color:var(--text-muted); font-weight:normal;">[${timeStr}]</span></div>
    <div class="transcript-text">${segment.text}</div>
  `;
  transcriptBox.appendChild(entry);
  transcriptBox.scrollTop = transcriptBox.scrollHeight;
}

stopBtn.addEventListener('click', () => {
  if (liveInterval) {
    clearInterval(liveInterval);
    liveInterval = null;
  }

  if (mediaRecorderTab && mediaRecorderTab.state !== 'inactive') mediaRecorderTab.stop();
  if (mediaRecorderMic && mediaRecorderMic.state !== 'inactive') mediaRecorderMic.stop();

  setStateIdle('Capture stopped.');
  cleanupStream();
});

// End of file
