from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton, QLabel, QMessageBox
from git_manager.git_wrapper import GitWrapper

class DiffViewerWidget(QWidget):
    def __init__(self, workspace_path=None, parent=None):
        super().__init__(parent)
        self.workspace_path = workspace_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        controls = QHBoxLayout()
        btn_refresh = QPushButton("Refresh Local Difference (Git Diff)")
        btn_refresh.clicked.connect(self.load_diff)
        controls.addWidget(btn_refresh)
        controls.addStretch()
        layout.addLayout(controls)

        self.lbl_info = QLabel("Uncommitted changes detailed view against last local repository state:")
        layout.addWidget(self.lbl_info)

        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        self.viewer.setFontFamily("Courier New")
        self.viewer.setFontPointSize(10)
        layout.addWidget(self.viewer)

    def set_workspace_path(self, path):
        self.workspace_path = path
        self.load_diff()

    def load_diff(self):
        if not self.workspace_path:
            self.viewer.setPlainText("No valid local path provided for comparisons.")
            return

        git = GitWrapper(self.workspace_path)
        if not git.is_repo():
            self.viewer.setPlainText("Path is not flagged as a valid git workspace. Perform synchronization initialization first.")
            return

        diff_text = git.get_diff()
        if not diff_text:
            self.viewer.setHtml("<span style='color: #a6e3a1;'>No changes found! Everything matches the last local commit state.</span>")
            return

        # Format lines for clear diff viewing
        formatted_html = []
        for line in diff_text.splitlines():
            escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            if escaped.startswith("+"):
                formatted_html.append(f"<div style='background-color: #2e3c30; color: #a6e3a1;'>{escaped}</div>")
            elif escaped.startswith("-"):
                formatted_html.append(f"<div style='background-color: #3f2d2f; color: #f38ba8;'>{escaped}</div>")
            elif escaped.startswith("@@"):
                formatted_html.append(f"<div style='color: #cba6f7;'>{escaped}</div>")
            else:
                formatted_html.append(f"<div>{escaped}</div>")

        self.viewer.setHtml("".join(formatted_html))