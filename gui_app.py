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
