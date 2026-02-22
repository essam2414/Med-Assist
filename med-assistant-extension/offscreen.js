// offscreen.js

let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let audioContext = null;
let sourceNode = null;

const videoEl = document.getElementById('hiddenVideo');

// Connect to background
const port = chrome.runtime.connect({ name: 'offscreen' });

port.onMessage.addListener((message) => {
  if (message.type === 'start-recording' && message.stream) {
    startRecording(message.stream);
  }

  if (message.type === 'stop-recording') {
    stopRecording();
  }
});

function startRecording(stream) {
  if (mediaRecorder) return;

  mediaStream = stream;

  // 1) Play audio so you can hear YouTube/Meet while recording
  videoEl.srcObject = mediaStream;

  audioContext = new AudioContext();
  sourceNode = audioContext.createMediaStreamSource(mediaStream);
  sourceNode.connect(audioContext.destination);

  // 2) Record the audio
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

    blob.arrayBuffer().then((buffer) => {
      chrome.runtime.sendMessage({
        type: 'recording-ready',
        audioBlob: {
          type: blob.type,
          data: Array.from(new Uint8Array(buffer))
        }
      });
    });

    cleanup();
  };

  mediaRecorder.start();
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop();
  } else {
    cleanup();
  }
}

function cleanup() {
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
  mediaRecorder = null;
  recordedChunks = [];
}
