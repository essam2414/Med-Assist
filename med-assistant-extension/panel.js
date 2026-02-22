// panel.js

const statusEl = document.getElementById('status');
const startBtn = document.getElementById('start');
const stopBtn = document.getElementById('stop');
const playBtn = document.getElementById('play');
const audioEl = document.getElementById('player');

let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let recordedBlobUrl = null;
let audioContext = null;
let sourceNode = null;

// Helper: clean up stream and audio context
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

startBtn.addEventListener('click', async () => {
  statusEl.textContent = 'Starting capture...';

  try {
    // Get the active tab id
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true
    });

    if (!tab || !tab.id || tab.url.startsWith('chrome://')) {
      statusEl.textContent = 'Cannot capture this page.';
      return;
    }

    // 1) Get a streamId for this tab
    const streamId = await new Promise((resolve, reject) => {
      chrome.tabCapture.getMediaStreamId({ targetTabId: tab.id }, (id) => {
        if (chrome.runtime.lastError) {
          reject(chrome.runtime.lastError);
        } else {
          resolve(id);
        }
      });
    });

    // 2) Use getUserMedia with that streamId
    mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        mandatory: {
          chromeMediaSource: 'tab',
          chromeMediaSourceId: streamId
        }
      },
      video: false
    });

    // Play audio so you can still hear it while recording
    audioContext = new AudioContext();
    sourceNode = audioContext.createMediaStreamSource(mediaStream);
    sourceNode.connect(audioContext.destination);

    // Set up recorder
    recordedChunks = [];
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

      playBtn.disabled = false;
      statusEl.textContent = 'Recording ready.';

      cleanupStream();
    };

    mediaRecorder.start();
    statusEl.textContent = 'Capturing tab audio...';
    startBtn.disabled = true;
    stopBtn.disabled = false;
    playBtn.disabled = true;
  } catch (err) {
    console.error('Error starting capture:', err);
    statusEl.textContent = 'Error starting capture: ' + err.message;
    cleanupStream();
  }
});

stopBtn.addEventListener('click', () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    statusEl.textContent = 'Stopping capture...';
    mediaRecorder.stop();
  } else {
    cleanupStream();
    statusEl.textContent = 'Not capturing.';
  }
  startBtn.disabled = false;
  stopBtn.disabled = true;
});

playBtn.addEventListener('click', () => {
  if (recordedBlobUrl) {
    audioEl.play();
  }
});
