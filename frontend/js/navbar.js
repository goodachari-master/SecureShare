// Navbar and Common UI Handler

document.addEventListener('DOMContentLoaded', async () => {
    // Populate username in navbar
    const navUsername = document.getElementById('navUsername');
    if (navUsername) {
        try {
            const user = await authAPI.getCurrentUser();
            if (user.success) {
                navUsername.textContent = user.data.username;
            } else {
                navUsername.textContent = 'Guest';
            }
        } catch (error) {
            console.error('Error fetching user for navbar:', error);
            navUsername.textContent = 'User';
        }
    }

    // Logout button handler
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            
            try {
                // Call logout API
                const result = await authAPI.logout();
                
                if (result.success) {
                    // Clear local storage
                    localStorage.removeItem('sessionId');
                    // Redirect to login page
                    window.location.href = '/index.html';
                } else {
                    showToast(result.message || 'Logout failed', 'error');
                }
            } catch (error) {
                console.error('Logout error:', error);
                // Even if API fails, clear local session and redirect
                localStorage.removeItem('sessionId');
                window.location.href = '/index.html';
            }
        });
    }

    // Active link highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-links a');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
});
