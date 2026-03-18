// options.js
document.addEventListener('DOMContentLoaded', () => {
  const backendInput   = document.getElementById('backend-url');
  const dashboardInput = document.getElementById('dashboard-url');
  const saveBtn        = document.getElementById('save-btn');
  const savedMsg       = document.getElementById('saved-msg');

  // Load saved values
  chrome.storage.local.get(['backendUrl', 'dashboardUrl'], (res) => {
    backendInput.value   = res.backendUrl   || 'http://localhost:8000';
    dashboardInput.value = res.dashboardUrl || 'http://localhost:5173';
  });

  saveBtn.addEventListener('click', () => {
    chrome.storage.local.set({
      backendUrl:   backendInput.value.trim().replace(/\/$/, ''),
      dashboardUrl: dashboardInput.value.trim().replace(/\/$/, '')
    }, () => {
      savedMsg.style.display = 'block';
      setTimeout(() => { savedMsg.style.display = 'none'; }, 3000);
    });
  });
});
