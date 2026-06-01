// Upload Handler

let selectedFile = null;
let selectedFileData = null;

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuth = await checkAuth();
    if (!isAuth) return;
    
    // Load recipients
    await loadRecipients();
    
    // Set up drop zone
    setupDropZone();
    
    // Set up file input
    const fileInput = document.getElementById('fileInput');
    fileInput.addEventListener('change', handleFileSelect);
    
    // Set up clear button
    document.getElementById('clearFile').addEventListener('click', clearFile);
    
    // Set up upload button
    document.getElementById('uploadBtn').addEventListener('click', handleUpload);
    
    // Start notification polling
    startNotificationPolling();
    setupNotificationBell();
});

async function loadRecipients() {
    const select = document.getElementById('recipientSelect');
    
    try {
        const users = await authAPI.getAllUsers();
        
        if (users.success && users.data) {
            select.innerHTML = '<option value="">-- Select a user --</option>';
            users.data.forEach(user => {
                const option = document.createElement('option');
                option.value = user.username;
                option.textContent = `${user.username} (${user.email})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading recipients:', error);
        showToast('Error loading users', 'error');
    }
}

function setupDropZone() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files.length > 0) {
        handleFile(files[0]);
    }
}

async function handleFile(file) {
    selectedFile = file;
    selectedFileData = await readFileAsBase64(file);
    
    // Update UI
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('selectedFile').style.display = 'flex';
    document.getElementById('dropZone').style.display = 'none';
    
    // Enable upload button if folder name and recipient are set
    checkUploadReady();
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const base64 = reader.result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(file);
    });
}

function clearFile() {
    selectedFile = null;
    selectedFileData = null;
    document.getElementById('selectedFile').style.display = 'none';
    document.getElementById('dropZone').style.display = 'block';
    document.getElementById('fileInput').value = '';
    
    checkUploadReady();
}

function checkUploadReady() {
    const folderName = document.getElementById('folderName').value;
    const recipient = document.getElementById('recipientSelect').value;
    const uploadBtn = document.getElementById('uploadBtn');
    
    uploadBtn.disabled = !(selectedFile && folderName && recipient);
}

// Add event listeners for folder name and recipient
document.getElementById('folderName').addEventListener('input', checkUploadReady);
document.getElementById('recipientSelect').addEventListener('change', checkUploadReady);

async function handleUpload() {
    const folderName = document.getElementById('folderName').value;
    const recipient = document.getElementById('recipientSelect').value;
    
    if (!selectedFile || !folderName || !recipient) {
        showToast('Please fill in all fields', 'error');
        return;
    }
    
    const uploadBtn = document.getElementById('uploadBtn');
    const progressContainer = document.getElementById('progressContainer');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    uploadBtn.disabled = true;
    progressContainer.style.display = 'block';
    
    try {
        progressFill.style.width = '50%';
        progressText.textContent = 'Encrypting file...';
        
        // Simulate encryption progress
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        progressFill.style.width = '75%';
        progressText.textContent = 'Uploading to cloud...';
        
        const result = await fileAPI.upload(recipient, folderName, selectedFile.name, selectedFileData);
        
        if (result.success) {
            progressFill.style.width = '100%';
            progressText.textContent = 'Upload complete!';
            
            showToast('File uploaded successfully!');
            
            // Reset form after delay
            setTimeout(() => {
                clearFile();
                document.getElementById('folderName').value = '';
                document.getElementById('recipientSelect').value = '';
                progressContainer.style.display = 'none';
                progressFill.style.width = '0%';
                uploadBtn.disabled = true;
                
                // Show share link if available
                if (result.data.share_link) {
                    showToast(`Share link: ${result.data.share_link}`);
                }
            }, 2000);
        } else {
            throw new Error(result.message);
        }
    } catch (error) {
        showToast(error.message || 'Upload failed', 'error');
        progressContainer.style.display = 'none';
        progressFill.style.width = '0%';
        uploadBtn.disabled = false;
    }
}