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

    # ---- Strong default instruction ----
    instruction = (
        custom_instruction.strip()
        if custom_instruction
        else (
            "You are a senior project analyst summarizing a team meeting for project leadership.\n"
            "Your goal is to produce a highly structured and faithful summary with the following sections:\n\n"
            "1. **Meeting Overview** – Context, main theme, and objective of discussion.\n"
            "2. **Detailed Team Member Updates** – For each person in the known team list below:\n"
            "     - Identify their spoken parts and summarize their work updates, blockers, and next actions.\n"
            "     - Include all JIRA or ticket numbers they mention (like RTWDATA-1234, ER-5678) under their section.\n"
            "     - If they are not mentioned, list them as '(No update shared)'.\n"
            "     - Keep summaries descriptive (3–5 lines per person if possible).\n"
            "3. **JIRA / Ticket Summary** – Group all ticket IDs mentioned and summarize current progress, blockers, or ownership per ticket.\n"
            "4. **Decisions Made** – Explicit decisions or agreements noted during the call.\n"
            "5. **Risks / Blockers** – Technical or resource issues raised.\n"
            "6. **Action Items** – Concrete next steps, with owners and due dates if discussed.\n\n"
            "Guidelines:\n"
            "- Extract factual details only. Avoid speculation.\n"
            "- Retain all numeric IDs (tickets, story numbers, release identifiers).\n"
            "- Be concise but detailed; this summary should be readable as an internal status report.\n"
            "- Use markdown formatting and bullet lists for readability."
        )
    )

    prompt = f"""
                You are an expert technical project assistant summarizing a meeting for the **{project_name}** project.

                Known Team Members:
                {team_section}

                Project / Technical Background:
                {background_section}

                Meeting Transcript:
                \"\"\"{transcript}\"\"\"

                {instruction}

                Ensure your response follows the exact section order above and uses markdown.
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
    
    # Clean transcript (remove noise, normalize spaces)
    transcript = transcript.replace("  ", " ").replace("\n\n", "\n").strip()

    prompt = _build_meeting_prompt(transcript, project_name, user_prompt, team, background)
    logger.info("Summarizing with provider=%s model=%s (team=%d, bg=%d)", provider, model_name, len(team), len(background))
    logger.info("Prompt:\n%s", prompt)

    client = _openai_client(provider)

    # Model defaults
    if provider == "ollama":
        model_to_use = model_name or "llama3"
        # OpenAI-compatible client (via OpenAI SDK)
        resp = client.chat.completions.create(
            model=model_to_use,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
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
            temperature=0.25,
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