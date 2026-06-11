import sys
import os
from PySide6.QtWidgets import QApplication
from database.db_connection import DatabaseConnection
from notifications.notifier import SystemNotifier
from ui.mainwindow import MainWindow
from core.logger import logger

def main():
    logger.info("Initializing SyncHub Engine Bootstrap...")
    
    # 1. Start Database Connections and Schema Validations
    try:
        db_connection = DatabaseConnection()
    except Exception as e:
        logger.error(f"Critical error establishing SQL pipelines: {e}")
        sys.exit(1)

    # 2. Run GUI Event Loop
    app = QApplication(sys.argv)
    app.setApplicationName("SyncHub")
    app.setApplicationVersion("1.0.0")

    # 3. Setup OS Notification Traps
    SystemNotifier.initialize(app)

    # 4. Spin main application layout
    window = MainWindow()
    window.show()

    logger.info("SyncHub application successfully booted.")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()