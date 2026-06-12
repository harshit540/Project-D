from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QPushButton, QStackedWidget, QTabWidget, QStatusBar, QMessageBox, QLabel, QInputDialog
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QAction
from core.settings_manager import SettingsManager
from ui.styles import ThemeStyles
from ui.dashboard import DashboardWidget
from ui.accounts import AccountsWidget
from ui.tab_config import TabConfigWidget
from ui.repo_browser import RepoBrowserWidget
from ui.diff_viewer import DiffViewerWidget
from ui.dialogs import BackupManagerDialog, CreateRepoDialog
from database.models import TabRepository, AccountRepository, HistoryRepository
from sync_engine.queue_manager import QueueManager
from process_monitor.process_watcher import ProcessWatcher
from notifications.notifier import SystemNotifier

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SyncHub Core Engine")
        self.resize(1100, 750)
        self.queue_manager = QueueManager()
        self.process_watcher = None
        
        self.init_ui()
        self.apply_theme()
        
        # Connect Sync Engines signals
        self.queue_manager.tab_sync_started.connect(self.handle_sync_started)
        self.queue_manager.tab_sync_finished.connect(self.handle_sync_finished)
        self.queue_manager.start_schedulers()

        self.start_process_watcher()

    def init_ui(self):
        main_central = QWidget()
        self.setCentralWidget(main_central)
        main_layout = QHBoxLayout(main_central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Navigation Sidebar panel setup
        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 20, 10, 20)
        sidebar_layout.setSpacing(10)

        # App Logo Brand Header
        lbl_logo = QLabel("SyncHub")
        lbl_logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #b4befe; padding-left: 10px; margin-bottom: 20px;")
        sidebar_layout.addWidget(lbl_logo)

        # Nav Elements
        self.btn_dash = QPushButton("  Dashboard")
        self.btn_dash.setObjectName("SidebarButton")
        self.btn_dash.setCheckable(True)
        self.btn_dash.setChecked(True)
        self.btn_dash.clicked.connect(lambda: self.switch_view(0))

        self.btn_accounts = QPushButton("  GitHub Profiles")
        self.btn_accounts.setObjectName("SidebarButton")
        self.btn_accounts.setCheckable(True)
        self.btn_accounts.clicked.connect(lambda: self.switch_view(1))

        self.btn_workspaces = QPushButton("  Sync Workspaces")
        self.btn_workspaces.setObjectName("SidebarButton")
        self.btn_workspaces.setCheckable(True)
        self.btn_workspaces.clicked.connect(lambda: self.switch_view(2))

        self.btn_backup = QPushButton("  Configuration Backup")
        self.btn_backup.setObjectName("SidebarButton")
        self.btn_backup.clicked.connect(self.open_backup_dialog)

        sidebar_layout.addWidget(self.btn_dash)
        sidebar_layout.addWidget(self.btn_accounts)
        sidebar_layout.addWidget(self.btn_workspaces)
        sidebar_layout.addWidget(self.btn_backup)
        sidebar_layout.addStretch()

        # Dynamic Sidebar Nav Button Check states
        self.nav_buttons = [self.btn_dash, self.btn_accounts, self.btn_workspaces]

        main_layout.addWidget(self.sidebar)

        # 2. Main Work Stack
        self.stack = QStackedWidget()
        
        self.view_dash = DashboardWidget()
        self.view_accounts = AccountsWidget()
        
        # Workspace dynamic tab shell creation
        self.view_workspaces = QWidget()
        work_layout = QVBoxLayout(self.view_workspaces)
        self.workspace_tabs = QTabWidget()
        self.workspace_tabs.setTabsClosable(True)
        self.workspace_tabs.tabCloseRequested.connect(self.close_tab_request)
        
        # Add a placeholder/plus button inside workspace tab
        self.btn_add_tab = QPushButton("Add New Sync Workspace")
        self.btn_add_tab.clicked.connect(self.create_new_workspace_tab)
        work_layout.addWidget(self.btn_add_tab)
        work_layout.addWidget(self.workspace_tabs)

        self.stack.addWidget(self.view_dash)
        self.stack.addWidget(self.view_accounts)
        self.stack.addWidget(self.view_workspaces)

        main_layout.addWidget(self.stack)

        # 3. Status Bar Indicators
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("SyncHub engine ready.")

        # Load workspace tabs config from database
        self.load_all_tabs_from_db()

    def switch_view(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 0:
            self.view_dash.refresh_stats()

    def open_backup_dialog(self):
        dlg = BackupManagerDialog(self)
        if dlg.exec():
            self.load_all_tabs_from_db()
            self.view_accounts.load_profiles()
            self.queue_manager.start_schedulers()

    def apply_theme(self):
        theme = SettingsManager.get_theme()
        if theme == "Dark":
            self.setStyleSheet(ThemeStyles.DARK_STYLESHEET)
        else:
            self.setStyleSheet(ThemeStyles.LIGHT_STYLESHEET)

    def load_all_tabs_from_db(self):
        # Clear workspaces
        self.workspace_tabs.clear()
        tabs = TabRepository.get_all_tabs()
        accounts = {a["id"]: a for a in AccountRepository.get_all_accounts()}

        for tab in tabs:
            self.add_workspace_tab_widget(tab, accounts.get(tab["account_id"]))

    def add_workspace_tab_widget(self, tab_data, account_data):
        if self.workspace_tabs.count() >= 100:
            QMessageBox.critical(self, "Maximum Reached", "A max limit of 100 operational active tabs is enforced.")
            return

        tab_shell = QWidget()
        tab_layout = QVBoxLayout(tab_shell)

        # Action bar inside the tab
        action_bar = QHBoxLayout()
        btn_sync = QPushButton("Sync Action")
        btn_sync.clicked.connect(lambda: self.run_tab_sync(tab_data, account_data, "sync"))
        
        btn_pull = QPushButton("Force Pull")
        btn_pull.setStyleSheet("color: #a6e3a1;")
        btn_pull.clicked.connect(lambda: self.run_tab_sync(tab_data, account_data, "pull"))

        btn_push = QPushButton("Force Push")
        btn_push.setStyleSheet("color: #f38ba8;")
        btn_push.clicked.connect(lambda: self.run_tab_sync(tab_data, account_data, "push"))

        btn_create_repo = QPushButton("Create Remote Repo")
        btn_create_repo.clicked.connect(lambda: self.create_remote_repo_action(account_data))

        action_bar.addWidget(btn_sync)
        action_bar.addWidget(btn_pull)
        action_bar.addWidget(btn_push)
        action_bar.addWidget(btn_create_repo)
        action_bar.addStretch()
        tab_layout.addLayout(action_bar)

        # Dynamic nested views: Config Settings, Explorer Browser, Diff visualizer
        nested_tabs = QTabWidget()
        config_view = TabConfigWidget(tab_data)
        explorer_view = RepoBrowserWidget(tab_data["folder_path"])
        diff_view = DiffViewerWidget(tab_data["folder_path"])

        nested_tabs.addTab(config_view, "Config Settings")
        nested_tabs.addTab(explorer_view, "Explorer Browser")
        nested_tabs.addTab(diff_view, "Diff View")

        tab_layout.addWidget(nested_tabs)
        self.workspace_tabs.addTab(tab_shell, tab_data["name"])

    def create_new_workspace_tab(self):
        name, ok = QInputDialog.getText(self, "New Sync Workspace", "Enter workspace name:")
        if ok and name.strip():
            new_tab_payload = {
                "name": name.strip(),
                "folder_path": "",
                "account_id": None,
                "repo_name": "",
                "branch": "main",
                "sync_mode": "manual",
                "sync_interval": 300,
                "commit_msg_template": "Auto Sync - {datetime}",
                "notifications_enabled": 1,
                "history_limit": 20,
                "app_trigger_exe": "",
                "app_trigger_on_open": "Do Nothing",
                "app_trigger_on_close": "Do Nothing",
                "conflict_resolution_mode": "Auto Resolve"
            }
            new_id = TabRepository.save_tab(new_tab_payload)
            new_tab_payload["id"] = new_id
            self.add_workspace_tab_widget(new_tab_payload, None)
            self.queue_manager.start_schedulers()

    def close_tab_request(self, index):
        confirm = QMessageBox.question(
            self, "Confirm Closure",
            "Are you sure you want to delete this tab configuration from SyncHub?\nThis will NOT delete your local directories or remote repository files.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            tabs = TabRepository.get_all_tabs()
            if index < len(tabs):
                tab_id = tabs[index]["id"]
                TabRepository.delete_tab(tab_id)
                self.workspace_tabs.removeTab(index)
                self.queue_manager.start_schedulers()

    def run_tab_sync(self, tab, account, mode):
        if not account:
            QMessageBox.critical(self, "No Profile Linked", "Please link and choose a valid GitHub Profile for this tab workspace configuration.")
            return
        self.status_bar.showMessage(f"Initiating {mode} workflow for workspace {tab['name']}...")
        self.queue_manager.trigger_sync(tab, account, force_mode=mode)

    def handle_sync_started(self, tab_id):
        self.status_bar.showMessage(f"Working on sync processes for Workspace ID: {tab_id}...")

    def handle_sync_finished(self, tab_id, success, msg):
        status_text = "Successful" if success else "Failed"
        self.status_bar.showMessage(f"Workspace {tab_id} sync result: {status_text} - {msg}")
        
        # Pop system notification
        SystemNotifier.show_message(
            f"SyncHub Workspace Action: {status_text}",
            f"ID: {tab_id} finished execution with results: {msg}"
        )

    def create_remote_repo_action(self, account_data):
        if not account_data:
            QMessageBox.warning(self, "Profile Required", "Select and save a GitHub account profile to host repositories.")
            return
        dlg = CreateRepoDialog(account_data, self)
        dlg.exec()

    def start_process_watcher(self):
        tabs = TabRepository.get_all_tabs()
        targets = [t["app_trigger_exe"] for t in tabs if t.get("app_trigger_exe")]
        if not targets:
            return

        self.process_watcher = ProcessWatcher(targets)
        self.process_watcher.process_started.connect(self.handle_watched_process_start)
        self.process_watcher.process_stopped.connect(self.handle_watched_process_stop)
        self.process_watcher.start()

    def handle_watched_process_start(self, exe):
        self.status_bar.showMessage(f"Detected monitored process launched: {exe}")
        # Identify matching workspaces
        tabs = TabRepository.get_all_tabs()
        accounts = {a["id"]: a for a in AccountRepository.get_all_accounts()}
        for tab in tabs:
            if tab["app_trigger_exe"] and tab["app_trigger_exe"].lower() == exe:
                action = tab["app_trigger_on_open"]
                if action == "Pull":
                    self.run_tab_sync(tab, accounts.get(tab["account_id"]), "pull")
                elif action == "Ask User":
                    ans = QMessageBox.question(self, "Detected Application Action", f"Process {exe} launched. Pull updates for {tab['name']} workspace?", QMessageBox.Yes | QMessageBox.No)
                    if ans == QMessageBox.Yes:
                        self.run_tab_sync(tab, accounts.get(tab["account_id"]), "pull")

    def handle_watched_process_stop(self, exe):
        self.status_bar.showMessage(f"Detected monitored process terminated: {exe}")
        tabs = TabRepository.get_all_tabs()
        accounts = {a["id"]: a for a in AccountRepository.get_all_accounts()}
        for tab in tabs:
            if tab["app_trigger_exe"] and tab["app_trigger_exe"].lower() == exe:
                action = tab["app_trigger_on_close"]
                if action == "Push":
                    self.run_tab_sync(tab, accounts.get(tab["account_id"]), "push")
                elif action == "Ask User":
                    ans = QMessageBox.question(self, "Detected Application Action", f"Process {exe} was closed. Push modifications for {tab['name']} workspace?", QMessageBox.Yes | QMessageBox.No)
                    if ans == QMessageBox.Yes:
                        self.run_tab_sync(tab, accounts.get(tab["account_id"]), "push")




def switch_view(self, index):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)
        if index == 0:
            self.view_dash.refresh_stats()
        elif index == 2:
            # જ્યારે વર્કસ્પેસ ટેબ ખોલવામાં આવે ત્યારે ડ્રોપડાઉન ઓટો-રિફ્રેશ કરો
            for idx in range(self.workspace_tabs.count()):
                tab_shell = self.workspace_tabs.widget(idx)
                # ટેબની અંદર રહેલા TabConfigWidget ને શોધો અને રિફ્રેશ કરો
                config_widget = tab_shell.findChild(TabConfigWidget)
                if config_widget:
                    config_widget.refresh_accounts_dropdown()