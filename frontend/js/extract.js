// Extract Handler

let currentFiles = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuth = await checkAuth();
    if (!isAuth) return;
    
    // Load files
    await loadFiles();
    
    // Set up filter buttons
    setupFilters();
    
    // Set up modal
    setupModal();
    
    // Start notification polling
    startNotificationPolling();
    setupNotificationBell();
});

async function loadFiles() {
    const filesList = document.getElementById('filesList');
    filesList.innerHTML = '<div class="loading">Loading files...</div>';
    
    try {
        const result = await fileAPI.getReceivedFiles();
        
        if (result.success && result.data) {
            currentFiles = result.data;
            displayFiles(currentFiles);
        } else {
            filesList.innerHTML = '<div class="loading">No files shared with you</div>';
        }
    } catch (error) {
        console.error('Error loading files:', error);
        filesList.innerHTML = '<div class="loading">Error loading files</div>';
    }
}

function displayFiles(files) {
    const filesList = document.getElementById('filesList');
    
    if (files.length === 0) {
        filesList.innerHTML = '<div class="loading">No files to display</div>';
        return;
    }
    
    filesList.innerHTML = files.map(file => `
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
    `).join('');
}

function setupFilters() {
    const filters = document.querySelectorAll('.filter-btn');
    
    filters.forEach(filter => {
        filter.addEventListener('click', () => {
            filters.forEach(f => f.classList.remove('active'));
            filter.classList.add('active');
            
            const filterValue = filter.dataset.filter;
            
            if (filterValue === 'all') {
                displayFiles(currentFiles);
            } else if (filterValue === 'unread') {
                displayFiles(currentFiles.filter(f => !f.is_read));
            } else if (filterValue === 'read') {
                displayFiles(currentFiles.filter(f => f.is_read));
            }
        });
    });
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
    const file = currentFiles.find(f => f.file_id === fileId);
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
                loadFiles(); // Refresh list
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
            await loadFiles();
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