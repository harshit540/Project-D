from database.db_connection import DatabaseConnection
import json
from core.logger import logger

class SettingsRepository:
    @staticmethod
    def get(key, default=None):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM global_settings WHERE key = ?;", (key,))
            row = cursor.fetchone()
            if row:
                try:
                    return json.loads(row[0])
                except json.JSONDecodeError:
                    return row[0]
            return default

    @staticmethod
    def set(key, value):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            serialized = json.dumps(value)
            cursor.execute("""
                INSERT INTO global_settings (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
            """, (key, serialized))
            conn.commit()

class AccountRepository:
    @staticmethod
    def add_account(username, email, encrypted_token, avatar_url=None):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO accounts (username, email, encrypted_token, avatar_url)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username) DO UPDATE SET
                    email = excluded.email,
                    encrypted_token = excluded.encrypted_token,
                    avatar_url = excluded.avatar_url;
            """, (username, email, encrypted_token, avatar_url))
            conn.commit()
            return cursor.lastrowid

    @staticmethod
    def get_all_accounts():
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts;")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete_account(account_id):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM accounts WHERE id = ?;", (account_id,))
            conn.commit()

class TabRepository:
    @staticmethod
    def save_tab(tab_data):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            if tab_data.get("id"):
                cursor.execute("""
                    UPDATE tabs SET
                        name = :name, folder_path = :folder_path, account_id = :account_id,
                        repo_name = :repo_name, branch = :branch, sync_mode = :sync_mode,
                        sync_interval = :sync_interval, commit_msg_template = :commit_msg_template,
                        notifications_enabled = :notifications_enabled, history_limit = :history_limit,
                        app_trigger_exe = :app_trigger_exe, app_trigger_on_open = :app_trigger_on_open,
                        app_trigger_on_close = :app_trigger_on_close, conflict_resolution_mode = :conflict_resolution_mode
                    WHERE id = :id;
                """, tab_data)
                tab_id = tab_data["id"]
            else:
                cursor.execute("""
                    INSERT INTO tabs (
                        name, folder_path, account_id, repo_name, branch, sync_mode,
                        sync_interval, commit_msg_template, notifications_enabled, history_limit,
                        app_trigger_exe, app_trigger_on_open, app_trigger_on_close, conflict_resolution_mode
                    ) VALUES (
                        :name, :folder_path, :account_id, :repo_name, :branch, :sync_mode,
                        :sync_interval, :commit_msg_template, :notifications_enabled, :history_limit,
                        :app_trigger_exe, :app_trigger_on_open, :app_trigger_on_close, :conflict_resolution_mode
                    );
                """, tab_data)
                tab_id = cursor.lastrowid
            conn.commit()
            return tab_id

    @staticmethod
    def get_all_tabs():
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tabs;")
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def delete_tab(tab_id):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tabs WHERE id = ?;", (tab_id,))
            conn.commit()

class HistoryRepository:
    @staticmethod
    def add_log(tab_id, operation_type, status, commit_hash=None, message=None, error_details=None):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_history (tab_id, operation_type, status, commit_hash, message, error_details)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (tab_id, operation_type, status, commit_hash, message, error_details))
            
            # Enforce log limits
            cursor.execute("SELECT history_limit FROM tabs WHERE id = ?;", (tab_id,))
            limit_row = cursor.fetchone()
            limit = limit_row[0] if limit_row else 20
            
            cursor.execute("""
                DELETE FROM sync_history 
                WHERE tab_id = ? AND id NOT IN (
                    SELECT id FROM sync_history WHERE tab_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                );
            """, (tab_id, tab_id, limit))
            conn.commit()

    @staticmethod
    def get_logs_for_tab(tab_id):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sync_history WHERE tab_id = ? ORDER BY timestamp DESC;", (tab_id,))
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def get_all_logs():
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT h.*, t.name as tab_name 
                FROM sync_history h 
                JOIN tabs t ON h.tab_id = t.id 
                ORDER BY h.timestamp DESC;
            """)
            return [dict(row) for row in cursor.fetchall()]

    @staticmethod
    def clear_history_for_tab(tab_id):
        db = DatabaseConnection()
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sync_history WHERE tab_id = ?;", (tab_id,))
            conn.commit()