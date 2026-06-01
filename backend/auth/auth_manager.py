import bcrypt
from datetime import datetime, timedelta
import secrets
from encryption.key_manager import KeyManager
from database.db_manager import DatabaseManager

class AuthManager:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def register_user(self, username, email, password):
        # Check if user exists
        existing = self.db.fetch_one(
            "SELECT user_id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        if existing:
            return False, "Username or email already exists"
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        
        # Generate RSA key pair
        private_key_pem, public_key_pem = KeyManager.generate_rsa_keypair()
        
        # Encrypt private key with password
        encrypted_private = KeyManager.encrypt_private_key_with_password(private_key_pem, password)
        
        # Insert user
        user_id = self.db.insert('users', {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'public_key': public_key_pem,
            'private_key_encrypted': encrypted_private['ciphertext'],
            'private_key_iv': encrypted_private['iv'],
            'private_key_tag': encrypted_private['tag'],
            'private_key_salt': encrypted_private['salt']
        })
        
        return True, {"user_id": user_id, "username": username}
    
    def login_user(self, username, password, ip_address=None, user_agent=None):
        # Get user
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )
        if not user:
            return False, "Invalid credentials"
        
        # Verify password
        if not bcrypt.checkpw(password.encode(), user['password_hash'].encode()):
            return False, "Invalid credentials"
        
        # Decrypt private key
        encrypted_data = {
            'salt': user['private_key_salt'],
            'iv': user['private_key_iv'],
            'tag': user['private_key_tag'],
            'ciphertext': user['private_key_encrypted']
        }
        
        try:
            private_key = KeyManager.decrypt_private_key_with_password(encrypted_data, password)
        except:
            return False, "Failed to decrypt private key"
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        auth_token = secrets.token_urlsafe(64)
        expires_at = datetime.now() + timedelta(hours=24)
        
        self.db.insert('user_sessions', {
            'session_id': session_id,
            'user_id': user['user_id'],
            'auth_token': auth_token,
            'expires_at': expires_at,
            'ip_address': ip_address,
            'user_agent': user_agent
        })
        
        # Update last login
        self.db.update('users', {'last_login': datetime.now()}, 'user_id = %s', [user['user_id']])
        
        return True, {
            'session_id': session_id,
            'auth_token': auth_token,
            'user_id': user['user_id'],
            'username': user['username'],
            'email': user['email'],
            'private_key': private_key
        }
    
    def validate_session(self, session_id, auth_token):
        session = self.db.fetch_one(
            "SELECT * FROM user_sessions WHERE session_id = %s AND auth_token = %s AND expires_at > NOW()",
            (session_id, auth_token)
        )
        if not session:
            return None
        
        # Update last activity
        self.db.update('user_sessions', {'last_activity': datetime.now()}, 'session_id = %s', [session_id])
        
        # Get user
        user = self.db.fetch_one(
            "SELECT user_id, username, email FROM users WHERE user_id = %s",
            (session['user_id'],)
        )
        
        return user
    
    def logout_user(self, session_id):
        self.db.delete('user_sessions', 'session_id = %s', [session_id])
        return True
    
    def get_user_public_key(self, username):
        user = self.db.fetch_one(
            "SELECT public_key FROM users WHERE username = %s",
            (username,)
        )
        return user['public_key'] if user else None
    
    def get_all_users(self, exclude_user_id=None):
        query = "SELECT user_id, username, email FROM users WHERE is_active = TRUE"
        params = []
        if exclude_user_id:
            query += " AND user_id != %s"
            params.append(exclude_user_id)
        
        return self.db.fetch_all(query, params)