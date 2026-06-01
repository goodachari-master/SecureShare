// Google Drive Browser - Full Screen File Manager

let currentFolderId = 'root';
let folderStack = [];
let currentFiles = [];
let selectedFiles = new Set();

document.addEventListener('DOMContentLoaded', () => {
    setupDriveBrowser();
});

function setupDriveBrowser() {
    const driveBtn = document.getElementById('driveBrowserBtn');
    const driveModal = document.getElementById('driveModal');
    const closeBtn = document.getElementById('closeDriveModal');
    const refreshBtn = document.getElementById('refreshDriveBtn');
    const uploadBtn = document.getElementById('uploadToDriveBtn');
    const searchBtn = document.getElementById('searchDriveBtn');
    const searchInput = document.getElementById('driveSearch');
    
    if (!driveBtn) return;
    
    // Open modal
    driveBtn.addEventListener('click', () => {
        driveModal.classList.add('show');
        // Reset state
        currentFolderId = 'root';
        folderStack = [];
        updateBreadcrumb('root', 'My Drive');
        loadDriveContents('root');
        loadStorageInfo();
    });
    
    // Close modal
    closeBtn.addEventListener('click', () => {
        driveModal.classList.remove('show');
        selectedFiles.clear();
    });
    
    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && driveModal.classList.contains('show')) {
            driveModal.classList.remove('show');
        }
    });
    
    // Refresh
    refreshBtn.addEventListener('click', () => {
        loadDriveContents(currentFolderId);
        loadStorageInfo();
    });
    
    // Upload file
    uploadBtn.addEventListener('click', () => {
        uploadToDrive();
    });
    
    // Search
    searchBtn.addEventListener('click', () => {
        const query = searchInput.value.trim();
        if (query) {
            searchDrive(query);
        } else {
            loadDriveContents(currentFolderId);
        }
    });
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                searchDrive(query);
            } else {
                loadDriveContents(currentFolderId);
            }
        }
    });
}

async function loadDriveContents(folderId, folderName = null) {
    const driveContent = document.getElementById('driveContent');
    driveContent.innerHTML = '<div class="drive-loading">📂 Loading files...</div>';
    
    // Clear selection when navigating folders
    selectedFiles.clear();
    showBulkActions();
    
    try {
        const response = await fetch('/api/drive/list', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Session-ID': localStorage.getItem('sessionId') || ''
            },
            body: JSON.stringify({ folder_id: folderId })
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentFiles = result.data.files;
            currentFolderId = folderId;
            
            // Update breadcrumb
            if (folderName) {
                updateBreadcrumb(folderId, folderName);
            }
            
            displayDriveContents(currentFiles);
        } else {
            driveContent.innerHTML = `<div class="drive-empty">❌ ${result.message}</div>`;
        }
    } catch (error) {
        console.error('Error loading drive:', error);
        driveContent.innerHTML = '<div class="drive-empty">❌ Error loading files</div>';
    }
}

function displayDriveContents(files) {
    const driveContent = document.getElementById('driveContent');
    
    if (!files || files.length === 0) {
        driveContent.innerHTML = '<div class="drive-empty">📭 This folder is empty</div>';
        return;
    }
    
    // Separate folders and files
    const folders = files.filter(f => f.mimeType === 'application/vnd.google-apps.folder');
    const regularFiles = files.filter(f => f.mimeType !== 'application/vnd.google-apps.folder');
    
    const allItems = [...folders, ...regularFiles];
    
    driveContent.innerHTML = `
        <div class="drive-grid">
            ${allItems.map(item => `
                <div class="drive-item ${selectedFiles.has(item.id) ? 'selected' : ''}" data-id="${item.id}" data-mime="${item.mimeType}">
                    <input type="checkbox" class="drive-select-checkbox" data-id="${item.id}" ${selectedFiles.has(item.id) ? 'checked' : ''}>
                    <div class="drive-item-icon">${getDriveIcon(item)}</div>
                    <div class="drive-item-info">
                        <div class="drive-item-name">${escapeHtml(item.name)}</div>
                        <div class="drive-item-meta">
                            ${item.mimeType === 'application/vnd.google-apps.folder' ? '📁 Folder' : formatFileSize(item.size)}
                            <br>${formatDate(item.modifiedTime)}
                        </div>
                    </div>
                    <div class="drive-item-actions">
                        ${item.mimeType === 'application/vnd.google-apps.folder' ? 
                            '<button class="drive-open-btn" title="Open">📂</button>' : 
                            '<button class="drive-download-btn" title="Download">💾</button>'}
                        <button class="drive-info-btn" title="Details">ℹ️</button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    
    // Add event listeners
    document.querySelectorAll('.drive-item').forEach(item => {
        const fileId = item.dataset.id;
        const isFolder = item.dataset.mime === 'application/vnd.google-apps.folder';
        
        // Checkbox selection
        const checkbox = item.querySelector('.drive-select-checkbox');
        checkbox.addEventListener('change', (e) => {
            e.stopPropagation();
            if (checkbox.checked) {
                selectedFiles.add(fileId);
                item.classList.add('selected');
            } else {
                selectedFiles.delete(fileId);
                item.classList.remove('selected');
            }
            showBulkActions();
        });
        
        // Open folder or download file
        const mainClick = () => {
            if (isFolder) {
                openFolder(fileId, item.querySelector('.drive-item-name').textContent);
            } else {
                downloadFromDrive(fileId, item.querySelector('.drive-item-name').textContent);
            }
        };
        
        item.addEventListener('click', (e) => {
            if (e.target !== checkbox && !e.target.classList.contains('drive-download-btn') && !e.target.classList.contains('drive-open-btn')) {
                mainClick();
            }
        });
        
        // Open button
        const openBtn = item.querySelector('.drive-open-btn');
        if (openBtn) {
            openBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                openFolder(fileId, item.querySelector('.drive-item-name').textContent);
            });
        }
        
        // Download button
        const downloadBtn = item.querySelector('.drive-download-btn');
        if (downloadBtn) {
            downloadBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                downloadFromDrive(fileId, item.querySelector('.drive-item-name').textContent);
            });
        }
        
        // Info button
        const infoBtn = item.querySelector('.drive-info-btn');
        if (infoBtn) {
            infoBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                showFileInfo(item);
            });
        }
    });
}

