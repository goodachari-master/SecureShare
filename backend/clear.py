import os
import shutil
from database.db_manager import DatabaseManager
from config import config
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def clear_database():
    """Clear all data from the database tables."""
    db = DatabaseManager()
    
    tables = [
        'activity_logs',
        'file_access_log',
        'notifications',
        'files_metadata',
        'user_sessions',
        'users'
    ]
    
    logger.info("Starting database cleanup...")
    
    try:
        # Disable foreign key checks to allow truncation
        db.execute_query("SET FOREIGN_KEY_CHECKS = 0;")
        
        for table in tables:
            logger.info(f"Clearing table: {table}")
            db.execute_query(f"TRUNCATE TABLE {table};")
            
        # Re-enable foreign key checks
        db.execute_query("SET FOREIGN_KEY_CHECKS = 1;")
        logger.info("Database cleanup completed successfully.")
        
    except Exception as e:
        logger.error(f"Error clearing database: {e}")
    finally:
        db.close()

def clear_files():
    """Clear all uploaded files and session files."""
    # 1. Clear Uploads
    upload_dir = config.UPLOAD_FOLDER
    logger.info(f"Starting file cleanup in: {upload_dir}")
    
    if os.path.exists(upload_dir):
        # We want to keep the main 'uploads' directory but clear its contents
        for item in os.listdir(upload_dir):
            item_path = os.path.join(upload_dir, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                logger.info(f"Deleted: {item}")
            except Exception as e:
                logger.error(f"Failed to delete {item_path}: {e}")
                
        # Recreate essential subdirectories
        os.makedirs(os.path.join(upload_dir, 'permanent'), exist_ok=True)
        os.makedirs(os.path.join(upload_dir, 'temp'), exist_ok=True)
        logger.info("Upload subdirectories recreated.")
    else:
        logger.warning(f"Upload directory {upload_dir} does not exist.")

    # 2. Clear Session Storage
    session_dir = config.SESSION_FILE_DIR
    logger.info(f"Starting session cleanup in: {session_dir}")
    
    if os.path.exists(session_dir):
        try:
            shutil.rmtree(session_dir)
            os.makedirs(session_dir, exist_ok=True)
            logger.info("Session storage cleared.")
        except Exception as e:
            logger.error(f"Failed to clear session storage: {e}")
    else:
        logger.warning(f"Session directory {session_dir} does not exist.")

if __name__ == "__main__":
    print("\n" + "="*40)
    print("      SECURESHARE SYSTEM CLEANUP      ")
    print("="*40)
    
    confirm = input("\nWARNING: This will delete ALL users, files, and database records.\nAre you sure you want to proceed? (y/N): ")
    
    if confirm.lower() == 'y':
        clear_database()
        clear_files()
        print("\n" + "="*40)
        print("          CLEANUP COMPLETED           ")
        print("="*40)
    else:
        print("\nCleanup cancelled.")
