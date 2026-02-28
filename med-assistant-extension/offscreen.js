// offscreen.js

let mediaRecorder = null;
let recordedChunks = [];
let audioContext = null;
let micStream = null;

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'start-offscreen-recording') {
    startRecording();
  }

  if (message.type === 'stop-offscreen-recording') {
    stopRecording();
  }
});

async function startRecording() {
  if (mediaRecorder) return;

  try {
    micStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    });

    recordedChunks = [];
    mediaRecorder = new MediaRecorder(micStream, {
      mimeType: 'audio/webm'
    });

    mediaRecorder.ondataavailable = (event) => {
      if (event.data && event.data.size > 0) {
        recordedChunks.push(event.data);
      }
    };

    mediaRecorder.onstop = () => {
      const blob = new Blob(recordedChunks, { type: 'audio/webm' });
      blob.arrayBuffer().then((buffer) => {
        chrome.runtime.sendMessage({
          type: 'mic-recording-ready',
          audioBlob: {
            type: blob.type,
            data: Array.from(new Uint8Array(buffer))
          }
        });
      });
      cleanup();
    };

    mediaRecorder.start();

  } catch (err) {
    console.error("Offscreen capture error:", err);
    chrome.runtime.sendMessage({
      type: 'error',
      message: err.message || err.toString()
    });
    cleanup();
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  } else {
    cleanup();
  }
}

function cleanup() {
  if (micStream) {
    micStream.getTracks().forEach((t) => t.stop());
    micStream = null;
  }
  mediaRecorder = null;
  recordedChunks = [];
}

