from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt
from database.models import TabRepository, AccountRepository, HistoryRepository

class DashboardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title Block
        header = QLabel("SyncHub Control Dashboard")
        header.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(header)

        # Main stats grid layout
        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        
        self.lbl_tabs = self.create_card("Total Active Workspace Tabs", "0")
        self.lbl_accounts = self.create_card("Connected GitHub Profiles", "0")
        self.lbl_logs = self.create_card("Total Synchronization Operations", "0")
        self.lbl_health = self.create_card("Repository Network Status", "Operational")

        self.grid.addWidget(self.lbl_tabs, 0, 0)
        self.grid.addWidget(self.lbl_accounts, 0, 1)
        self.grid.addWidget(self.lbl_logs, 1, 0)
        self.grid.addWidget(self.lbl_health, 1, 1)

        layout.addLayout(self.grid)
        layout.addStretch()

    def create_card(self, title, default_val):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setStyleSheet("""
            QFrame#Card {
                background-color: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
                padding: 16px;
            }
        """)
        card_layout = QVBoxLayout(frame)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("color: #89b4fa; font-weight: bold; font-size: 14px;")
        
        lbl_val = QLabel(default_val)
        lbl_val.setStyleSheet("font-size: 28px; font-weight: bold; margin-top: 8px;")
        lbl_val.setObjectName("val_label")
        
        card_layout.addWidget(lbl_title)
        card_layout.addWidget(lbl_val)
        return frame

    def refresh_stats(self):
        tabs_count = len(TabRepository.get_all_tabs())
        accounts_count = len(AccountRepository.get_all_accounts())
        history_count = len(HistoryRepository.get_all_logs())

        self.lbl_tabs.findChild(QLabel, "val_label").setText(str(tabs_count))
        self.lbl_accounts.findChild(QLabel, "val_label").setText(str(accounts_count))
        self.lbl_logs.findChild(QLabel, "val_label").setText(str(history_count))