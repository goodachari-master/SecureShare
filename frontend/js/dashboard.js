// Dashboard Handler

document.addEventListener('DOMContentLoaded', async () => {
    // Check authentication
    const isAuth = await checkAuth();
    if (!isAuth) return;
    
    // Get current user
    try {
        const user = await authAPI.getCurrentUser();
        if (user.success) {
            document.getElementById('username').textContent = user.data.username;
        }
    } catch (error) {
        console.error('Error loading user:', error);
    }
    
    // Load dashboard data
    await loadStats();
    await loadRecentActivity();
    
    // Poll for updates every 5 seconds
    setInterval(async () => {
        await loadStats();
        await loadRecentActivity();
    }, 5000);
    
    // Start notification polling
    startNotificationPolling();
    
    // Set up notification bell
    setupNotificationBell();
});

async function loadStats() {
    try {
        // Get received files
        const received = await fileAPI.getReceivedFiles();
        const receivedCount = received.data ? received.data.length : 0;
        document.getElementById('receivedCount').textContent = receivedCount;
        
        // Get sent files
        const sent = await fileAPI.getSentFiles();
        const sentCount = sent.data ? sent.data.length : 0;
        document.getElementById('sentCount').textContent = sentCount;
        
        // Count unread
        const unreadCount = received.data ? received.data.filter(f => !f.is_read).length : 0;
        document.getElementById('unreadCount').textContent = unreadCount;
        
        // Get notification count
        const notifCount = await notificationAPI.getUnreadCount();
        document.getElementById('notifStatCount').textContent = notifCount.data?.count || 0;
        
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

async function loadRecentActivity() {
    const activityList = document.getElementById('activityList');
    
    try {
        const received = await fileAPI.getReceivedFiles();
        const sent = await fileAPI.getSentFiles();
        
        const activities = [];
        
        // Add received files
        if (received.data) {
            received.data.slice(0, 5).forEach(file => {
                activities.push({
                    type: 'received',
                    filename: file.original_filename,
                    user: file.sender_username,
                    date: file.uploaded_at,
                    is_read: file.is_read
                });
            });
        }
        
        // Add sent files
        if (sent.data) {
            sent.data.slice(0, 5).forEach(file => {
                activities.push({
                    type: 'sent',
                    filename: file.original_filename,
                    user: file.recipient_username,
                    date: file.uploaded_at,
                    is_read: file.is_read
                });
            });
        }
        
        // Sort by date
        activities.sort((a, b) => new Date(b.date) - new Date(a.date));
        
        if (activities.length === 0) {
            activityList.innerHTML = '<div class="activity-empty">No recent activity</div>';
            return;
        }
        
        activityList.innerHTML = activities.slice(0, 10).map(activity => `
            <div class="activity-item">
                <div class="activity-icon">${activity.type === 'received' ? '📥' : '📤'}</div>
                <div class="activity-details">
                    <p><strong>${activity.filename}</strong> ${activity.type === 'received' ? 'shared by' : 'sent to'} ${activity.user}</p>
                    <span class="activity-time">${formatDate(activity.date)}</span>
                    ${!activity.is_read && activity.type === 'received' ? '<span class="unread-badge">New</span>' : ''}
                </div>
            </div>
        `).join('');
        
    } catch (error) {
        console.error('Error loading activity:', error);
        activityList.innerHTML = '<div class="activity-empty">Error loading activity</div>';
    }
}

// Add activity styles if not present
const style = document.createElement('style');
style.textContent = `
    .activity-list {
        background: var(--bg-card);
        border-radius: 1rem;
        overflow: hidden;
        margin-top: 1rem;
    }
    
    .activity-item {
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem;
        border-bottom: 1px solid var(--border);
        transition: background 0.3s ease;
    }
    
    .activity-item:hover {
        background: var(--bg-hover);
    }
    
    .activity-icon {
        font-size: 1.5rem;
    }
    
    .activity-details {
        flex: 1;
    }
    
    .activity-details p {
        margin-bottom: 0.25rem;
    }
    
    .activity-time {
        font-size: 0.75rem;
        color: var(--text-secondary);
    }
    
    .activity-empty {
        text-align: center;
        padding: 2rem;
        color: var(--text-secondary);
    }
`;
document.head.appendChild(style);