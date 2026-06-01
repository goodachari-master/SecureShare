# Secure Cloud File Sharing System

## Hybrid AES-256-GCM + RSA-4096-OAEP Encryption

### Features
- End-to-end encryption using hybrid cryptography
- Google Drive integration for cloud storage
- Multi-user support with session isolation
- Real-time notifications for file sharing
- Direct access to shared files (no search needed)
- Secure key management (both keys stored in MySQL)

### Tech Stack
- **Backend**: Flask, Python
- **Database**: MySQL
- **Encryption**: cryptography library (AES-256-GCM, RSA-4096-OAEP)
- **Cloud**: Google Drive API
- **Frontend**: HTML5, CSS3, JavaScript

### Installation

#### 1. Clone Repository
```bash
git clone <repository-url>
cd secure-cloud-file-sharing