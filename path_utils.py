# path_utils.py
import os
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

APP_ROOT_DIRNAME = "MeetingNoteMateData"
APP_LOGGER_NAME = "MeetingNoteMate"

def get_base_dir() -> Path:
    """Return the base dir for resources, both source and PyInstaller bundle."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent

def get_user_data_dir() -> Path:
    """
    Returns the persistent base directory in the user's home, e.g., ~/MeetingNoteMateData
    """
    data_dir = Path.home() / APP_ROOT_DIRNAME
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

def get_project_data_dir(project_name: str) -> Path:
    """
    Returns ~/MeetingNoteMateData/<ProjectName>
    Ensures the standard subfolders exist.
    """
    p = get_user_data_dir() / project_name
    (p / "audio_files").mkdir(parents=True, exist_ok=True)
    (p / "transcripts").mkdir(parents=True, exist_ok=True)
    (p / "summaries").mkdir(parents=True, exist_ok=True)
    (p / "team_summaries").mkdir(parents=True, exist_ok=True)
    (p / "logs").mkdir(parents=True, exist_ok=True)
    return p

def _logger_file_handler(project_name: str) -> RotatingFileHandler:
    log_dir = get_project_data_dir(project_name) / "logs"
    logfile = log_dir / "app.log"
    handler = RotatingFileHandler(logfile, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(fmt)
    return handler

def get_logger(project_name: str) -> logging.Logger:
    """
    Returns a project-scoped logger.
    If project_name == 'Tests' -> DEBUG (very chatty).
    Else -> INFO (concise).
    """
    logger = logging.getLogger(f"{APP_LOGGER_NAME}.{project_name}")
    # Avoid duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    level = logging.DEBUG if project_name.strip().lower() == "tests" else logging.INFO
    logger.setLevel(level)

    # File handler
    fh = _logger_file_handler(project_name)
    logger.addHandler(fh)

    # Console handler in Tests only (helpful while iterating)
    if level == logging.DEBUG:
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(message)s"))
        logger.addHandler(ch)

    logger.propagate = False
    logger.debug("Logger initialized for project '%s' with level %s", project_name, logging.getLevelName(level))
    return logger
