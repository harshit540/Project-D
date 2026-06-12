import os
import shutil
import json
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QCheckBox, QPushButton, QLabel, QMessageBox, QFileDialog, QProgressBar
from PySide6.QtCore import Qt
from database.db_connection import DatabaseConnection
from database.models import TabRepository, AccountRepository
from github.github_client import GitHubClient
from core.logger import logger

class CreateRepoDialog(QDialog):
    def __init__(self, account_data, parent=None):
        super().__init__(parent)
        self.account = account_data
        self.created_repo_data = None
        self.setWindowTitle("Create New GitHub Repository")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_name = QLineEdit()
        form.addRow("Repository Name:", self.txt_name)

        self.txt_desc = QLineEdit()
        form.addRow("Description:", self.txt_desc)

        self.chk_private = QCheckBox()
        self.chk_private.setChecked(True)
        form.addRow("Private Repository:", self.chk_private)

        self.chk_readme = QCheckBox()
        self.chk_readme.setChecked(True)
        form.addRow("Add default README.md:", self.chk_readme)

        self.cmb_license = QComboBox()
        self.cmb_license.addItems(["None", "mit", "apache-2.0", "gpl-3.0"])
        form.addRow("Select License Layout:", self.cmb_license)

        layout.addLayout(form)

        buttons = QHBoxLayout()
        btn_ok = QPushButton("Create Remote Repository")
        btn_ok.clicked.connect(self.create_remote)
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)

        buttons.addWidget(btn_ok)
        buttons.addWidget(btn_cancel)
        layout.addLayout(buttons)

    def create_remote(self):
        name = self.txt_name.text().strip()
        if not name:
            QMessageBox.critical(self, "Invalid Name", "A unique repository name is mandatory.")
            return

        try:
            from security.crypt_manager import CryptManager
            token = CryptManager.decrypt(self.account["encrypted_token"])
            client = GitHubClient(token)
            
            self.created_repo_data = client.create_repository(
                name=name,
                description=self.txt_desc.text(),
                is_private=self.chk_private.isChecked(),
                init_readme=self.chk_readme.isChecked(),
                license_template=self.cmb_license.currentText()
            )
            QMessageBox.information(self, "Success", f"Repository {name} successfully created on your remote GitHub account.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Creation Failed", f"Failed to complete GitHub repository setup: {e}")

class BackupManagerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SyncHub Workspace Backup Operations")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        lbl_info = QLabel("Export or restore your active local workspace maps and app metadata:")
        lbl_info.setStyleSheet("font-weight: bold;")
        layout.addWidget(lbl_info)

        btn_export = QPushButton("Export Settings Workspace Backup (.json)")
        btn_export.clicked.connect(self.export_backup)
        layout.addWidget(btn_export)

        btn_import = QPushButton("Import / Restore Settings Workspace (.json)")
        btn_import.clicked.connect(self.import_backup)
        layout.addWidget(btn_import)

        btn_close = QPushButton("Dismiss")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close)

    def export_backup(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Workspace Backup", "", "JSON Backup (*.json)")
        if not file_path:
            return

        try:
            tabs = TabRepository.get_all_tabs()
            accounts = AccountRepository.get_all_accounts()
            
            payload = {
                "version": "1.0.0",
                "tabs": tabs,
                "accounts": accounts
            }
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=4)
                
            QMessageBox.information(self, "Export Completed", f"Successfully backed up configurations to {os.path.basename(file_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Export Failed", f"An error occurred during export: {e}")

    def import_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select SyncHub Workspace Backup", "", "JSON Backup (*.json)")
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Re-map accounts
            accounts_imported = 0
            for acc in data.get("accounts", []):
                AccountRepository.add_account(
                    username=acc["username"],
                    email=acc["email"],
                    encrypted_token=acc["encrypted_token"],
                    avatar_url=acc.get("avatar_url")
                )
                accounts_imported += 1

            # Restore Tabs
            tabs_imported = 0
            for tab in data.get("tabs", []):
                # Strip dynamic ID so SQLite creates new entries cleanly
                if "id" in tab:
                    del tab["id"]
                TabRepository.save_tab(tab)
                tabs_imported += 1

            QMessageBox.information(self, "Import Completed", f"Successfully restored {accounts_imported} accounts and {tabs_imported} tabs from backup.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", f"An error occurred during import: {e}")