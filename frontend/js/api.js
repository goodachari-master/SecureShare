// API Configuration
const API_BASE = '/api';

// API Request Helper
async function apiRequest(endpoint, options = {}) {
    const sessionId = localStorage.getItem('sessionId');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers
    };

    if (sessionId) {
        headers['X-Session-ID'] = sessionId;
    }

    const config = {
        headers,
        ...options
    };
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Auth APIs
const authAPI = {
    register: (username, email, password) => 
        apiRequest('/register', { method: 'POST', body: JSON.stringify({ username, email, password }) }),
    
    login: (username, password) => 
        apiRequest('/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
    
    logout: () => 
        apiRequest('/logout', { method: 'POST' }),
    
    getCurrentUser: () => 
        apiRequest('/me'),
    
    getAllUsers: () => 
        apiRequest('/users')
};

// File APIs
const fileAPI = {
    upload: (recipient, folderName, filename, fileContent) =>
        apiRequest('/upload', { method: 'POST', body: JSON.stringify({ recipient, folder_name: folderName, filename, file_content: fileContent }) }),
    
    getReceivedFiles: () =>
        apiRequest('/files/received'),
    
    getSentFiles: () =>
        apiRequest('/files/sent'),
    
    extractFile: (fileId) =>
        apiRequest('/extract', { method: 'POST', body: JSON.stringify({ file_id: fileId }) }),

    deleteFile: (fileId) =>
        apiRequest('/files/delete', { method: 'POST', body: JSON.stringify({ file_id: fileId }) })
};

// Notification APIs
const notificationAPI = {
    getNotifications: () =>
        apiRequest('/notifications'),
    
    getUnreadCount: () =>
        apiRequest('/notifications/unread/count'),

    getSummary: () =>
        apiRequest('/notifications/summary'),
    
    markRead: (notificationId = null) =>
        apiRequest('/notifications/mark-read', { method: 'POST', body: JSON.stringify({ notification_id: notificationId }) })
};

// Key APIs
const keyAPI = {
    getPublicKey: () =>
        apiRequest('/keys/public'),
    
    getFingerprint: () =>
        apiRequest('/keys/fingerprint'),
    
    getPrivateKey: (password) =>
        apiRequest('/keys/private', { method: 'POST', body: JSON.stringify({ password }) })
};

// Utility Functions
// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    if (!toast) return;
    
    // Truncate extremely long messages to prevent UI popping
    const displayMessage = message.length > 300 ? message.substring(0, 300) + '...' : message;
    
    toast.textContent = displayMessage;
    toast.style.borderLeftColor = type === 'error' ? '#E87A7A' : '#2E9E9E';
    toast.className = `toast show ${type}`;
    
    setTimeout(() => {
        toast.className = toast.className.replace('show', '');
    }, 3000);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)} minutes ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)} hours ago`;
    return date.toLocaleDateString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        pdf: '📄', doc: '📝', docx: '📝', txt: '📃',
        jpg: '🖼️', jpeg: '🖼️', png: '🖼️', gif: '🖼️',
        mp3: '🎵', mp4: '🎬', zip: '📦', rar: '📦',
        exe: '⚙️', js: '📜', py: '🐍', html: '🌐'
    };
    return icons[ext] || '📁';
}

function downloadFile(content, filename, type = 'application/octet-stream') {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Check authentication on page load
async function checkAuth() {
    try {
        const user = await authAPI.getCurrentUser();
        if (!user.success && !window.location.pathname.includes('index.html')) {
            window.location.href = '/index.html';
        }
        return user.success;
    } catch (error) {
        if (!window.location.pathname.includes('index.html')) {
            window.location.href = '/index.html';
        }
        return false;
    }
}

// Export for use in other files
window.api = { authAPI, fileAPI, notificationAPI, keyAPI };
window.utils = { showToast, formatDate, formatFileSize, getFileIcon, downloadFile, checkAuth };