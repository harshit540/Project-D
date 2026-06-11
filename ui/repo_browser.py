from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeView, QFileSystemModel, QLabel
from PySide6.QtCore import QDir

class RepoBrowserWidget(QWidget):
    def __init__(self, workspace_path=None, parent=None):
        super().__init__(parent)
        self.workspace_path = workspace_path
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.lbl_path = QLabel("Active Repository Workspace: " + (self.workspace_path or "No target selected"))
        self.lbl_path.setStyleSheet("font-weight: bold; color: #a6e3a1;")
        self.layout.addWidget(self.lbl_path)

        self.tree = QTreeView()
        self.model = QFileSystemModel()
        self.model.setFilter(QDir.AllDirs | QDir.Files | QDir.NoDotAndDotDot)
        self.tree.setModel(self.model)
        
        if self.workspace_path:
            self.set_active_path(self.workspace_path)
            
        self.layout.addWidget(self.tree)

    def set_active_path(self, path):
        self.workspace_path = path
        self.lbl_path.setText(f"Active Repository Workspace: {path}")
        self.model.setRootPath(path)
        self.tree.setRootIndex(self.model.index(path))