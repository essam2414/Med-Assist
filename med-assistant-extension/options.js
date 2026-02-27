document.addEventListener('DOMContentLoaded', () => {
    const grantBtn = document.getElementById('grantBtn');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');

    // Immediately request permission on load
    requestMicPermission();

    grantBtn.addEventListener('click', () => {
        requestMicPermission();
    });

    async function requestMicPermission() {
        statusEl.textContent = 'Requesting microphone permission...';
        errorEl.textContent = '';

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            statusEl.textContent = 'Permission granted! You can now close this tab and return to the side panel to start capture.';

            // Stop tracks immediately
            stream.getTracks().forEach((track) => track.stop());
        } catch (err) {
            console.error(err);
            errorEl.textContent = 'Permission denied. Please click the button below to try again, or check your browser settings (look for the camera/mic icon in the address bar).';
            statusEl.textContent = '';
        }
    }
});
