from flask import Blueprint, request, jsonify
from auth.session_store import SessionManager
import base64
import io
import os
import logging

bp = Blueprint('drive', __name__, url_prefix='/api/drive')
logger = logging.getLogger(__name__)

import datetime

def get_local_encrypted_files(folder_id='root'):
    """Helper to return local permanent files/folders as Drive-like objects using DB metadata"""
    from config import config
    from database.db_manager import DatabaseManager
    import os
    
    files = []
    permanent_base_dir = os.path.join(config.UPLOAD_FOLDER, 'permanent')
    
    with DatabaseManager() as db:
        if folder_id == 'root':
            # If Drive is available, show local folders in root.
            # If Drive is NOT available, they will be shown inside 'demo_folder' instead.
            from app import drive_manager
            if not drive_manager.is_available():
                return [] # Don't show local folders in root if Drive is offline (use demo_folder)
                
            # Return unique folder names as virtual folders
            local_folders = db.fetch_all("""
                SELECT DISTINCT folder_name 
                FROM files_metadata 
                WHERE is_deleted = FALSE AND drive_file_id IS NULL
            """)
            
            for folder in local_folders:
                name = folder['folder_name']
                files.append({
                    'id': f"local_folder_{name}",
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'size': 0,
                    'createdTime': datetime.datetime.now().isoformat() + 'Z',
                    'modifiedTime': datetime.datetime.now().isoformat() + 'Z',
                    'webViewLink': '#',
                    'is_local': True
                })
                
        elif folder_id == 'demo_folder':
            # Always show local folders inside the virtual backups folder
            local_folders = db.fetch_all("""
                SELECT DISTINCT folder_name 
                FROM files_metadata 
                WHERE is_deleted = FALSE AND drive_file_id IS NULL
            """)
            
            for folder in local_folders:
                name = folder['folder_name']
                files.append({
                    'id': f"local_folder_{name}",
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'size': 0,
                    'createdTime': datetime.datetime.now().isoformat() + 'Z',
                    'modifiedTime': datetime.datetime.now().isoformat() + 'Z',
                    'webViewLink': '#',
                    'is_local': True
                })
        
        elif folder_id.startswith('local_folder_'):
            # Return files inside this specific local folder
            target_folder = folder_id.replace('local_folder_', '')
            
            local_metas = db.fetch_all("""
                SELECT folder_name, encrypted_filename, encrypted_key_filename, uploaded_at, file_size 
                FROM files_metadata 
                WHERE is_deleted = FALSE AND drive_file_id IS NULL AND folder_name = %s
            """, (target_folder,))
            
            for meta in local_metas:
                # Add Encrypted File
                folder_name = meta['folder_name']
                enc_filename = meta['encrypted_filename']
                enc_path = os.path.join(permanent_base_dir, folder_name, enc_filename)
                
                if os.path.exists(enc_path):
                    files.append({
                        'id': f"local_{enc_filename}",
                        'name': f"🔒 {enc_filename} (Encrypted Data)",
                        'mimeType': 'application/octet-stream',
                        'size': meta['file_size'],
                        'createdTime': meta['uploaded_at'].isoformat() + 'Z' if hasattr(meta['uploaded_at'], 'isoformat') else str(meta['uploaded_at']),
                        'modifiedTime': meta['uploaded_at'].isoformat() + 'Z' if hasattr(meta['uploaded_at'], 'isoformat') else str(meta['uploaded_at']),
                        'webViewLink': '#',
                        'is_local': True
                    })
                    
                # Add Key File
                key_filename = meta['encrypted_key_filename']
                key_path = os.path.join(permanent_base_dir, folder_name, key_filename)
                
                if os.path.exists(key_path):
                    files.append({
                        'id': f"local_{key_filename}",
                        'name': f"🔑 {key_filename} (Decryption Key)",
                        'mimeType': 'application/x-pem-file',
                        'size': os.path.getsize(key_path),
                        'createdTime': meta['uploaded_at'].isoformat() + 'Z' if hasattr(meta['uploaded_at'], 'isoformat') else str(meta['uploaded_at']),
                        'modifiedTime': meta['uploaded_at'].isoformat() + 'Z' if hasattr(meta['uploaded_at'], 'isoformat') else str(meta['uploaded_at']),
                        'webViewLink': '#',
                        'is_local': True
                    })
            
    return files

