import os
import sys
from pathlib import Path

def get_base_dir():
    """
    Returns the correct base directory for resources and data,
    whether running from source or a PyInstaller bundle.
    """
    if getattr(sys, 'frozen', False):
        # Running inside .app bundle
        return Path(sys._MEIPASS)
    else:
        # Running in normal dev environment
        return Path(__file__).resolve().parent

def get_user_data_dir():
    """
    Returns a persistent directory in the user's home (for saving files),
    e.g., ~/MeetingNoteMateData
    """
    data_dir = Path.home() / "MeetingNoteMateData"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
