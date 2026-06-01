from flask import Blueprint, request, jsonify, session
from auth.session_store import SessionManager
from database.db_manager import DatabaseManager
from encryption.crypto_manager import CryptoManager
from cloud.drive_manager import DriveManager
from auth.auth_manager import AuthManager
from config import config
import os
import uuid
import json
from datetime import datetime
import logging

bp = Blueprint('files', __name__, url_prefix='/api')
db_manager = DatabaseManager()
crypto_manager = CryptoManager()
drive_manager = DriveManager()
auth_manager = AuthManager(db_manager)
logger = logging.getLogger(__name__)

# Use config for upload folder
# config.UPLOAD_FOLDER is the base uploads directory
# We use temp for transient files
TEMP_UPLOAD_FOLDER = os.path.join(config.UPLOAD_FOLDER, 'temp')

@bp.route('/upload', methods=['POST'])
def upload_file():
    try:
        sender = SessionManager.get_current_user()
        if not sender:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        recipient_username = data.get('recipient')
        folder_name = data.get('folder_name')
        file_content = data.get('file_content')
        original_filename = data.get('filename')
        
        if not all([recipient_username, folder_name, file_content, original_filename]):
            return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
        # Get recipient's public key
        recipient_public_key = auth_manager.get_user_public_key(recipient_username)
        if not recipient_public_key:
            return jsonify({'success': False, 'message': 'Recipient not found'}), 404
        
        # Get recipient user ID
        recipient = db_manager.fetch_one(
            "SELECT user_id, username FROM users WHERE username = %s",
            (recipient_username,)
        )
        
        # ... logic continues ...
        # Make sure to replace any usage of UPLOAD_FOLDER with TEMP_UPLOAD_FOLDER or config.UPLOAD_FOLDER
        
        # If not found by exact match, try case-insensitive for ID as well
        if not recipient:
            recipient = db_manager.fetch_one(
                "SELECT user_id, username FROM users WHERE LOWER(username) = LOWER(%s)",
                (recipient_username,)
            )
        
        if not recipient:
            return jsonify({'success': False, 'message': 'Recipient record not found'}), 404
        
        # Update recipient_username to the actual case-sensitive username from DB
        recipient_username = recipient['username']
        
        # Generate AES key and IV
        aes_key = crypto_manager.generate_aes_key()
        iv = crypto_manager.generate_iv()
        
        # Decode file content
        import base64
        file_bytes = base64.b64decode(file_content)
        
        # Encrypt file with AES
        ciphertext, tag = crypto_manager.encrypt_aes_gcm(file_bytes, aes_key, iv)
        
        # Encrypt AES key with recipient's public key
        encrypted_aes_key = crypto_manager.encrypt_rsa_oaep(aes_key, recipient_public_key)
        
        # Save encrypted files locally (initially in temp)
        os.makedirs(TEMP_UPLOAD_FOLDER, exist_ok=True)
        temp_id = str(uuid.uuid4())
        encrypted_filename = f"{temp_id}_encrypted.enc"
        key_filename = f"{temp_id}_key.key"
        encrypted_path = os.path.join(TEMP_UPLOAD_FOLDER, encrypted_filename)
        key_path = os.path.join(TEMP_UPLOAD_FOLDER, key_filename)
        
        # Save encrypted file with IV and tag
        with open(encrypted_path, 'wb') as f:
            f.write(iv + tag + ciphertext)
        
        # Save encrypted key
        with open(key_path, 'wb') as f:
            f.write(encrypted_aes_key)
        
        drive_file_id = None
        drive_key_file_id = None
        drive_folder_id = None
        share_link = None
        
        # Check if Google Drive is available
        if drive_manager.is_available():
            try:
                # Create folder in Google Drive
                drive_folder_id = drive_manager.create_folder(folder_name)
                
                # Upload encrypted file
                drive_file_id, share_link = drive_manager.upload_file(
                    encrypted_path, encrypted_filename, parent_id=drive_folder_id
                )
                
                # Upload encrypted key
                drive_key_file_id, _ = drive_manager.upload_file(
                    key_path, key_filename, parent_id=drive_folder_id
                )
            except Exception as de:
                logger.warning(f"Google Drive upload failed, falling back to local storage: {de}")
        
        # If Drive failed or is not available, move files to permanent local storage
        if not drive_file_id:
            # Create a folder with folder_name inside permanent
            permanent_dir = os.path.join(config.UPLOAD_FOLDER, 'permanent', folder_name)
            os.makedirs(permanent_dir, exist_ok=True)
            
            local_encrypted_path = os.path.join(permanent_dir, encrypted_filename)
            local_key_path = os.path.join(permanent_dir, key_filename)
            
            import shutil
            shutil.copy2(encrypted_path, local_encrypted_path)
            shutil.copy2(key_path, local_key_path)
            
            logger.info(f"File stored locally in folder '{folder_name}' at {local_encrypted_path}")
        
        # Store metadata
        file_id = db_manager.insert('files_metadata', {
            'folder_name': folder_name,
            'original_filename': original_filename,
            'encrypted_filename': encrypted_filename,
            'encrypted_key_filename': key_filename,
            'file_size': len(file_bytes),
            'file_hash': '',
            'sender_id': sender['user_id'],
            'recipient_id': recipient['user_id'],
            'drive_file_id': drive_file_id,
            'drive_key_file_id': drive_key_file_id,
            'drive_folder_id': drive_folder_id,
            'share_link': share_link,
            'is_read': False
        })
        
        # Create notification for recipient
        db_manager.insert('notifications', {
            'user_id': recipient['user_id'],
            'from_user_id': sender['user_id'],
            'file_id': file_id,
            'type': 'file_received',
            'title': 'New File Shared',
            'message': f"{sender['username']} shared '{original_filename}' with you"
        })
        
        # Cleanup temp files
        os.remove(encrypted_path)
        os.remove(key_path)
        
        return jsonify({
            'success': True,
            'message': 'File uploaded successfully',
            'data': {
                'file_id': file_id,
                'share_link': share_link
            }
        })
    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/files/received', methods=['GET'])
