// Authentication Handler

document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const tabs = document.querySelectorAll('.auth-tab');
    const forms = document.querySelectorAll('.auth-form');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabId = tab.dataset.tab;
            
            tabs.forEach(t => t.classList.remove('active'));
            forms.forEach(f => f.classList.remove('active'));
            
            tab.classList.add('active');
            document.getElementById(`${tabId}Form`).classList.add('active');
        });
    });
    
    // Login form
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('loginUsername').value;
            const password = document.getElementById('loginPassword').value;
            
            if (!username || !password) {
                showToast('Please fill in all fields', 'error');
                return;
            }
            
            const submitBtn = loginForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Logging in...';
            
            try {
                const result = await authAPI.login(username, password);
                
                if (result.success) {
                    // Store session ID if provided
                    if (result.data.session_id) {
                        localStorage.setItem('sessionId', result.data.session_id);
                    }
                    
                    showToast('Login successful! Redirecting...');
                    setTimeout(() => {
                        window.location.href = '/dashboard.html';
                    }, 1000);
                } else {
                    showToast(result.message || 'Login failed', 'error');
                    submitBtn.disabled = false;
                    submitBtn.textContent = 'Login →';
                }
            } catch (error) {
                showToast(error.message || 'Login failed', 'error');
                submitBtn.disabled = false;
                submitBtn.textContent = 'Login →';
            }
        });
    }
    
    // Register form
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const username = document.getElementById('regUsername').value;
            const email = document.getElementById('regEmail').value;
            const password = document.getElementById('regPassword').value;
            const confirmPassword = document.getElementById('regConfirmPassword').value;
            
            if (!username || !email || !password) {
                showToast('Please fill in all fields', 'error');
                return;
            }
            
            if (password !== confirmPassword) {
                showToast('Passwords do not match', 'error');
                return;
            }
            
            if (password.length < 6) {
                showToast('Password must be at least 6 characters', 'error');
                return;
            }
            
            const submitBtn = registerForm.querySelector('button[type="submit"]');
            submitBtn.disabled = true;
            submitBtn.textContent = 'Registering...';
            
            try {
                const result = await authAPI.register(username, email, password);
                
                if (result.success) {
                    showToast('Registration successful! Please login.');
                    
                    // Switch to login tab
                    document.querySelector('.auth-tab[data-tab="login"]').click();
                    
                    // Clear form
                    registerForm.reset();
                } else {
                    showToast(result.message || 'Registration failed', 'error');
                }
            } catch (error) {
                showToast(error.message || 'Registration failed', 'error');
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Register →';
            }
        });
    }
    
    // Check auth on protected pages
    if (!window.location.pathname.includes('index.html')) {
        checkAuth();
    }
});