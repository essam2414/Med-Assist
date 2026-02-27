// background.js

// Enable the side panel to open when the extension icon is clicked on any page
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
  .catch((error) => console.error(error));

chrome.runtime.onInstalled.addListener(() => {
  chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
    .catch((error) => console.error(error));
});

let recordingTabId = null;

async function setupOffscreenDocument(path) {
  const offscreenUrl = chrome.runtime.getURL(path);
  const existingContexts = await chrome.runtime.getContexts({
    contextTypes: ['OFFSCREEN_DOCUMENT'],
    documentUrls: [offscreenUrl]
  });

  if (existingContexts.length > 0) {
    return;
  }

  await chrome.offscreen.createDocument({
    url: path,
    reasons: ['USER_MEDIA', 'DISPLAY_MEDIA'],
    justification: 'Recording tab audio and microphone audio'
  });
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'start-recording-request') {
    (async () => {
      await setupOffscreenDocument('offscreen.html');

      chrome.runtime.sendMessage({
        type: 'start-offscreen-recording'
      });
    })();
    return true; // async
  }

  if (message.type === 'stop-recording-request') {
    chrome.runtime.sendMessage({ type: 'stop-offscreen-recording' });
  }

  // The offscreen doc sends back the audioblob, forward it to the panel
  if (message.type === 'recording-ready') {
    // We broadcast it, panel.js will be listening
    chrome.runtime.sendMessage(message);

    // Optionally close the offscreen document when done
    // chrome.offscreen.closeDocument()
  }
});