def get_received_files():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        files = db_manager.fetch_all("""
            SELECT f.*, s.username as sender_username 
            FROM files_metadata f
            JOIN users s ON f.sender_id = s.user_id
            WHERE f.recipient_id = %s AND f.is_deleted = FALSE
            ORDER BY f.uploaded_at DESC
        """, (user['user_id'],))
        
        return jsonify({'success': True, 'data': files})
    
    except Exception as e:
        logger.error(f"Get received files error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/files/sent', methods=['GET'])
def get_sent_files():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        files = db_manager.fetch_all("""
            SELECT f.*, r.username as recipient_username 
            FROM files_metadata f
            JOIN users r ON f.recipient_id = r.user_id
            WHERE f.sender_id = %s AND f.is_deleted = FALSE
            ORDER BY f.uploaded_at DESC
        """, (user['user_id'],))
        
        return jsonify({'success': True, 'data': files})
    
    except Exception as e:
        logger.error(f"Get sent files error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/extract', methods=['POST'])
def extract_file():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({'success': False, 'message': 'File ID required'}), 400
        
        # Get file metadata
        file_meta = db_manager.fetch_one("""
            SELECT f.*, s.username as sender_username 
            FROM files_metadata f
            JOIN users s ON f.sender_id = s.user_id
            WHERE f.file_id = %s AND f.recipient_id = %s
        """, (file_id, user['user_id']))
        
        if not file_meta:
            return jsonify({'success': False, 'message': 'File not found or access denied'}), 404
        
        # Get user's private key from session
        private_key_pem = SessionManager.get_private_key()
        if not private_key_pem:
            return jsonify({'success': False, 'message': 'Private key not available'}), 401
        
        # Create temp directory for download/extraction
        temp_dir = os.path.join(TEMP_UPLOAD_FOLDER, str(uuid.uuid4()))
        os.makedirs(temp_dir)
        
        encrypted_path = os.path.join(temp_dir, file_meta['encrypted_filename'])
        key_path = os.path.join(temp_dir, file_meta['encrypted_key_filename'])
        
        # If the file is on Google Drive, download it
        if file_meta['drive_file_id']:
            drive_manager.download_file(file_meta['drive_file_id'], encrypted_path)
            drive_manager.download_file(file_meta['drive_key_file_id'], key_path)
        else:
            # File is stored locally in permanent directory (possibly in a subfolder)
            permanent_base_dir = os.path.join(config.UPLOAD_FOLDER, 'permanent')
            folder_name = file_meta.get('folder_name', '')
            
            local_encrypted = os.path.join(permanent_base_dir, folder_name, file_meta['encrypted_filename'])
            local_key = os.path.join(permanent_base_dir, folder_name, file_meta['encrypted_key_filename'])
            
            # Fallback for legacy files (no subfolder)
            if not os.path.exists(local_encrypted):
                local_encrypted = os.path.join(permanent_base_dir, file_meta['encrypted_filename'])
            if not os.path.exists(local_key):
                local_key = os.path.join(permanent_base_dir, file_meta['encrypted_key_filename'])
            
            if not os.path.exists(local_encrypted) or not os.path.exists(local_key):
                return jsonify({'success': False, 'message': 'Encrypted files not found on local storage'}), 404
            
            import shutil
            shutil.copy2(local_encrypted, encrypted_path)
            shutil.copy2(local_key, key_path)
            
            logger.info(f"Extracted file from local storage: {local_encrypted}")
        
        # Read encrypted key
        with open(key_path, 'rb') as f:
            encrypted_aes_key = f.read()
        
        # Decrypt AES key with private key
        aes_key = crypto_manager.decrypt_rsa_oaep(encrypted_aes_key, private_key_pem)
        
        # Read encrypted file
        with open(encrypted_path, 'rb') as f:
            iv = f.read(12)
            tag = f.read(16)
            ciphertext = f.read()
        
        # Decrypt file
        plaintext = crypto_manager.decrypt_aes_gcm(ciphertext, aes_key, iv, tag)
        
        # Mark file as read if not already
        if not file_meta['is_read']:
            db_manager.update('files_metadata', 
                {'is_read': True, 'read_at': datetime.now()}, 
                'file_id = %s', [file_id])
            
            # Send read receipt notification to sender
            db_manager.insert('notifications', {
                'user_id': file_meta['sender_id'],
                'from_user_id': user['user_id'],
                'file_id': file_id,
                'type': 'file_read',
                'title': 'File Extracted',
                'message': f"{user['username']} extracted your file '{file_meta['original_filename']}'"
            })
        
        # Log access
        db_manager.insert('file_access_log', {
            'file_id': file_id,
            'accessed_by_user_id': user['user_id'],
            'ip_address': request.remote_addr
        })
        
        # Return decrypted file
        import base64
        file_content = base64.b64encode(plaintext).decode('utf-8')
        
        # Cleanup
        import shutil
        shutil.rmtree(temp_dir)
        
        return jsonify({
            'success': True,
            'message': 'File extracted successfully',
            'data': {
                'filename': file_meta['original_filename'],
                'content': file_content
            }
        })
    
    except Exception as e:
        logger.error(f"Extract error: {e}")
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        return jsonify({'success': False, 'message': error_msg}), 500

@bp.route('/files/delete', methods=['POST'])
def delete_file():
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        file_id = data.get('file_id')
        
        if not file_id:
            return jsonify({'success': False, 'message': 'File ID required'}), 400
        
        # Check if user is sender or recipient
        file_meta = db_manager.fetch_one("""
            SELECT file_id, sender_id, recipient_id 
            FROM files_metadata 
            WHERE file_id = %s AND (sender_id = %s OR recipient_id = %s)
        """, (file_id, user['user_id'], user['user_id']))
        
        if not file_meta:
            return jsonify({'success': False, 'message': 'File not found or access denied'}), 404
        
        # Soft delete in database
        db_manager.update('files_metadata', {'is_deleted': True}, 'file_id = %s', [file_id])
        
        # Log activity
        db_manager.insert('activity_logs', {
            'user_id': user['user_id'],
            'action': 'delete_file',
            'details': f"Deleted file ID {file_id}",
            'ip_address': request.remote_addr
        })
        
        return jsonify({
            'success': True,
            'message': 'File deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500