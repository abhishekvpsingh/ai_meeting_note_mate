# team_members.py
import json
from typing import List, Dict
from pathlib import Path
from path_utils import get_project_data_dir

def _team_file(project_name: str) -> Path:
    return get_project_data_dir(project_name) / "team_members.json"

def load_team_members(project_name: str) -> List[str]:
    fp = _team_file(project_name)
    if fp.exists():
        try:
            with open(fp, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return [str(x).strip() for x in data if str(x).strip()]
        except Exception:
            return []
    return []

def save_team_members(project_name: str, members: List[str]) -> None:
    fp = _team_file(project_name)
    with open(fp, "w") as f:
        json.dump([m.strip() for m in members if m.strip()], f, indent=2)
