import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'secure_cloud_storage')
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    SESSION_PERMANENT = os.getenv('SESSION_PERMANENT', 'true').lower() == 'true'
    SESSION_TIMEOUT_MINUTES = int(os.getenv('SESSION_TIMEOUT_MINUTES', 30))
    SESSION_FILE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flask_sessions_storage')
    
    # Google Drive
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _creds_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS', 'credentials.json')
    GOOGLE_DRIVE_CREDENTIALS = _creds_path if os.path.isabs(_creds_path) else os.path.join(BASE_DIR, _creds_path)
    
    _token_path = os.getenv('GOOGLE_DRIVE_TOKEN', 'token.json')
    GOOGLE_DRIVE_TOKEN = _token_path if os.path.isabs(_token_path) else os.path.join(BASE_DIR, _token_path)
    
    # Upload
    _upload_path = os.getenv('UPLOAD_FOLDER', 'uploads')
    UPLOAD_FOLDER = _upload_path if os.path.isabs(_upload_path) else os.path.join(BASE_DIR, _upload_path)
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 52428800))
    
    # Encryption
    RSA_KEY_SIZE = int(os.getenv('RSA_KEY_SIZE', 4096))
    AES_KEY_SIZE = int(os.getenv('AES_KEY_SIZE', 32))
    IV_SIZE = int(os.getenv('IV_SIZE', 12))
    
    # App
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    PORT = int(os.getenv('PORT', 5000))
    HOST = os.getenv('HOST', '0.0.0.0')

config = Config()