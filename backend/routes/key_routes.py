from flask import Blueprint, request, jsonify
from auth.session_store import SessionManager
from database.db_manager import DatabaseManager
from encryption.key_manager import KeyManager
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
import hashlib
import logging

bp = Blueprint('keys', __name__, url_prefix='/api')
db_manager = DatabaseManager()
logger = logging.getLogger(__name__)

@bp.route('/keys/public', methods=['GET'])
def get_public_key():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        result = db_manager.fetch_one(
            "SELECT public_key FROM users WHERE user_id = %s",
            (user['user_id'],)
        )
        
        if result:
            return jsonify({'success': True, 'data': {'public_key': result['public_key']}})
        return jsonify({'success': False, 'message': 'Key not found'}), 404
    
    except Exception as e:
        logger.error(f"Get public key error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/keys/fingerprint', methods=['GET'])
def get_key_fingerprint():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        result = db_manager.fetch_one(
            "SELECT public_key FROM users WHERE user_id = %s",
            (user['user_id'],)
        )
        
        if result:
            # Generate fingerprint
            fingerprint = hashlib.sha256(result['public_key'].encode()).hexdigest()[:16]
            fingerprint_formatted = ':'.join(fingerprint[i:i+2] for i in range(0, 16, 2))
            
            return jsonify({'success': True, 'data': {
                'fingerprint': fingerprint_formatted.upper(),
                'algorithm': 'RSA-4096',
                'padding': 'OAEP',
                'hash': 'SHA-256'
            }})
        return jsonify({'success': False, 'message': 'Key not found'}), 404
    
    except Exception as e:
        logger.error(f"Get fingerprint error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/keys/private', methods=['POST'])
def get_private_key():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        password = data.get('password')
        
        if not password:
            return jsonify({'success': False, 'message': 'Password required'}), 400
        
        # Get encrypted private key data
        result = db_manager.fetch_one(
            "SELECT private_key_encrypted, private_key_iv, private_key_tag, private_key_salt FROM users WHERE user_id = %s",
            (user['user_id'],)
        )
        
        if not result:
            return jsonify({'success': False, 'message': 'User data not found'}), 404
            
        encrypted_data = {
            'salt': result['private_key_salt'],
            'iv': result['private_key_iv'],
            'tag': result['private_key_tag'],
            'ciphertext': result['private_key_encrypted']
        }
        
        try:
            # Decrypt private key
            private_key = KeyManager.decrypt_private_key_with_password(encrypted_data, password)
            return jsonify({'success': True, 'data': {'private_key': private_key}})
        except Exception as de:
            logger.warning(f"Failed to decrypt private key for user {user['user_id']}: {de}")
            return jsonify({'success': False, 'message': 'Invalid password or decryption failed'}), 401
            
    except Exception as e:
        logger.error(f"Get private key error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500