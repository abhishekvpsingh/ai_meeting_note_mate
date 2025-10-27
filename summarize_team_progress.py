# summarize_team_progress.py
import os
from datetime import datetime, timedelta
from pathlib import Path
from path_utils import get_project_data_dir, get_logger
from dotenv import load_dotenv
from team_members import load_team_members
from background_knowledge import load_background
from html_viewer import show_in_browser

load_dotenv()

def _openai_client(provider: str):
    if provider == "ollama":
        from openai import OpenAI
        return OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    else:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment.")
        return openai

def _load_recent_summaries(project_name: str, days: int = 30) -> list[tuple[str, str]]:
    base = get_project_data_dir(project_name) / "summaries"
    if not base.exists():
        return []
    cutoff = datetime.now() - timedelta(days=days)
    out = []
    for f in base.glob("summary_*.txt"):
        try:
            ts_part = f.stem.replace("summary_", "")
            t = datetime.strptime(ts_part, "%Y%m%d_%H%M%S")
            if t >= cutoff:
                out.append((f.name, f.read_text()))
        except Exception:
            continue
    return out

def summarize_team_progress(project_name: str = "Datalake", provider: str = "openai", model_name: str | None = None) -> str:
    """
    Generate a 30-day team summary by member/tickets for the given project.
    Saves and returns the content; also opens in Chrome.
    """
    logger = get_logger(project_name)
    summaries = _load_recent_summaries(project_name, days=30)
    if not summaries:
        msg = "No past summaries found for this project in last 30 days."
        logger.info(msg)
        return msg

    team = load_team_members(project_name)
    background = load_background(project_name)

    all_text = "\n\n---\n\n".join([s[1] for s in summaries])
    prompt = f"""
You are analyzing daily standups for the {project_name} team over the last 30 days.
Team Members: {", ".join(team) if team else "N/A"}
Background knowledge (per member):
{chr(10).join([f"- {k}: {v}" for k, v in background.items()]) if background else "N/A"}

From the combined summaries below, create a concise roll-up with a Markdown table:

| Team Member | Recent Work (last 30d) | JIRA IDs | Blockers/Notes |
|-------------|-------------------------|----------|----------------|

Rules:
- Attribute updates ONLY to known team members.
- Keep exact JIRA IDs (formats like ABC-1234).
- If no info for a person, write "No explicit updates found".
- Be accurate; do not invent facts.

Combined past summaries:
{all_text}
"""

    client = _openai_client(provider)
    if provider == "ollama":
        model_to_use = model_name or "llama3"
        resp = client.chat.completions.create(
            model=model_to_use, messages=[{"role": "user", "content": prompt}], temperature=0.2
        )
        result = resp.choices[0].message.content
    else:
        import openai as openai_legacy
        model_to_use = model_name or "gpt-4o-mini"
        resp = openai_legacy.chat.completions.create(
            model=model_to_use, messages=[{"role": "user", "content": prompt}], temperature=0.2
        )
        result = resp.choices[0].message.content

    # Save under team_summaries
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = get_project_data_dir(project_name) / "team_summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{project_name.lower()}_summary_{ts}.txt"
    out_path.write_text(result)
    logger.info("Team 30-day summary saved: %s", out_path)

    # Auto-open in Chrome
    show_in_browser(f"{project_name} - 30 Day Team Summary", result)
    return result