function getDriveIcon(item) {
    if (item.mimeType === 'application/vnd.google-apps.folder') {
        return '📁';
    }
    
    const ext = item.name.split('.').pop().toLowerCase();
    const icons = {
        pdf: '📄', doc: '📝', docx: '📝', txt: '📃',
        jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️',
        mp3: '🎵', mp4: '🎬', zip: '📦', rar: '📦',
        exe: '⚙️', js: '📜', py: '🐍', html: '🌐'
    };
    return icons[ext] || '📎';
}

async function openFolder(folderId, folderName) {
    // Don't add to stack if we are in root and opening something else
    // or if we are already in this folder
    if (currentFolderId !== folderId) {
        folderStack.push({ id: currentFolderId, name: getCurrentFolderName() });
    }
    await loadDriveContents(folderId, folderName);
}

function getCurrentFolderName() {
    const breadcrumb = document.getElementById('driveBreadcrumb');
    const activeItem = breadcrumb.querySelector('.breadcrumb-item.active');
    return activeItem ? activeItem.textContent : 'My Drive';
}

function updateBreadcrumb(folderId, folderName) {
    const breadcrumb = document.getElementById('driveBreadcrumb');
    
    // Start with My Drive as the base
    let html = `<span class="breadcrumb-item ${folderId === 'root' ? 'active' : ''}" data-folder-id="root">My Drive</span>`;
    
    // Only show stack items that aren't the root
    folderStack.forEach((folder, index) => {
        if (folder.id !== 'root') {
            html += `<span class="breadcrumb-separator">›</span>`;
            html += `<span class="breadcrumb-item" data-folder-id="${folder.id}">${escapeHtml(folder.name)}</span>`;
        }
    });
    
    // Add current folder if it's not the root
    if (folderId !== 'root') {
        html += `<span class="breadcrumb-separator">›</span>`;
        html += `<span class="breadcrumb-item active" data-folder-id="${folderId}">${escapeHtml(folderName)}</span>`;
    }
    
    breadcrumb.innerHTML = html;
    
    // Add click handlers
    document.querySelectorAll('.breadcrumb-item').forEach(item => {
        item.addEventListener('click', async () => {
            const id = item.dataset.folderId;
            const name = item.textContent;
            
            // Remove all items after this one from stack
            const index = folderStack.findIndex(f => f.id === id);
            if (index !== -1) {
                folderStack = folderStack.slice(0, index);
            }
            
            await loadDriveContents(id, name);
        });
    });
}

