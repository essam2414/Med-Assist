// panel.js

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

startBtn.addEventListener('click', async () => {
  setStateProcessing();
  statusEl.textContent = 'Requesting permission and starting capture…';

  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    if (!tab || !tab.id || tab.url.startsWith('chrome://')) {
      setStateIdle('Cannot capture this page. Try a normal website tab.');
      return;
    }

    const streamId = await new Promise((resolve, reject) => {
      chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id }, (id) => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          resolve(id);
        }
      });
    });

    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId
        }
      },
      video: false
    });

    audioContext = new AudioContext();
    sourceNode = audioContext.createMediaStreamSource(mediaStream);
    sourceNode.connect(audioContext.destination);

    recordedChunks = [];
    resetProgress();

    mediaRecorder = new MediaRecorder(mediaStream, {
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
