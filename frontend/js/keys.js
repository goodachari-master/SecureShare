// Key Management Handler

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuth = await checkAuth();
    if (!isAuth) return;
    
    // Load public key
    await loadPublicKey();
    
    // Load fingerprint
    await loadFingerprint();
    
    // Set up buttons
    setupButtons();
    
    // Start notification polling
    startNotificationPolling();
    setupNotificationBell();
});

async function loadPublicKey() {
    try {
        const result = await keyAPI.getPublicKey();
        
        if (result.success && result.data) {
            const publicKey = result.data.public_key;
            const preview = document.getElementById('publicKeyPreview');
            
            // Show truncated preview
            const lines = publicKey.split('\n');
            const shortKey = lines.slice(0, 2).join('\n') + '\n...\n' + lines.slice(-2).join('\n');
            preview.innerHTML = `<pre>${escapeHtml(shortKey)}</pre>`;
            
            // Store full key for copying
            window.publicKeyFull = publicKey;
        }
    } catch (error) {
        console.error('Error loading public key:', error);
        document.getElementById('publicKeyPreview').innerHTML = '<pre>Error loading key</pre>';
    }
}

async function loadFingerprint() {
    try {
        const result = await keyAPI.getFingerprint();
        
        if (result.success && result.data) {
            document.getElementById('fingerprint').textContent = result.data.fingerprint;
        }
    } catch (error) {
        console.error('Error loading fingerprint:', error);
        document.getElementById('fingerprint').textContent = 'Error';
    }
}

function setupButtons() {
    // Copy public key
    document.getElementById('copyPublicKey').addEventListener('click', () => {
        if (window.publicKeyFull) {
            navigator.clipboard.writeText(window.publicKeyFull);
            showToast('Public key copied to clipboard');
        }
    });
    
    // Download public key
    document.getElementById('downloadPublicKey').addEventListener('click', () => {
        if (window.publicKeyFull) {
            const blob = new Blob([window.publicKeyFull], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'public_key.pem';
            a.click();
            URL.revokeObjectURL(url);
            showToast('Public key downloaded');
        }
    });
    
    // View private key
    document.getElementById('viewPrivateKey').addEventListener('click', () => {
        document.getElementById('passwordModal').classList.add('show');
        document.getElementById('privateKeyPassword').value = '';
        document.getElementById('privateKeyPassword').focus();
        window.keyAction = 'view';
    });
    
    // Download private key
    document.getElementById('downloadPrivateKey').addEventListener('click', () => {
        document.getElementById('passwordModal').classList.add('show');
        document.getElementById('privateKeyPassword').value = '';
        document.getElementById('privateKeyPassword').focus();
        window.keyAction = 'download';
    });
    
    // Confirm password button
    document.getElementById('confirmPasswordBtn').addEventListener('click', async () => {
        const password = document.getElementById('privateKeyPassword').value;
        if (!password) {
            showToast('Password is required', 'error');
            return;
        }
        
        try {
            const result = await keyAPI.getPrivateKey(password);
            if (result.success && result.data) {
                const privateKey = result.data.private_key;
                window.privateKeyFull = privateKey;
                
                document.getElementById('passwordModal').classList.remove('show');
                
                if (window.keyAction === 'view') {
                    document.getElementById('privateKeyContent').textContent = privateKey;
                    document.getElementById('privateKeyModal').classList.add('show');
                } else if (window.keyAction === 'download') {
                    downloadFile(privateKey, 'private_key.pem');
                    showToast('Private key downloaded successfully');
                }
            } else {
                showToast(result.message || 'Verification failed', 'error');
            }
        } catch (error) {
            console.error('Key error:', error);
            showToast('Verification failed. Please check your password.', 'error');
        }
    });
    
    // Copy private key
    document.getElementById('copyPrivateKey').addEventListener('click', () => {
        if (window.privateKeyFull) {
            navigator.clipboard.writeText(window.privateKeyFull);
            showToast('Private key copied to clipboard');
        }
    });
    
    // Download private key action from modal
    document.getElementById('downloadPrivateKeyAction').addEventListener('click', () => {
        if (window.privateKeyFull) {
            downloadFile(window.privateKeyFull, 'private_key.pem');
            showToast('Private key downloaded successfully');
        }
    });
    
    // Setup modal close
    document.getElementById('closePasswordModal').onclick = () => document.getElementById('passwordModal').classList.remove('show');
    document.getElementById('closePrivateKeyModal').onclick = () => document.getElementById('privateKeyModal').classList.remove('show');
    
    // Also close on window click
    window.onclick = (event) => {
        const passModal = document.getElementById('passwordModal');
        const keyModal = document.getElementById('privateKeyModal');
        if (event.target == passModal) passModal.classList.remove('show');
        if (event.target == keyModal) keyModal.classList.remove('show');
    };
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}