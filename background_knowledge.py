# background_knowledge.py
import json
from typing import Dict
from pathlib import Path
from path_utils import get_project_data_dir

def _kb_file(project_name: str) -> Path:
    return get_project_data_dir(project_name) / "team_background.json"

def load_background(project_name: str) -> Dict[str, str]:
    fp = _kb_file(project_name)
    if fp.exists():
        try:
            with open(fp, "r") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # normalize to string:string
                    return {str(k).strip(): str(v).strip() for k, v in data.items() if str(k).strip()}
        except Exception:
            return {}
    return {}

def save_background(project_name: str, mapping: Dict[str, str]) -> None:
    fp = _kb_file(project_name)
    # Only keep non-empty pairs
    clean = {str(k).strip(): str(v).strip() for k, v in mapping.items() if str(k).strip() and str(v).strip()}
    with open(fp, "w") as f:
        json.dump(clean, f, indent=2)
