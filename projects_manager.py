# projects_manager.py
import json
from typing import List
from pathlib import Path
from path_utils import get_user_data_dir

PROJECT_FILE = get_user_data_dir() / "projects.json"
DEFAULT_PROJECTS = ["Datalake", "General"]

def load_projects() -> List[str]:
    if PROJECT_FILE.exists():
        try:
            with open(PROJECT_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list) and data:
                    # Ensure no empties, unique, preserve order
                    out = []
                    seen = set()
                    for p in data:
                        p = str(p).strip()
                        if p and p not in seen:
                            seen.add(p)
                            out.append(p)
                    return out
        except Exception:
            pass
    # Write defaults if file missing/corrupt
    save_projects(DEFAULT_PROJECTS)
    return DEFAULT_PROJECTS[:]

def save_projects(projects: List[str]) -> None:
    clean = []
    seen = set()
    for p in projects:
        p = str(p).strip()
        if p and p not in seen:
            seen.add(p)
            clean.append(p)
    with open(PROJECT_FILE, "w") as f:
        json.dump(clean, f, indent=2)
