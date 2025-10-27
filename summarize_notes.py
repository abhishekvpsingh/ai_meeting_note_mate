# summarize_notes.py
import os
from datetime import datetime
from path_utils import get_project_data_dir, get_logger
from dotenv import load_dotenv
from team_members import load_team_members
from background_knowledge import load_background

load_dotenv()

def _openai_client(provider):
    """Return an OpenAI or Ollama-compatible client."""
    from openai import OpenAI

    if provider == "ollama":        
        # Ollama-compatible endpoint (no proxies arg!)
        return OpenAI(
            base_url="http://localhost:11434/v1",
            api_key="ollama",
        )
    else:
        return OpenAI()


def _build_meeting_prompt(transcript: str, project_name: str, custom_instruction: str | None, team: list[str], background: dict[str, str]) -> str:
    """
    Stronger, role-aware prompt for meeting MOM + status.
    """
    team_section = ", ".join(team) if team else "N/A"
    bg_lines = [f"- {k}: {v}" for k, v in background.items()]
    background_section = "\n".join(bg_lines) if bg_lines else "N/A"

    instruction = custom_instruction.strip() if custom_instruction else (
        "Summarize this meeting like a crisp daily standup note with sections for:"
        "\n- Key Updates per person (use ONLY the team members list; if not mentioned, label as 'Unattributed')"
        "\n- JIRA Tickets mentioned (keep exact IDs like ER-1234, RTWDATA-4567)"
        "\n- Blockers / Risks"
        "\n- Decisions"
        "\n- Action Items (owner & due date if mentioned)\n"
        "Be faithful to the transcript; do not invent names, tickets or facts."
    )

    prompt = f"""
                You are an expert technical PM assistant for the {project_name} project.
                Use this known team and background to attribute updates:

                Team Members: {team_section}
                Team Background:
                {background_section}

                Now read the meeting transcript and produce a structured summary.
                {instruction}

                Transcript:
                {transcript}
            """
    return prompt

def summarize_text(
    transcript: str,
    user_prompt: str | None,
    provider: str = "openai",
    model_name: str | None = None,
    project_name: str = "Datalake"
    ) -> str:
    """
    Summarize a single meeting transcript with project/team context.
    """
    logger = get_logger(project_name)
    team = load_team_members(project_name)
    background = load_background(project_name)

    prompt = _build_meeting_prompt(transcript, project_name, user_prompt, team, background)
    logger.info("Summarizing with provider=%s model=%s (team=%d, bg=%d)", provider, model_name, len(team), len(background))
    logger.debug("Prompt:\n%s", prompt)

    client = _openai_client(provider)

    # Model defaults
    if provider == "ollama":
        model_to_use = model_name or "llama3"
        # OpenAI-compatible client (via OpenAI SDK)
        resp = client.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        result = resp.choices[0].message.content
    else:
        # Official openai legacy (chat.completions)
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise Exception("OpenAI API key is not set in .env")
        model_to_use = model_name or "gpt-4o-mini"
        resp = openai.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        result = resp.choices[0].message.content

    # Persist
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = get_project_data_dir(project_name) / "summaries"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"summary_{ts}.txt"
    with open(out_path, "w") as f:
        f.write(result)

    logger.info("Summary saved: %s", out_path)
    return result


if __name__ == "__main__":

    client = _openai_client("ollama")
    # import openai
    # openai.api_key = os.getenv("OPENAI_API_KEY")
    resp = client.chat.completions.create(
        model="llama3",
        messages=[{"role": "user", "content": "Hello from Meeting Note Mate!"}],
        temperature=0.2,
    )
    print(resp.choices[0].message.content)