async function downloadFromDrive(fileId, fileName) {
    utils.showToast(`Downloading ${fileName}...`);
    
    try {
        const response = await fetch('/api/drive/download', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Session-ID': localStorage.getItem('sessionId') || ''
            },
            body: JSON.stringify({ file_id: fileId, file_name: fileName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Decode base64 content
            const binaryContent = atob(result.data.content);
            const bytes = new Uint8Array(binaryContent.length);
            for (let i = 0; i < binaryContent.length; i++) {
                bytes[i] = binaryContent.charCodeAt(i);
            }
            
            // Download using the utility function if available, otherwise fallback
            if (window.utils && window.utils.downloadFile) {
                window.utils.downloadFile(bytes, fileName);
            } else {
                const blob = new Blob([bytes]);
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = fileName;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }
            
            utils.showToast(`✅ Downloaded: ${fileName}`);
        } else {
            utils.showToast(`❌ Download failed: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Download error:', error);
        utils.showToast('❌ Download failed', 'error');
    }
}

async function uploadToDrive() {
    const input = document.createElement('input');
    input.type = 'file';
    input.multiple = true;
    
    input.onchange = async (e) => {
        const files = Array.from(e.target.files);
        
        for (const file of files) {
            utils.showToast(`Uploading ${file.name}...`);
            
            const reader = new FileReader();
            reader.onload = async (event) => {
                const base64Content = event.target.result.split(',')[1];
                
                try {
                    const response = await fetch('/api/drive/upload', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'X-Session-ID': localStorage.getItem('sessionId') || ''
                        },
                        body: JSON.stringify({
                            file_name: file.name,
                            file_content: base64Content,
                            parent_id: currentFolderId
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        utils.showToast(`✅ Uploaded: ${file.name}`);
                        loadDriveContents(currentFolderId);
                        loadStorageInfo();
                    } else {
                        utils.showToast(`❌ Upload failed: ${result.message}`, 'error');
                    }
                } catch (error) {
                    utils.showToast(`❌ Upload failed`, 'error');
                }
            };
            reader.readAsDataURL(file);
        }
    };
    
    input.click();
}

async function searchDrive(query) {
    const driveContent = document.getElementById('driveContent');
    driveContent.innerHTML = '<div class="drive-loading">🔍 Searching...</div>';
    
    try {
        const response = await fetch('/api/drive/search', {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Session-ID': localStorage.getItem('sessionId') || ''
            },
            body: JSON.stringify({ query })
        });
        
        const result = await response.json();
        
        if (result.success) {
            displayDriveContents(result.data.files);
        } else {
            driveContent.innerHTML = `<div class="drive-empty">❌ ${result.message}</div>`;
        }
    } catch (error) {
        console.error('Search error:', error);
        driveContent.innerHTML = '<div class="drive-empty">❌ Search failed</div>';
    }
}

async function loadStorageInfo() {
    try {
        const response = await fetch('/api/drive/storage', {
            headers: { 
                'X-Session-ID': localStorage.getItem('sessionId') || ''
            }
        });
        const result = await response.json();
        
        if (result.success) {
            const stats = result.data;
            const usedGB = (stats.used / (1024 * 1024 * 1024)).toFixed(2);
            const totalGB = (stats.total / (1024 * 1024 * 1024)).toFixed(2);
            const percent = (stats.used / stats.total * 100).toFixed(1);
            
            document.getElementById('driveStats').innerHTML = `
                💾 Storage: ${usedGB} GB of ${totalGB} GB used (${percent}%)
                | 📁 Folders: ${stats.folderCount} | 📄 Files: ${stats.fileCount}
            `;
        }
    } catch (error) {
        console.error('Storage info error:', error);
    }
}

function showBulkActions() {
    const selectedCount = selectedFiles.size;
    const existingBar = document.querySelector('.drive-bulk-actions');
    
    if (selectedCount > 0) {
        if (existingBar) existingBar.remove();
        
        const bar = document.createElement('div');
        bar.className = 'drive-bulk-actions';
        bar.innerHTML = `
            <span>${selectedCount} item(s) selected</span>
            <button id="bulkDownloadBtn">💾 Download Selected</button>
            <button id="bulkClearBtn">✖ Clear</button>
        `;
        document.body.appendChild(bar);
        
        document.getElementById('bulkDownloadBtn').onclick = async () => {
            for (const fileId of selectedFiles) {
                const file = currentFiles.find(f => f.id === fileId);
                if (file && file.mimeType !== 'application/vnd.google-apps.folder') {
                    await downloadFromDrive(fileId, file.name);
                    await new Promise(resolve => setTimeout(resolve, 500));
                }
            }
        };
        
        document.getElementById('bulkClearBtn').onclick = () => {
            selectedFiles.clear();
            bar.remove();
            loadDriveContents(currentFolderId);
        };
    } else {
        if (existingBar) existingBar.remove();
    }
}

function showFileInfo(item) {
    const name = item.querySelector('.drive-item-name').textContent;
    const meta = item.querySelector('.drive-item-meta').textContent;
    alert(`📄 File: ${name}\n\n${meta}`);
}

function formatFileSize(bytes) {
    if (!bytes) return 'Unknown size';
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return parseFloat((bytes / Math.pow(1024, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}