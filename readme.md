
```markdown
# Meeting Note Mate

**Meeting Note Mate** is a local Mac-based AI-powered application that records audio, transcribes it using Whisper, and summarizes the transcript into structured meeting notes (MoM). It comes with a modern GUI built using `ttkbootstrap` and supports both **OpenAI** and **Ollama (LLaMA)** as LLM backends.

---

## Features

- 🎤 Record meeting audio from mic
- 📁 Load existing `.wav` files
- 🧠 Transcribe audio using `faster-whisper`
- ✨ Summarize transcripts using LLMs (OpenAI or Ollama)
- 🖥️ GUI built with `Tkinter + ttkbootstrap`
- 🔐 API key management and provider switch (OpenAI or Ollama)
- 📂 Saves transcripts and summaries automatically
- 💻 Works fully offline with Ollama

---

## Project Structure

```

meeting\_note\_mate\_v3/
├── audio\_files/       # Recorded audio (.wav)
├── transcripts/       # Saved transcripts
├── summaries/         # Summarized notes
├── record\_audio.py
├── transcribe\_audio.py
├── summarize\_notes.py
├── gui\_app.py         # Main app GUI
├── requirements.txt
├── setup\_project.sh   # ⬅️ One-step setup script
└── .env               # (created on first use if OpenAI selected)

````

---

## ⚙️ Setup Instructions

### Step 1: Run the setup script

Make sure you have **Python 3.8+** installed (preferably via `python.org` or `brew`, not Anaconda).

In your terminal:

```bash
curl -O https://raw.githubusercontent.com/your-repo/meeting_note_mate_v3/main/setup_project.sh
chmod +x setup_project.sh
./setup_project.sh
````

This script will:

* Create the project folder
* Set up a virtual environment
* Install required packages
* Generate the source code and GUI

---

## How to Run the App

Once setup is complete:

```bash
cd meeting_note_mate
source note-env/bin/activate
python gui_app.py
```

---

## Supported LLM Providers

### OpenAI

* Requires an OpenAI API key
* You'll be prompted to enter it once and it will be saved to `.env`

### Ollama (local model)

* Must have [Ollama](https://ollama.com) running locally
* No API key required
* Recommended model: `llama3` or `mistral`

---

## Requirements

* `Python 3.8+`
* `faster-whisper`
* `openai`
* `sounddevice`, `scipy`, `pydub`
* `python-dotenv`
* `ttkbootstrap`
* Optional: `ollama` running locally

> All dependencies are auto-installed during the setup.

---

## Customization

* You can edit `summarize_notes.py` to change the summarization prompt.
* Transcripts and summaries are saved with timestamps for easy tracking.

---

## Notes

* Audio is saved in `audio_files/`
* Transcripts in `transcripts/`
* Summaries in `summaries/`
* You can record new audio or use an existing `.wav` file.

---


## Questions or Help?

Feel free to open an issue or message me directly for support.

```