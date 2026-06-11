from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QHeaderView
from PySide6.QtCore import Qt
import webbrowser
from database.models import AccountRepository
from github.oauth_manager import OAuthManager
from security.crypt_manager import CryptManager
from notifications.notifier import SystemNotifier

class AccountsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.oauth = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Control Panel Actions
        btn_layout = QHBoxLayout()
        self.btn_login = QPushButton("Add New GitHub Account")
        self.btn_login.clicked.connect(self.initiate_oauth)
        
        self.btn_delete = QPushButton("Remove Selected Profile")
        self.btn_delete.clicked.connect(self.delete_profile)
        
        btn_layout.addWidget(self.btn_login)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Accounts Listing Grid
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["GitHub Username", "Primary Email", "OAuth Access Token Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)

        self.load_profiles()

    def initiate_oauth(self):
        self.oauth = OAuthManager()
        self.oauth.signals.auth_finished.connect(self.handle_oauth_success)
        self.oauth.signals.auth_failed.connect(self.handle_oauth_failure)
        
        url = self.oauth.get_auth_url()
        webbrowser.open(url)
        QMessageBox.information(self, "OAuth Authentication", "Your browser has been opened to GitHub. Complete the log in there to authorize SyncHub.")

    def handle_oauth_success(self, payload):
        encrypted = CryptManager.encrypt(payload["token"])
        AccountRepository.add_account(
            username=payload["username"],
            email=payload["email"],
            encrypted_token=encrypted,
            avatar_url=payload["avatar_url"]
        )
        SystemNotifier.show_message("Profile Linked", f"Authorized successfully as {payload['username']}")
        self.load_profiles()

    def handle_oauth_failure(self, error):
        QMessageBox.critical(self, "Authentication Error", f"OAuth verification loop failed: {error}")

    def load_profiles(self):
        self.table.setRowCount(0)
        accounts = AccountRepository.get_all_accounts()
        for acc in accounts:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(acc["username"]))
            self.table.setItem(row, 1, QTableWidgetItem(acc["email"] or "N/A"))
            self.table.setItem(row, 2, QTableWidgetItem("Active Session Enforced (Encrypted)"))

    def delete_profile(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Selection Required", "Please select a GitHub account row to delete.")
            return

        username = self.table.item(self.table.currentRow(), 0).text()
        confirm = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to remove authorization details for {username}?\nThis cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            accounts = AccountRepository.get_all_accounts()
            for acc in accounts:
                if acc["username"] == username:
                    AccountRepository.delete_account(acc["id"])
                    break
            self.load_profiles()