@bp.route('/list', methods=['POST'])
def list_files():
    """List files and folders in Google Drive (merged with local files)"""
    try:
        from app import drive_manager
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        folder_id = data.get('folder_id', 'root')
        
        files = []
        
        # 1. Get Google Drive files if available
        if drive_manager.is_available():
            results = drive_manager.service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
                orderBy="folder, name"
            ).execute()
            files = results.get('files', [])
        
        # 2. If we are in the root or a local folder, add local content
        if folder_id == 'root' or folder_id.startswith('local_folder_'):
            local_files = get_local_encrypted_files(folder_id)
            # Append local files to the list
            files.extend(local_files)
            
            # Also add the virtual backups folder if Drive isn't available and we are in root
            if folder_id == 'root' and not drive_manager.is_available():
                files.append({
                    'id': 'demo_folder',
                    'name': 'My Secure Backups',
                    'mimeType': 'application/vnd.google-apps.folder',
                    'size': 0,
                    'createdTime': datetime.datetime.now().isoformat() + 'Z',
                    'modifiedTime': datetime.datetime.now().isoformat() + 'Z'
                })
        
        # 3. Handle the virtual demo folder
        elif folder_id == 'demo_folder':
            files = get_local_encrypted_files(folder_id)
            
        return jsonify({
            'success': True,
            'data': {'files': files, 'folder_id': folder_id}
        })
        
    except Exception as e:
        logger.error(f"Drive list error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/download', methods=['POST'])
def download_file():
    """Download a file from Google Drive (with local fallback)"""
    try:
        from app import drive_manager
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        file_id = data.get('file_id')
        file_name = data.get('file_name', 'download')
        
        if not file_id:
            return jsonify({'success': False, 'message': 'Missing file_id'}), 400
            
        # Ensure file_id is a string and handle accidental dictionary/content passing
        if isinstance(file_id, dict):
            # If it's a dict, check if it has an 'id' key
            if 'id' in file_id:
                file_id = str(file_id['id'])
            else:
                # If it's a content dict (like the user saw), it's invalid
                return jsonify({'success': False, 'message': 'Invalid file ID format (received content instead of ID)'}), 400
        else:
            file_id = str(file_id)
        
        if not drive_manager.is_available() or file_id.startswith('local_'):
            # Handle local download
            real_filename = file_id.replace('local_', '')
            from config import config
            from database.db_manager import DatabaseManager
            
            # Use absolute path from config
            permanent_base_dir = os.path.join(config.UPLOAD_FOLDER, 'permanent')
            
            with DatabaseManager() as db:
                # Find folder_name from database
                file_meta = db.fetch_one("""
                    SELECT folder_name FROM files_metadata 
                    WHERE (encrypted_filename = %s OR encrypted_key_filename = %s)
                """, (real_filename, real_filename))
            
            if file_meta:
                file_path = os.path.join(permanent_base_dir, file_meta['folder_name'], real_filename)
                # Fallback for legacy files
                if not os.path.exists(file_path):
                    file_path = os.path.join(permanent_base_dir, real_filename)
            else:
                file_path = os.path.join(permanent_base_dir, real_filename)
            
            if not os.path.exists(file_path):
                return jsonify({'success': False, 'message': f'Local file not found at {file_path}'}), 404
                
            with open(file_path, 'rb') as f:
                content = f.read()
            
            return jsonify({
                'success': True,
                'data': {
                    'content': base64.b64encode(content).decode('utf-8'),
                    'file_name': file_name
                }
            })
        
        # Download file content from Drive
        request_drive = drive_manager.service.files().get_media(fileId=file_id)
        content = request_drive.execute()
        
        return jsonify({
            'success': True,
            'data': {
                'content': base64.b64encode(content).decode('utf-8'),
                'file_name': file_name
            }
        })
            
    except Exception as e:
        logger.error(f"Drive download error: {e}")
        # Only return the first 100 characters of the error message to avoid UI issues
        error_msg = str(e)
        if len(error_msg) > 100:
            error_msg = error_msg[:100] + "..."
        return jsonify({'success': False, 'message': error_msg}), 500

@bp.route('/upload', methods=['POST'])
def upload_file():
    """Upload a file to Google Drive"""
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        file_name = data.get('file_name')
        file_content = data.get('file_content')
        parent_id = data.get('parent_id', 'root')
        
        if not file_name or not file_content:
            return jsonify({'success': False, 'message': 'Missing file data'}), 400
        
        # Decode base64 content
        content = base64.b64decode(file_content)
        
        # Create temporary file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{file_name}") as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        from app import drive_manager
        try:
            # Upload to Drive
            file_id, link = drive_manager.upload_file(tmp_path, file_name, parent_id=parent_id)
            
            # Cleanup
            os.unlink(tmp_path)
            
            return jsonify({
                'success': True,
                'data': {'file_id': file_id, 'link': link}
            })
        except Exception as e:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise e
            
    except Exception as e:
        logger.error(f"Drive upload error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/search', methods=['POST'])
def search_files():
    """Search files in Google Drive"""
    try:
        user = SessionManager.get_current_user()
        if not user:
            return jsonify({'success': False, 'message': 'Not logged in'}), 401
        
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'success': False, 'message': 'Search query required'}), 400
        
        from app import drive_manager
        # Search Drive
        results = drive_manager.service.files().list(
            q=f"name contains '{query}' and trashed=false",
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)",
            orderBy="folder, name"
        ).execute()
        files = results.get('files', [])
        
        return jsonify({
            'success': True,
            'data': {'files': files}
        })
        
    except Exception as e:
        logger.error(f"Drive search error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/storage', methods=['GET'])
def get_storage_info():
    """Get Google Drive storage usage info"""
    try:
        from app import drive_manager
        if not drive_manager.is_available():
            # Return dummy data for local mode
            return jsonify({
                'success': True,
                'data': {
                    'total': 15 * 1024 * 1024 * 1024, # 15GB
                    'used': 100 * 1024 * 1024, # 100MB
                    'fileCount': 0,
                    'folderCount': 0
                }
            })
            
        about = drive_manager.service.about().get(fields="storageQuota, user").execute()
        quota = about.get('storageQuota', {})
        
        # Get counts
        files = drive_manager.service.files().list(
            q="trashed=false",
            fields="files(id, mimeType)"
        ).execute().get('files', [])
        
        file_count = len([f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder'])
        folder_count = len([f for f in files if f['mimeType'] == 'application/vnd.google-apps.folder'])
        
        return jsonify({
            'success': True,
            'data': {
                'total': int(quota.get('limit', 0)),
                'used': int(quota.get('usage', 0)),
                'fileCount': file_count,
                'folderCount': folder_count,
                'user': about.get('user', {})
            }
        })
    except Exception as e:
        logger.error(f"Storage info error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
