document.addEventListener('DOMContentLoaded', () => {
    const grantBtn = document.getElementById('grantBtn');
    const statusEl = document.getElementById('status');
    const errorEl = document.getElementById('error');

    async function checkPermission() {
        try {
            const micPerm = await navigator.permissions.query({ name: 'microphone' });
            updateUI(micPerm.state);

            micPerm.onchange = () => {
                updateUI(micPerm.state);
            };
        } catch (e) {
            console.error('Permission query error', e);
            updateUI('prompt');
        }
    }

    function updateUI(state) {
        if (state === 'granted') {
            document.querySelector('h2').textContent = 'Microphone Access: Active';
            document.querySelector('p').innerHTML = `
                The extension has access to your microphone.
                <br/><br/>
                <strong>How to Revoke Access:</strong><br/>
                1. Click the <strong>Microphone icon</strong> (🎙️) on the far right of the address bar.<br/>
                2. Select <strong>"Continue blocking..."</strong> or click <strong>Manage</strong> to reset permissions.<br/>
                3. Alternatively, click the <strong>Settings icon</strong> (left of URL) and toggle off the Microphone.
            `;
            statusEl.textContent = 'Status: GRANTED';
            statusEl.style.color = '#4ade80';
            errorEl.textContent = ''; // Explicitly clear any previous error
            grantBtn.textContent = 'Disable Microphone Access';
            grantBtn.style.backgroundColor = '#ef4444'; // Red for disable
        } else {
            document.querySelector('h2').textContent = 'Microphone Access: Inactive';
            document.querySelector('p').innerHTML = `
                The extension needs microphone access to capture your voice during consultations.
            `;
            statusEl.textContent = state === 'denied' ? 'Status: BLOCKED' : 'Status: NOT GRANTED';
            statusEl.style.color = state === 'denied' ? '#ef4444' : '#f8fafc';
            grantBtn.textContent = 'Enable Microphone Access';
            grantBtn.style.backgroundColor = '#3b82f6';

            if (state === 'denied') {
                errorEl.textContent = 'Permission is currently blocked in your browser settings. Please click the microphone icon with a red X in the address bar to manually allow access.';
            } else {
                errorEl.textContent = '';
            }
        }
    }

    grantBtn.addEventListener('click', async () => {
        const state = (await navigator.permissions.query({ name: 'microphone' })).state;

        if (state === 'granted') {
            try {
                // Triggering a stream forces the "Active Microphone" icon to appear in the address bar (URL)
                // This allows the user to click it and select "Block" or "Manage".
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                statusEl.textContent = 'Settings icon triggered in address bar. Click the 🎙️ icon in the URL to revoke.';
                statusEl.style.color = '#3b82f6';

                // Keep it active for 10 seconds so the icon stays visible, then cleanup
                setTimeout(() => {
                    stream.getTracks().forEach(t => t.stop());
                    checkPermission();
                }, 10000);
            } catch (err) {
                console.error('Ping failed', err);
            }
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(t => t.stop());
            checkPermission();
        } catch (err) {
            console.error('Request failed', err);
            checkPermission();
        }
    });

    checkPermission();
});
