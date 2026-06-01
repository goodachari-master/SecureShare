from flask import session
from datetime import datetime, timedelta
import json

class SessionManager:
    @staticmethod
    def set_user_session(user_data):
        """Store user session data"""
        session['user_id'] = user_data['user_id']
        session['username'] = user_data['username']
        session['email'] = user_data['email']
        session['private_key'] = user_data.get('private_key')
        session['login_time'] = datetime.now().isoformat()
        session.permanent = True
    
    @staticmethod
    def get_current_user():
        """Get current user from session"""
        if 'user_id' in session:
            return {
                'user_id': session['user_id'],
                'username': session['username'],
                'email': session['email'],
                'private_key': session.get('private_key')
            }
        return None
    
    @staticmethod
    def get_private_key():
        """Get decrypted private key from session"""
        return session.get('private_key')
    
    @staticmethod
    def clear_user_session():
        """Clear all session data"""
        session.clear()
    
    @staticmethod
    def is_logged_in():
        """Check if user is logged in"""
        return 'user_id' in session
    
    @staticmethod
    def refresh_session():
        """Refresh session expiry"""
        session.permanent = True