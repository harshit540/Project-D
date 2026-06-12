from PySide6.QtCore import QObject, QTimer, Signal
from database.models import TabRepository, AccountRepository
from sync_engine.sync_worker import SyncWorker
from core.logger import logger

class QueueManager(QObject):
    tab_sync_started = Signal(int)
    tab_sync_finished = Signal(int, bool, str)

    def __init__(self):
        super().__init__()
        self.timers = {}
        self.active_workers = {}

    def start_schedulers(self):
        self.stop_schedulers()
        tabs = TabRepository.get_all_tabs()
        accounts = {a["id"]: a for a in AccountRepository.get_all_accounts()}

        for tab in tabs:
            if tab["sync_mode"] == "scheduled" and tab["sync_interval"] > 0:
                tab_id = tab["id"]
                interval_ms = tab["sync_interval"] * 1000
                
                # Create and start a timer for each tab with scheduled syncing enabled
                timer = QTimer(self)
                timer.timeout.connect(lambda t=tab, acc=accounts.get(tab["account_id"]): self.trigger_sync(t, acc))
                timer.start(interval_ms)
                self.timers[tab_id] = timer
                logger.info(f"Registered scheduled timer for Tab {tab_id} every {tab['sync_interval']} seconds.")

    def stop_schedulers(self):
        for timer in self.timers.values():
            timer.stop()
        self.timers.clear()

    def trigger_sync(self, tab, account, force_mode="sync"):
        tab_id = tab["id"]
        if tab_id in self.active_workers:
            logger.info(f"Sync already running for tab {tab_id}. Skipping.")
            return

        worker = SyncWorker(tab, account, force_mode)
        worker.sync_started.connect(self.tab_sync_started.emit)
        worker.sync_finished.connect(lambda tid, success, msg: self._on_sync_finished(tid, success, msg))
        
        self.active_workers[tab_id] = worker
        worker.start()

    def _on_sync_finished(self, tab_id, success, message):
        if tab_id in self.active_workers:
            self.active_workers[tab_id].deleteLater()
            del self.active_workers[tab_id]
        self.tab_sync_finished.emit(tab_id, success, message)