import os
import datetime
from dotenv import load_dotenv
load_dotenv()

def summarize_text(transcript, user_prompt=None, provider: str = "openai") -> str:
    default_instruction = "Extract key points, action items, and summary in structured format like MOM."
    instruction = user_prompt if user_prompt else default_instruction

    prompt = f"""
    The following is a meeting transcript. {instruction}

    {transcript}
    """

    if provider == "ollama":
        from openai import OpenAI
        MODEL = "llama3"
        openai = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
    else:
        import openai
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise Exception("OpenAI API key is not set in .env")
        MODEL = "gpt-4o"

    print(f"🤖 Using provider: {provider}, model: {MODEL}")
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )
    result = response.choices[0].message.content

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"summaries/summary_{timestamp}.txt", "w") as f:
        f.write(result)

    return result
