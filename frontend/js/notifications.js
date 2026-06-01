// Notification Handler

let notificationPollingInterval = null;
let isPolling = false;

async function startNotificationPolling() {
    // Poll every 5 seconds (safer for resource management)
    if (notificationPollingInterval) clearInterval(notificationPollingInterval);
    
    // Initial load
    await refreshNotifications();
    
    notificationPollingInterval = setInterval(async () => {
        await refreshNotifications();
    }, 5000);
}

async function refreshNotifications() {
    // Prevent overlapping requests if one is still pending
    if (isPolling) return;
    isPolling = true;

    try {
        const result = await notificationAPI.getSummary();
        
        if (result.success && result.data) {
            const { count, notifications } = result.data;
            
            // 1. Update Badge Count
            const notifCountElements = document.querySelectorAll('#notifCount');
            notifCountElements.forEach(el => {
                el.textContent = count;
                el.style.display = count > 0 ? 'inline-block' : 'none';
            });

            // Update dashboard stat if present
            const statCount = document.getElementById('notifStatCount');
            if (statCount) statCount.textContent = count;

            // 2. Display Notifications list
            displayNotifications(notifications);
        }
    } catch (error) {
        console.error('Error refreshing notifications:', error);
    } finally {
        isPolling = false;
    }
}

// Backward compatibility or manual triggers
async function updateNotificationCount() {
    await refreshNotifications();
}

async function loadNotifications() {
    await refreshNotifications();
}

function displayNotifications(notifications) {
    const notificationList = document.getElementById('notificationList');
    
    if (!notificationList) return;
    
    if (notifications.length === 0) {
        notificationList.innerHTML = '<div class="notification-empty">No notifications</div>';
        return;
    }
    
    notificationList.innerHTML = notifications.map(notif => `
        <div class="notification-item ${!notif.is_read ? 'unread' : ''}" data-id="${notif.notification_id}">
            <div class="notification-title">${escapeHtml(notif.title)}</div>
            <div class="notification-message">${escapeHtml(notif.message)}</div>
            <div class="notification-time">${formatDate(notif.created_at)}</div>
        </div>
    `).join('');
    
    // Add click handlers
    document.querySelectorAll('.notification-item').forEach(item => {
        item.addEventListener('click', async () => {
            const id = item.dataset.id;
            if (id) {
                await notificationAPI.markRead(id);
                item.classList.remove('unread');
                // Refresh count immediately
                await updateNotificationCount();
                await loadNotifications();
            }
            
            // Close dropdown
            document.getElementById('notificationDropdown').classList.remove('show');
            
            // Redirect based on notification type
            // Could redirect to relevant file
        });
    });
}

function setupNotificationBell() {
    const bell = document.getElementById('notificationBell');
    const dropdown = document.getElementById('notificationDropdown');
    const markAllRead = document.getElementById('markAllRead');
    
    if (!bell) return;
    
    bell.addEventListener('click', (e) => {
        e.stopPropagation();
        dropdown.classList.toggle('show');
        if (dropdown.classList.contains('show')) {
            loadNotifications();
        }
    });
    
    if (markAllRead) {
        markAllRead.addEventListener('click', async () => {
            await notificationAPI.markRead();
            // We still update the count, but it won't change unless files were extracted/deleted
            await updateNotificationCount();
            await loadNotifications();
            showToast('Notification list cleared');
        });
    }
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!bell.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.classList.remove('show');
        }
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Add styles for notifications
const notifStyle = document.createElement('style');
notifStyle.textContent = `
    .notification-empty {
        text-align: center;
        padding: 2rem;
        color: var(--text-secondary);
    }
    
    .read-badge {
        display: inline-block;
        background: var(--teal-medium);
        color: white;
        font-size: 0.7rem;
        padding: 0.2rem 0.5rem;
        border-radius: 1rem;
        margin-top: 0.5rem;
    }
`;
document.head.appendChild(notifStyle);