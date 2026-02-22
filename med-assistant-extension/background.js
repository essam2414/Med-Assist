// background.js

chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id || !tab.url || tab.url.startsWith('chrome://')) {
    console.warn('Cannot use assistant on this page');
    return;
  }

  // Attach side panel to this tab and open it
  chrome.sidePanel.setOptions(
    {
      tabId: tab.id,
      path: 'panel.html',
      enabled: true
    },
    () => {
      chrome.sidePanel.open({ tabId: tab.id });
    }
  );
});
