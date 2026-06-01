// Recipients Handler - View all users

let allUsers = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuth = await checkAuth();
    if (!isAuth) return;
    
    // Load users
    await loadUsers();
    
    // Set up search
    setupSearch();
    
    // Start notification polling
    startNotificationPolling();
    setupNotificationBell();
});

async function loadUsers() {
    const usersGrid = document.getElementById('usersList');
    usersGrid.innerHTML = '<div class="loading">Loading users...</div>';
    
    try {
        const result = await authAPI.getAllUsers();
        
        if (result.success && result.data) {
            allUsers = result.data;
            displayUsers(allUsers);
        } else {
            usersGrid.innerHTML = '<div class="loading">No users found</div>';
        }
    } catch (error) {
        console.error('Error loading users:', error);
        usersGrid.innerHTML = '<div class="loading">Error loading users</div>';
    }
}

function displayUsers(users) {
    const usersGrid = document.getElementById('usersList');
    
    if (users.length === 0) {
        usersGrid.innerHTML = '<div class="loading">No users found</div>';
        return;
    }
    
    usersGrid.innerHTML = users.map(user => `
        <div class="user-card" onclick="shareWithUser('${user.username}')">
            <div class="user-avatar">
                ${user.username.charAt(0).toUpperCase()}
            </div>
            <div class="user-info">
                <h4>${escapeHtml(user.username)}</h4>
                <p>${escapeHtml(user.email)}</p>
            </div>
        </div>
    `).join('');
}

function setupSearch() {
    const searchInput = document.getElementById('searchUsers');
    
    if (!searchInput) return;
    
    searchInput.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const filtered = allUsers.filter(user => 
            user.username.toLowerCase().includes(searchTerm) ||
            user.email.toLowerCase().includes(searchTerm)
        );
        displayUsers(filtered);
    });
}

window.shareWithUser = (username) => {
    // Redirect to upload page with recipient pre-selected
    window.location.href = `/upload.html?recipient=${encodeURIComponent(username)}`;
};

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}