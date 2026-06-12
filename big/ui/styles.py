class ThemeStyles:
    DARK_STYLESHEET = """
        QMainWindow {
            background-color: #1e1e2e;
        }
        QWidget {
            color: #cdd6f4;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QFrame#Sidebar {
            background-color: #11111b;
            border-right: 1px solid #313244;
        }
        QPushButton {
            background-color: #313244;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 8px 16px;
            color: #cdd6f4;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #45475a;
            border-color: #f5c2e7;
        }
        QPushButton:pressed {
            background-color: #11111b;
        }
        QPushButton#SidebarButton {
            background-color: transparent;
            border: none;
            border-radius: 8px;
            text-align: left;
            padding: 12px;
            font-size: 14px;
        }
        QPushButton#SidebarButton:hover {
            background-color: #313244;
            color: #f5c2e7;
        }
        QPushButton#SidebarButton:checked {
            background-color: #b4befe;
            color: #11111b;
        }
        QTableWidget, QListWidget, QTreeView {
            background-color: #181825;
            border: 1px solid #313244;
            border-radius: 6px;
            gridline-color: #313244;
        }
        QLineEdit, QComboBox, QSpinBox, QTextEdit {
            background-color: #181825;
            border: 1px solid #313244;
            border-radius: 6px;
            padding: 6px;
            color: #cdd6f4;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #b4befe;
        }
        QStatusBar {
            background-color: #11111b;
            color: #a6adc8;
            border-top: 1px solid #313244;
        }
    """

    LIGHT_STYLESHEET = """
        QMainWindow {
            background-color: #f2f2f7;
        }
        QWidget {
            color: #1c1c1e;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 13px;
        }
        QFrame#Sidebar {
            background-color: #e5e5ea;
            border-right: 1px solid #d1d1d6;
        }
        QPushButton {
            background-color: #ffffff;
            border: 1px solid #d1d1d6;
            border-radius: 6px;
            padding: 8px 16px;
            color: #1c1c1e;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #e5e5ea;
            border-color: #007aff;
        }
        QPushButton:pressed {
            background-color: #c7c7cc;
        }
        QPushButton#SidebarButton {
            background-color: transparent;
            border: none;
            border-radius: 8px;
            text-align: left;
            padding: 12px;
            font-size: 14px;
        }
        QPushButton#SidebarButton:hover {
            background-color: #d1d1d6;
            color: #007aff;
        }
        QPushButton#SidebarButton:checked {
            background-color: #007aff;
            color: #ffffff;
        }
        QTableWidget, QListWidget, QTreeView {
            background-color: #ffffff;
            border: 1px solid #d1d1d6;
            border-radius: 6px;
            gridline-color: #e5e5ea;
        }
        QLineEdit, QComboBox, QSpinBox, QTextEdit {
            background-color: #ffffff;
            border: 1px solid #d1d1d6;
            border-radius: 6px;
            padding: 6px;
            color: #1c1c1e;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid #007aff;
        }
        QStatusBar {
            background-color: #e5e5ea;
            color: #48484a;
            border-top: 1px solid #d1d1d6;
        }
    """