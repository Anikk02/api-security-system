import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
import os

LOG_DIR = "logs_data"
LOG_FILE = os.path.join(LOG_DIR, "app.log")

os.makedirs(LOG_DIR, exist_ok=True)


def setup_logging():
    root_logger = logging.getLogger()

    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    root_logger.setLevel(log_level)

    # Prevent duplicate handlers (important in FastAPI reload)
    if root_logger.handlers:
        return root_logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    # 🖥️ Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # 📁 File Handler (Rotating)
    file_handler = ConcurrentRotatingFileHandler(
        LOG_FILE,
        maxBytes=1024 * 1024,   # 1 MB
        backupCount=3
    )
    file_handler.setFormatter(formatter)

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    return root_logger