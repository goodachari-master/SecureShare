import mysql.connector
from mysql.connector import Error, pooling
from config import config
import logging
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    _pool = None
    _lock = threading.Lock()

    def __init__(self):
        self.connection = None
        if DatabaseManager._pool is None:
            with DatabaseManager._lock:
                # Double-check inside lock
                if DatabaseManager._pool is None:
                    try:
                        DatabaseManager._pool = mysql.connector.pooling.MySQLConnectionPool(
                            pool_name="secure_share_pool",
                            pool_size=15, # Increased pool size for high-frequency polling
                            host=config.DB_HOST,
                            user=config.DB_USER,
                            password=config.DB_PASSWORD,
                            database=config.DB_NAME,
                            use_pure=True # Force pure Python implementation to avoid C-level double-free issues
                        )
                        logger.info("Database connection pool created (Pure Python mode)")
                    except Error as e:
                        logger.error(f"Error creating connection pool: {e}")
                        raise
        
        self.connect()
    
    def connect(self):
        try:
            if not self.connection or not self.connection.is_connected():
                self.connection = DatabaseManager._pool.get_connection()
        except Error as e:
            logger.error(f"Error getting connection from pool: {e}")
            raise
    
    def get_cursor(self, dictionary=True, buffered=True):
        self.connect()
        return self.connection.cursor(dictionary=dictionary, buffered=buffered)
    
    def execute_query(self, query, params=None, commit=True):
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params or ())
            if commit:
                last_id = cursor.lastrowid
                self.connection.commit()
                cursor.close()
                return last_id
            return cursor
        except Error as e:
            if commit:
                self.connection.rollback()
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            logger.error(f"Query execution error: {e}")
            raise
    
    def fetch_one(self, query, params=None):
        cursor = self.execute_query(query, params, commit=False)
        try:
            result = cursor.fetchone()
            return result
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def fetch_all(self, query, params=None):
        cursor = self.execute_query(query, params, commit=False)
        try:
            result = cursor.fetchall()
            return result
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def insert(self, table, data):
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['%s'] * len(data))
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return self.execute_query(query, list(data.values()))
    
    def update(self, table, data, where_clause, where_params):
        set_clause = ', '.join([f"{k} = %s" for k in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + where_params
        self.execute_query(query, params)
    
    def delete(self, table, where_clause, params):
        query = f"DELETE FROM {table} WHERE {where_clause}"
        self.execute_query(query, params)
    
    def close(self):
        if self.connection and self.connection.is_connected():
            self.connection.close()
            self.connection = None
            # logger.info("Database connection returned to pool")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()