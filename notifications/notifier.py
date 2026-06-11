from PySide6.QtWidgets import QSystemTrayIcon
from PySide6.QtGui import QIcon
from core.settings_manager import SettingsManager

class SystemNotifier:
    _tray_icon = None

    @classmethod
    def initialize(cls, parent_app):
        if cls._tray_icon is None:
            # Use a basic fallback layout if resource icons are missing
            cls._tray_icon = QSystemTrayIcon(parent_app)
            cls._tray_icon.setIcon(QIcon.fromTheme("system-run"))
            cls._tray_icon.show()

    @classmethod
    def show_message(cls, title: str, message: str, icon=QSystemTrayIcon.Information):
        if not SettingsManager.get_notifications_enabled():
            return
        if cls._tray_icon:
            cls._tray_icon.showMessage(title, message, icon, 3500)