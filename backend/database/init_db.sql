-- Secure Cloud File Sharing System
-- Database Schema

-- Create database
CREATE DATABASE IF NOT EXISTS secure_cloud_storage;
USE secure_cloud_storage;

-- ============================================
-- TABLE 1: USERS
-- Stores user accounts with encrypted private keys
-- ============================================
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    public_key TEXT NOT NULL,
    private_key_encrypted TEXT NOT NULL,
    private_key_iv VARCHAR(255) NOT NULL,
    private_key_tag VARCHAR(255) NOT NULL,
    private_key_salt VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE
);

-- ============================================
-- TABLE 2: USER_SESSIONS
-- Manages active sessions for multiple users
-- ============================================
DROP TABLE IF EXISTS user_sessions;
CREATE TABLE user_sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    user_id INT NOT NULL,
    auth_token VARCHAR(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);

-- ============================================
-- TABLE 3: FILES_METADATA
-- Tracks all encrypted files
-- ============================================
DROP TABLE IF EXISTS files_metadata;
CREATE TABLE files_metadata (
    file_id INT PRIMARY KEY AUTO_INCREMENT,
    folder_name VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    encrypted_filename VARCHAR(255) NOT NULL,
    encrypted_key_filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    file_hash VARCHAR(64),
    sender_id INT NOT NULL,
    recipient_id INT NOT NULL,
    drive_file_id VARCHAR(255),
    drive_key_file_id VARCHAR(255),
    drive_folder_id VARCHAR(255),
    share_link TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id),
    INDEX idx_sender (sender_id),
    INDEX idx_recipient (recipient_id),
    INDEX idx_folder (folder_name)
);

-- ============================================
-- TABLE 4: NOTIFICATIONS
-- Real-time notifications for users
-- ============================================
DROP TABLE IF EXISTS notifications;
CREATE TABLE notifications (
    notification_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    from_user_id INT NOT NULL,
    file_id INT,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (from_user_id) REFERENCES users(user_id),
    FOREIGN KEY (file_id) REFERENCES files_metadata(file_id) ON DELETE SET NULL,
    INDEX idx_user_unread (user_id, is_read),
    INDEX idx_created (created_at)
);

-- ============================================
-- TABLE 5: FILE_ACCESS_LOG
-- Track when files are accessed
-- ============================================
DROP TABLE IF EXISTS file_access_log;
CREATE TABLE file_access_log (
    access_id INT PRIMARY KEY AUTO_INCREMENT,
    file_id INT NOT NULL,
    accessed_by_user_id INT NOT NULL,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    FOREIGN KEY (file_id) REFERENCES files_metadata(file_id) ON DELETE CASCADE,
    FOREIGN KEY (accessed_by_user_id) REFERENCES users(user_id),
    INDEX idx_file (file_id)
);

-- ============================================
-- TABLE 6: ACTIVITY_LOGS
-- Tracks all user activities
-- ============================================
DROP TABLE IF EXISTS activity_logs;
CREATE TABLE activity_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100) NOT NULL,
    details TEXT,
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    INDEX idx_user (user_id),
    INDEX idx_created (created_at)
);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX idx_username ON users(username);
CREATE INDEX idx_email ON users(email);
CREATE INDEX idx_session_expiry ON user_sessions(expires_at);
CREATE INDEX idx_files_recipient ON files_metadata(recipient_id, is_deleted);

-- ============================================
-- Insert sample data (for testing)
-- ============================================
INSERT INTO users (username, email, password_hash, public_key, private_key_encrypted, private_key_iv, private_key_tag, private_key_salt)
VALUES ('admin', 'admin@example.com', 'sample_hash', 'sample_key', 'sample_encrypted', 'sample_iv', 'sample_tag', 'sample_salt')
ON DUPLICATE KEY UPDATE user_id=user_id;

-- Done