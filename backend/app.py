from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
import os
import sys
from datetime import timedelta

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config
from database.db_manager import DatabaseManager
from auth.auth_manager import AuthManager
from encryption.crypto_manager import CryptoManager
from cloud.drive_manager import DriveManager

app = Flask(__name__, static_folder='../frontend', static_url_path='')
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['SESSION_TYPE'] = config.SESSION_TYPE
app.config['SESSION_PERMANENT'] = config.SESSION_PERMANENT
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=config.SESSION_TIMEOUT_MINUTES)
app.config['SESSION_FILE_DIR'] = config.SESSION_FILE_DIR
app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = config.MAX_CONTENT_LENGTH

# Initialize extensions
CORS(app, supports_credentials=True)
Session(app)

# Initialize managers
db_manager = DatabaseManager()
auth_manager = AuthManager(db_manager)
crypto_manager = CryptoManager()
drive_manager = DriveManager()

# Ensure upload and session directories exist
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(config.UPLOAD_FOLDER, 'temp'), exist_ok=True)
os.makedirs(os.path.join(config.UPLOAD_FOLDER, 'permanent'), exist_ok=True)
os.makedirs(os.path.join(config.UPLOAD_FOLDER, 'downloads'), exist_ok=True)
os.makedirs(os.path.join(config.UPLOAD_FOLDER, 'keys'), exist_ok=True)
os.makedirs(config.SESSION_FILE_DIR, exist_ok=True)

# Import routes
from routes import auth_routes, file_routes, notification_routes, key_routes, drive_routes

# Register blueprints
app.register_blueprint(auth_routes.bp)
app.register_blueprint(file_routes.bp)
app.register_blueprint(notification_routes.bp)
app.register_blueprint(key_routes.bp)
app.register_blueprint(drive_routes.bp)

# Serve frontend
@app.route('/')
def serve_index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

if __name__ == '__main__':
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)