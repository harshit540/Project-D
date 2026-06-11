import os
import sys
import logging
from logging.handlers import RotatingFileHandler

def setup_logger():
    log_dir = os.path.join(os.path.expanduser("~"), ".synchub", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "synchub.log")

    logger = logging.getLogger("SyncHub")
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if re-initialized
    if logger.handlers:
        return logger

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] (%(filename)s:%(lineno)d) - %(message)s')

    # Rotating file handler (10MB per file, max 5 files)
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger

logger = setup_logger()