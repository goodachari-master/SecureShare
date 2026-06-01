from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import io
from config import config

class DriveManager:
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        try:
            creds = None
            if os.path.exists(config.GOOGLE_DRIVE_TOKEN):
                creds = Credentials.from_authorized_user_file(config.GOOGLE_DRIVE_TOKEN, self.SCOPES)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(config.GOOGLE_DRIVE_CREDENTIALS):
                        print(f"Warning: {config.GOOGLE_DRIVE_CREDENTIALS} not found. Google Drive features will be disabled.")
                        return
                    flow = InstalledAppFlow.from_client_secrets_file(
                        config.GOOGLE_DRIVE_CREDENTIALS, self.SCOPES)
                    # creds = flow.run_local_server(port=0, open_browser=False)
                    print("Warning: Google Drive authentication required. Please run locally to authorize.")
                    return
                
                with open(config.GOOGLE_DRIVE_TOKEN, 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('drive', 'v3', credentials=creds)
        except Exception as e:
            print(f"Warning: Google Drive authentication failed: {e}. Google Drive features will be disabled.")
    
    def _check_service(self):
        if not self.service:
            raise Exception("Google Drive service not initialized. Please ensure credentials.json exists and you have authorized the app.")

    def is_available(self):
        return self.service is not None

    def create_folder(self, folder_name, parent_id=None):
        self._check_service()
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        folder = self.service.files().create(body=file_metadata, fields='id').execute()
        return folder.get('id')
    
    def upload_file(self, file_path, file_name, mime_type='application/octet-stream', parent_id=None):
        self._check_service()
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        file_metadata = {'name': file_name}
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        return file.get('id'), file.get('webViewLink')
    
    def download_file(self, file_id, destination_path):
        self._check_service()
        request = self.service.files().get_media(fileId=file_id)
        fh = io.FileIO(destination_path, 'wb')
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        fh.close()
        return destination_path
    
    def delete_file(self, file_id):
        self._check_service()
        self.service.files().delete(fileId=file_id).execute()
    
    def list_files(self, folder_id=None):
        self._check_service()
        query = []
        if folder_id:
            query.append(f"'{folder_id}' in parents")
        query.append("trashed=false")
        
        results = self.service.files().list(
            q=" and ".join(query),
            fields="files(id, name, mimeType, size, createdTime)"
        ).execute()
        
        return results.get('files', [])
    
    def get_share_link(self, file_id):
        self._check_service()
        file = self.service.files().get(fileId=file_id, fields='webViewLink').execute()
        return file.get('webViewLink')