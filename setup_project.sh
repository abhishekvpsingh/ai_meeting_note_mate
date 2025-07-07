#!/bin/bash

PROJECT_DIR="meeting_note_mate_v3"
ENV_NAME="note-env"

echo "📁 Creating project structure..."
mkdir -p $PROJECT_DIR/{audio_files,transcripts,summaries}

cd $PROJECT_DIR

echo "📝 Creating requirements.txt..."
cat <<EOF > requirements.txt
sounddevice==0.4.6
scipy
openai
faster-whisper==0.10.0
pydub
python-dotenv==1.0.1
ttkbootstrap
EOF

echo "🌱 Setting up virtual environment..."
python3 -m venv $ENV_NAME
source $ENV_NAME/bin/activate

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "📂 Creating Python source files..."

# record_audio.py
cat <<EOF > record_audio.py
import sounddevice as sd
from scipy.io.wavfile import write
import datetime
import numpy as np
import threading

frames = []
recording = False

def callback(indata, frames_count, time, status):
    if status:
        print(status)
    frames.append(indata.copy())

def start_recording(samplerate=44100):
    global recording, frames
    recording = True
    frames = []
    print("🔴 Recording started...")
    threading.Thread(target=_record, args=(samplerate,), daemon=True).start()

def _record(samplerate):
    global recording
    with sd.InputStream(callback=callback, channels=1, samplerate=samplerate):
        while recording:
            sd.sleep(100)

def stop_recording(samplerate=44100):
    global recording
    recording = False
    audio_data = np.concatenate(frames, axis=0)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audio_files/meeting_{timestamp}.wav"
    write(filename, samplerate, audio_data)
    print(f"💾 Audio saved to {filename}")
    return filename
EOF

# transcribe_audio.py
cat <<EOF > transcribe_audio.py
from faster_whisper import WhisperModel
import datetime

def transcribe_audio(audio_path):
    model = WhisperModel("base", compute_type="int8")
    segments, info = model.transcribe(audio_path)

    transcript = ""
    for segment in segments:
        transcript += segment.text + " "

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"transcripts/transcript_{timestamp}.txt", "w") as f:
        f.write(transcript.strip())

    print("📝 Transcription complete.")
    return transcript.strip()
EOF

# summarize_notes.py
cat <<EOF > summarize_notes.py
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
EOF

# gui_app.py
cat <<EOF > gui_app.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, simpledialog, messagebox
import os
from dotenv import load_dotenv, set_key
from record_audio import start_recording, stop_recording
from transcribe_audio import transcribe_audio
from summarize_notes import summarize_text

load_dotenv()

class MeetingNoteMateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Meeting Note Mate - AI Notetaker")
        self.root.geometry("1000x700")
        self.provider = tb.StringVar(value="openai")

        self.style = tb.Style("cosmo")

        main_frame = tb.Frame(root, padding=20)
        main_frame.pack(fill=BOTH, expand=True)

        # Title
        tb.Label(main_frame, text="Meeting Note Mate", font=("Helvetica", 24, "bold")).pack(pady=(0, 20))

        # Top buttons and input
        controls_frame = tb.Labelframe(main_frame, text="Controls", padding=15)
        controls_frame.pack(fill=X, pady=10)

        tb.Button(controls_frame, text="🎤 Start Recording", bootstyle=PRIMARY, command=self.start_recording).pack(side=LEFT, padx=5)
        tb.Button(controls_frame, text="⏹️ Stop & Transcribe", bootstyle=WARNING, command=self.stop_and_process).pack(side=LEFT, padx=5)
        tb.Button(controls_frame, text="📁 Use Saved Audio", bootstyle=INFO, command=self.use_existing_audio).pack(side=LEFT, padx=5)
        tb.Button(controls_frame, text="🔑 Change API Key", bootstyle=SECONDARY, command=self.change_api_key).pack(side=LEFT, padx=5)

        # Provider and prompt
        config_frame = tb.Labelframe(main_frame, text="Settings", padding=15)
        config_frame.pack(fill=X, pady=10)

        tb.Label(config_frame, text="LLM Provider:").pack(side=LEFT)
        tb.Radiobutton(config_frame, text="OpenAI", variable=self.provider, value="openai").pack(side=LEFT, padx=5)
        tb.Radiobutton(config_frame, text="Ollama", variable=self.provider, value="ollama").pack(side=LEFT, padx=5)

        tb.Label(config_frame, text="Custom Prompt:").pack(side=LEFT, padx=(15, 5))
        self.prompt_entry = tb.Entry(config_frame, width=50)
        self.prompt_entry.pack(side=LEFT, padx=5)

        # Output summary
        output_frame = tb.Labelframe(main_frame, text="📝 Generated Summary", padding=10)
        output_frame.pack(fill=BOTH, expand=True, pady=10)

        self.output_box = tb.ScrolledText(output_frame, height=25, font=("Courier", 11))
        self.output_box.pack(fill=BOTH, expand=True)

    def start_recording(self):
        start_recording()

    def stop_and_process(self):
        try:
            audio_path = stop_recording()
            self._process_audio(audio_path)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def use_existing_audio(self):
        audio_path = filedialog.askopenfilename(initialdir="audio_files", title="Select Audio File")
        if audio_path:
            self._process_audio(audio_path)

    def _process_audio(self, audio_path):
        try:
            transcript = transcribe_audio(audio_path)
            custom_prompt = self.prompt_entry.get().strip()

            if self.provider.get() == "openai":
                if not os.getenv("OPENAI_API_KEY"):
                    key = simpledialog.askstring("API Key", "Enter your OpenAI API key:")
                    if key:
                        set_key(".env", "OPENAI_API_KEY", key)
                        os.environ["OPENAI_API_KEY"] = key

            summary = summarize_text(transcript, user_prompt=custom_prompt, provider=self.provider.get())
            self.output_box.delete(1.0, "end")
            self.output_box.insert("end", summary)
            messagebox.showinfo("Success", "Transcript and summary saved!")

        except Exception as e:
            messagebox.showerror("Error", str(e))

    def change_api_key(self):
        key = simpledialog.askstring("API Key", "Enter new OpenAI API key:")
        if key:
            set_key(".env", "OPENAI_API_KEY", key)
            os.environ["OPENAI_API_KEY"] = key
            messagebox.showinfo("API Key Updated", "API key updated successfully!")

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")
    app = MeetingNoteMateApp(root)
    root.mainloop()
EOF

echo "✅ GUI project with full features is ready."
echo "➡️ To start, run:"
echo "cd $PROJECT_DIR"
echo "source $ENV_NAME/bin/activate && python gui_app.py"
