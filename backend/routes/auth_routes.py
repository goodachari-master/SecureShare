from flask import Blueprint, request, jsonify, session
from auth.session_store import SessionManager
from database.db_manager import DatabaseManager
from auth.auth_manager import AuthManager
import logging

bp = Blueprint('auth', __name__, url_prefix='/api')
db_manager = DatabaseManager()
auth_manager = AuthManager(db_manager)
logger = logging.getLogger(__name__)

@bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        
        if not all([username, email, password]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        success, result = auth_manager.register_user(username, email, password)
        
        if success:
            return jsonify({'success': True, 'message': 'Registration successful', 'data': result})
        else:
            return jsonify({'success': False, 'message': result}), 400
    
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not all([username, password]):
            return jsonify({'success': False, 'message': 'Missing username or password'}), 400
        
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent')
        
        success, result = auth_manager.login_user(username, password, ip_address, user_agent)
        
        if success:
            SessionManager.set_user_session({
                'user_id': result['user_id'],
                'username': result['username'],
                'email': result['email'],
                'private_key': result['private_key']
            })
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'data': {
                    'user_id': result['user_id'],
                    'username': result['username'],
                    'email': result['email'],
                    'session_id': result['session_id']
                }
            })
        else:
            return jsonify({'success': False, 'message': result}), 401
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/logout', methods=['POST'])
def logout():
    try:
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            auth_manager.logout_user(session_id)
        
        SessionManager.clear_user_session()
        return jsonify({'success': True, 'message': 'Logged out successfully'})
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/me', methods=['GET'])
def get_current_user():
    try:
        user = SessionManager.get_current_user()
        if user:
            return jsonify({'success': True, 'data': user})
        return jsonify({'success': False, 'message': 'Not logged in'}), 401
    
    except Exception as e:
        logger.error(f"Get user error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/users', methods=['GET'])
def get_users():
    try:
        current_user = SessionManager.get_current_user()
        if not current_user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        users = auth_manager.get_all_users(current_user['user_id'])
        return jsonify({'success': True, 'data': users})
    
    except Exception as e:
        logger.error(f"Get users error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500