from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit, QComboBox, QSpinBox, QPushButton, QFileDialog, QMessageBox, QLabel, QCheckBox
from database.models import TabRepository, AccountRepository

class TabConfigWidget(QWidget):
    def __init__(self, tab_data=None, parent=None):
        super().__init__(parent)
        self.tab_id = tab_data["id"] if tab_data else None
        self.init_ui()
        if tab_data:
            self.populate_data(tab_data)

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.txt_name = QLineEdit()
        form.addRow("Visual Tab Name:", self.txt_name)

        # Folder Selection Row
        row_folder = QHBoxLayout()
        self.txt_path = QLineEdit()
        self.btn_browse = QPushButton("Browse Folder")
        self.btn_browse.clicked.connect(self.browse_folder)
        row_folder.addWidget(self.txt_path)
        row_folder.addWidget(self.btn_browse)
        form.addRow("Local Folder Path:", row_folder)

        self.cmb_account = QComboBox()
        self.refresh_accounts_dropdown()
        form.addRow("Linked GitHub Profile:", self.cmb_account)

        self.txt_repo = QLineEdit()
        form.addRow("Remote Repo Name:", self.txt_repo)

        self.txt_branch = QLineEdit("main")
        form.addRow("Synchronized Branch:", self.txt_branch)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["manual", "scheduled"])
        form.addRow("Synchronization Strategy:", self.cmb_mode)

        self.spin_interval = QSpinBox()
        self.spin_interval.setRange(30, 86400)
        self.spin_interval.setSuffix(" Seconds")
        self.spin_interval.setValue(300)
        form.addRow("Sync Interval:", self.spin_interval)

        self.txt_template = QLineEdit("Auto Sync - {datetime}")
        form.addRow("Commit Message Schema:", self.txt_template)

        self.chk_notif = QCheckBox("Enable Status Action Notifications")
        self.chk_notif.setChecked(True)
        form.addRow("Notifications:", self.chk_notif)

        self.spin_history = QSpinBox()
        self.spin_history.setRange(5, 100)
        self.spin_history.setValue(20)
        form.addRow("Log Retention Limit:", self.spin_history)

        self.txt_exe_watcher = QLineEdit()
        self.txt_exe_watcher.setPlaceholderText("e.g. obsidian.exe")
        form.addRow("Executable Watcher:", self.txt_exe_watcher)

        self.cmb_trigger_open = QComboBox()
        self.cmb_trigger_open.addItems(["Do Nothing", "Pull", "Ask User"])
        form.addRow("Action on Process Opened:", self.cmb_trigger_open)

        self.cmb_trigger_close = QComboBox()
        self.cmb_trigger_close.addItems(["Do Nothing", "Push", "Ask User"])
        form.addRow("Action on Process Closed:", self.cmb_trigger_close)

        self.cmb_conflict = QComboBox()
        self.cmb_conflict.addItems(["Auto Resolve", "Manual Resolve", "Visual Compare"])
        form.addRow("Merge Conflict Strategy:", self.cmb_conflict)

        layout.addLayout(form)

        # Control Row
        actions = QHBoxLayout()
        self.btn_save = QPushButton("Save Config Settings")
        self.btn_save.clicked.connect(self.save_settings)
        actions.addWidget(self.btn_save)
        actions.addStretch()
        layout.addLayout(actions)

    def browse_folder(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Sync Target Directory")
        if dir_path:
            self.txt_path.setText(dir_path)

    def refresh_accounts_dropdown(self):
        self.cmb_account.clear()
        self.accounts_map = AccountRepository.get_all_accounts()
        for acc in self.accounts_map:
            self.cmb_account.addItem(acc["username"], acc["id"])

    def populate_data(self, d):
        self.txt_name.setText(d.get("name", ""))
        self.txt_path.setText(d.get("folder_path", ""))
        self.txt_repo.setText(d.get("repo_name", ""))
        self.txt_branch.setText(d.get("branch", "main"))
        self.cmb_mode.setCurrentText(d.get("sync_mode", "manual"))
        self.spin_interval.setValue(d.get("sync_interval", 300))
        self.txt_template.setText(d.get("commit_msg_template", "Auto Sync - {datetime}"))
        self.chk_notif.setChecked(bool(d.get("notifications_enabled", 1)))
        self.spin_history.setValue(d.get("history_limit", 20))
        self.txt_exe_watcher.setText(d.get("app_trigger_exe", ""))
        self.cmb_trigger_open.setCurrentText(d.get("app_trigger_on_open", "Do Nothing"))
        self.cmb_trigger_close.setCurrentText(d.get("app_trigger_on_close", "Do Nothing"))
        self.cmb_conflict.setCurrentText(d.get("conflict_resolution_mode", "Auto Resolve"))

        idx = self.cmb_account.findData(d.get("account_id"))
        if idx >= 0:
            self.cmb_account.setCurrentIndex(idx)

    def save_settings(self):
        if not self.txt_name.text() or not self.txt_path.text() or not self.txt_repo.text():
            QMessageBox.critical(self, "Save Denied", "Visual Name, Target Path, and Remote Repo are mandatory fields.")
            return

        payload = {
            "id": self.tab_id,
            "name": self.txt_name.text(),
            "folder_path": self.txt_path.text(),
            "account_id": self.cmb_account.currentData(),
            "repo_name": self.txt_repo.text(),
            "branch": self.txt_branch.text(),
            "sync_mode": self.cmb_mode.currentText(),
            "sync_interval": self.spin_interval.value(),
            "commit_msg_template": self.txt_template.text(),
            "notifications_enabled": 1 if self.chk_notif.isChecked() else 0,
            "history_limit": self.spin_history.value(),
            "app_trigger_exe": self.txt_exe_watcher.text(),
            "app_trigger_on_open": self.cmb_trigger_open.currentText(),
            "app_trigger_on_close": self.cmb_trigger_close.currentText(),
            "conflict_resolution_mode": self.cmb_conflict.currentText()
        }
        
        saved_id = TabRepository.save_tab(payload)
        self.tab_id = saved_id
        QMessageBox.information(self, "Success", "Workspace configuration successfully updated in the database.")


def refresh_accounts_dropdown(self):
        # અત્યારે સિલેક્ટ કરેલી વેલ્યુ યાદ રાખો
        current_data = self.cmb_account.currentData()
        
        self.cmb_account.clear()
        self.accounts_map = AccountRepository.get_all_accounts()
        for acc in self.accounts_map:
            self.cmb_account.addItem(acc["username"], acc["id"])
            
        # જો કોઈ ડેટા અગાઉથી સિલેક્ટ હતો, તો તેને ફરીથી સેટ કરો
        if current_data is not None:
            idx = self.cmb_account.findData(current_data)
            if idx >= 0:
                self.cmb_account.setCurrentIndex(idx)