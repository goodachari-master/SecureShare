// My Files Handler - Direct Access (No Search Needed)

let receivedFiles = [];
let sentFiles = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuth = await checkAuth();
    if (!isAuth) return;
    
    // Load files
    await loadAllFiles();
    
    // Set up tabs
    setupTabs();
    
    // Set up modal
    setupModal();
    
    // Start notification polling
    startNotificationPolling();
    setupNotificationBell();

    // Poll for new files every 5 seconds
    setInterval(async () => {
        await loadAllFiles();
    }, 5000);
    
    // Check URL param for default tab
    const urlParams = new URLSearchParams(window.location.search);
    const tab = urlParams.get('tab');
    if (tab) {
        const tabBtn = document.querySelector(`.tab-btn[data-tab="${tab}"]`);
        if (tabBtn) tabBtn.click();
    }
});

async function loadAllFiles() {
    try {
        // Load received files
        const receivedResult = await fileAPI.getReceivedFiles();
        if (receivedResult.success) {
            receivedFiles = receivedResult.data;
            updateTabCounts();
        }
        
        // Load sent files
        const sentResult = await fileAPI.getSentFiles();
        if (sentResult.success) {
            sentFiles = sentResult.data;
            updateTabCounts();
        }
        
        // Display initial tab
        displayReceivedFiles();
        
    } catch (error) {
        console.error('Error loading files:', error);
        showToast('Error loading files', 'error');
    }
}

function updateTabCounts() {
    const receivedCount = receivedFiles.length;
    const sentCount = sentFiles.length;
    const unreadCount = receivedFiles.filter(f => !f.is_read).length;
    
    document.getElementById('receivedTabCount').textContent = receivedCount;
    document.getElementById('sentTabCount').textContent = sentCount;
    document.getElementById('unreadTabCount').textContent = unreadCount;
}

function setupTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            document.getElementById(`${tabId}Tab`).classList.add('active');
            
            // Load appropriate files
            if (tabId === 'received') displayReceivedFiles();
            else if (tabId === 'sent') displaySentFiles();
            else if (tabId === 'unread') displayUnreadFiles();
        });
    });
}

function displayReceivedFiles() {
    const container = document.getElementById('receivedFilesList');
    
    if (receivedFiles.length === 0) {
        container.innerHTML = '<div class="loading">No files shared with you yet</div>';
        return;
    }
    
    container.innerHTML = receivedFiles.map(file => createFileCard(file, 'received')).join('');
}

function displaySentFiles() {
    const container = document.getElementById('sentFilesList');
    
    if (sentFiles.length === 0) {
        container.innerHTML = '<div class="loading">No files shared yet</div>';
        return;
    }
    
    container.innerHTML = sentFiles.map(file => createFileCard(file, 'sent')).join('');
}

function displayUnreadFiles() {
    const container = document.getElementById('unreadFilesList');
    const unreadFiles = receivedFiles.filter(f => !f.is_read);
    
    if (unreadFiles.length === 0) {
        container.innerHTML = '<div class="loading">No unread files</div>';
        return;
    }
    
    container.innerHTML = unreadFiles.map(file => createFileCard(file, 'received')).join('');
}

function createFileCard(file, type) {
    if (type === 'received') {
        return `
            <div class="file-card ${file.is_read ? 'read' : 'unread'}">
                <div class="file-icon">${getFileIcon(file.original_filename)}</div>
                <div class="file-info">
                    <h4>${escapeHtml(file.original_filename)}</h4>
                    <p>From: ${escapeHtml(file.sender_username)}</p>
                    <p>Date: ${formatDate(file.uploaded_at)}</p>
                    <p>Size: ${formatFileSize(file.file_size)}</p>
                    ${!file.is_read ? '<span class="unread-badge">New</span>' : ''}
                </div>
                <div class="file-actions">
                    <button onclick="extractFile(${file.file_id})" class="btn-extract">
                        🔓 Extract
                    </button>
                    <button onclick="deleteFile(${file.file_id})" class="btn-delete">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    } else {
        return `
            <div class="file-card">
                <div class="file-icon">${getFileIcon(file.original_filename)}</div>
                <div class="file-info">
                    <h4>${escapeHtml(file.original_filename)}</h4>
                    <p>To: ${escapeHtml(file.recipient_username)}</p>
                    <p>Date: ${formatDate(file.uploaded_at)}</p>
                    <p>Size: ${formatFileSize(file.file_size)}</p>
                    ${file.is_read ? '<span class="read-badge">✓ Read</span>' : '<span class="unread-badge">Unread</span>'}
                </div>
                <div class="file-actions">
                    <button onclick="deleteFile(${file.file_id})" class="btn-delete">
                        🗑️ Delete
                    </button>
                </div>
            </div>
        `;
    }
}

function setupModal() {
    const modal = document.getElementById('extractModal');
    const closeBtn = modal.querySelector('.close');
    const confirmBtn = document.getElementById('confirmExtractBtn');
    
    closeBtn.onclick = () => {
        modal.classList.remove('show');
    };
    
    window.onclick = (e) => {
        if (e.target === modal) {
            modal.classList.remove('show');
        }
    };
    
    confirmBtn.onclick = async () => {
        const fileId = modal.dataset.fileId;
        await performExtract(fileId);
    };
}

window.extractFile = (fileId) => {
    const file = receivedFiles.find(f => f.file_id === fileId);
    if (!file) return;
    
    const modal = document.getElementById('extractModal');
    modal.dataset.fileId = fileId;
    document.getElementById('extractFileName').textContent = file.original_filename;
    modal.classList.add('show');
};

async function performExtract(fileId) {
    const modal = document.getElementById('extractModal');
    const confirmBtn = document.getElementById('confirmExtractBtn');
    const progressFill = document.getElementById('extractProgressFill');
    const statusText = document.getElementById('extractStatus');
    
    confirmBtn.disabled = true;
    progressFill.style.width = '0%';
    statusText.textContent = 'Downloading encrypted file...';
    
    try {
        progressFill.style.width = '30%';
        
        const result = await fileAPI.extractFile(fileId);
        
        if (result.success) {
            progressFill.style.width = '100%';
            statusText.textContent = 'Decryption complete!';
            
            // Decode base64 content
            const binaryContent = atob(result.data.content);
            const bytes = new Uint8Array(binaryContent.length);
            for (let i = 0; i < binaryContent.length; i++) {
                bytes[i] = binaryContent.charCodeAt(i);
            }
            
            // Download file
            downloadFile(bytes, result.data.filename);
            
            showToast('File extracted successfully!');
            
            setTimeout(() => {
                modal.classList.remove('show');
                loadAllFiles(); // Refresh all lists
                if (window.updateNotificationCount) window.updateNotificationCount();
            }, 1500);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showToast(error.message || 'Extraction failed', 'error');
        statusText.textContent = 'Extraction failed';
    } finally {
        confirmBtn.disabled = false;
        setTimeout(() => {
            statusText.textContent = 'Preparing to decrypt...';
            progressFill.style.width = '0%';
        }, 2000);
    }
}

window.deleteFile = async (fileId) => {
    if (!confirm('Are you sure you want to delete this file?')) return;
    
    try {
        const result = await fileAPI.deleteFile(fileId);
        if (result.success) {
            showToast('File deleted successfully');
            await loadAllFiles();
            if (window.updateNotificationCount) window.updateNotificationCount();
        } else {
            showToast(result.message || 'Delete failed', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Delete failed', 'error');
    }
};

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}