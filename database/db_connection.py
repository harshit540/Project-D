import os
import sqlite3
from core.logger import logger

class DatabaseConnection:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseConnection, cls).__new__(cls)
            cls._instance._db_path = os.path.join(os.path.expanduser("~"), ".synchub", "synchub.db")
            os.makedirs(os.path.dirname(cls._instance._db_path), exist_ok=True)
            cls._instance.init_db()
        return cls._instance

    def get_connection(self):
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row
            return conn
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise e

    def init_db(self):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            # Enable Foreign Keys
            cursor.execute("PRAGMA foreign_keys = ON;")
            
            # Accounts Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT,
                    encrypted_token TEXT NOT NULL,
                    avatar_url TEXT
                );
            """)

            # Workspace Tabs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tabs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    folder_path TEXT NOT NULL,
                    account_id INTEGER,
                    repo_name TEXT,
                    branch TEXT DEFAULT 'main',
                    sync_mode TEXT DEFAULT 'manual',
                    sync_interval INTEGER DEFAULT 300,
                    commit_msg_template TEXT DEFAULT 'Auto Sync - {datetime}',
                    notifications_enabled INTEGER DEFAULT 1,
                    history_limit INTEGER DEFAULT 20,
                    app_trigger_exe TEXT,
                    app_trigger_on_open TEXT DEFAULT 'Do Nothing',
                    app_trigger_on_close TEXT DEFAULT 'Do Nothing',
                    conflict_resolution_mode TEXT DEFAULT 'Auto Resolve',
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
                );
            """)

            # Sync History Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tab_id INTEGER NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    operation_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    commit_hash TEXT,
                    message TEXT,
                    error_details TEXT,
                    FOREIGN KEY (tab_id) REFERENCES tabs(id) ON DELETE CASCADE
                );
            """)

            # Global Application Settings Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS global_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
            """)
            conn.commit()
            logger.info("Database initialized successfully.")