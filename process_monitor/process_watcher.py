import os
import subprocess
from PySide6.QtCore import QThread, Signal
from core.logger import logger

class ProcessWatcher(QThread):
    process_started = Signal(str) # process_name
    process_stopped = Signal(str) # process_name

    def __init__(self, target_executables: list, poll_interval_secs: int = 5):
        super().__init__()
        self.target_executables = [exe.lower() for exe in target_executables]
        self.poll_interval = poll_interval_secs
        self.running = True
        self.active_processes = set()

    def run(self):
        logger.info(f"Starting Process Watcher. Monitoring: {self.target_executables}")
        while self.running:
            current_running = self._get_running_processes()
            
            # Detect launches
            for exe in self.target_executables:
                if exe in current_running and exe not in self.active_processes:
                    self.active_processes.add(exe)
                    self.process_started.emit(exe)
                    logger.debug(f"Detected process launch: {exe}")

            # Detect closures
            stopped = []
            for exe in self.active_processes:
                if exe not in current_running:
                    stopped.append(exe)
                    self.process_stopped.emit(exe)
                    logger.debug(f"Detected process termination: {exe}")

            for exe in stopped:
                self.active_processes.remove(exe)

            self.msleep(self.poll_interval * 1000)

    def _get_running_processes(self) -> set:
        running = set()
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            # Check running tasks on Windows
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                startupinfo=startupinfo,
                timeout=5
            )
            for line in result.stdout.splitlines():
                if line.strip():
                    parts = line.split(",")
                    if parts:
                        exe_name = parts[0].strip('"').lower()
                        running.add(exe_name)
        except Exception as e:
            logger.error(f"Error querying process monitor list: {e}")
        return running

    def stop(self):
        self.running = False