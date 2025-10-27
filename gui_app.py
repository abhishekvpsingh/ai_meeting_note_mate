# gui_app.py
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from tkinter import filedialog, simpledialog, messagebox, Listbox, Scrollbar, Frame, END, RIGHT, Y, BOTH, Canvas
import os
import threading

from dotenv import load_dotenv, set_key
load_dotenv()

from path_utils import get_logger
from projects_manager import load_projects, save_projects
from record_audio import start_recording, stop_recording, is_recording
from transcribe_audio import transcribe_audio
from summarize_notes import summarize_text
from summarize_team_progress import summarize_team_progress
from team_members import load_team_members, save_team_members
from background_knowledge import load_background, save_background
from html_viewer import show_in_browser

# Ollama discovery
def list_ollama_models() -> list[str]:
    try:
        import requests
        r = requests.get("http://localhost:11434/api/tags", timeout=1.2)
        r.raise_for_status()
        data = r.json()
        names = []
        for m in data.get("models", []):
            # common fields: "name": "llama3:8b", etc.
            n = m.get("name") or m.get("model")
            if n:
                names.append(str(n))
        # unique, keep order
        seen = set(); out = []
        for n in names:
            if n not in seen:
                seen.add(n)
                out.append(n)
        return out or ["llama3"]
    except Exception:
        return ["llama3"]

class MeetingNoteMateApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Meeting Note Mate — Datalake Edition")

        # ===== Base variable initialization =====
        self.provider = tb.StringVar(value="openai")
        self.model_var = tb.StringVar(value="gpt-4o-mini")
        self.project_var = tb.StringVar(value="Datalake")  # default

        # Custom prompt area
        self.prompt_text = None

        # Layout
        # ========= Compact Modern UI with Gradient Background =========

        # ---- Style and Window ----
        self.style = tb.Style("flatly")  # fresh, modern color palette
        self.root.geometry("1000x620")
        self.root.minsize(850, 520)
        self.root.title("Meeting Note Mate — Datalake Edition")

        # Soft gradient background
        gradient = Canvas(self.root, width=1200, height=800, highlightthickness=0)
        gradient.pack(fill=BOTH, expand=True)
        for i in range(0, 800):
            color = f"#e9f2f7" if i < 300 else f"#f6f9fb"
            gradient.create_rectangle(0, i, 1200, i + 1, outline="", fill=color)

        # ---- Center card (main app frame) ----
        outer = tb.Frame(self.root, padding=10)
        outer.place(relx=0.5, rely=0.5, anchor="center")

        card = tb.Frame(outer, padding=16, bootstyle="secondary")
        card.pack(fill=BOTH, expand=True)
        card.configure(style="Card.TFrame")

        # card background and font styling
        card_bg = "#ffffff"
        self.style.configure("Card.TFrame", background=card_bg, relief="raised")
        self.style.configure("Card.TLabelframe", background=card_bg)
        self.style.configure("Card.TLabelframe.Label", background=card_bg, font=("Helvetica", 11, "bold"))
        self.style.configure("Card.TLabel", background=card_bg)
        card.configure(borderwidth=2, relief="groove")

        # ---------- HEADER ----------
        header = tb.Frame(card, bootstyle="light")
        header.pack(fill=X, pady=(0, 10))
        tb.Label(header, text="🧠 Meeting Note Mate", font=("Helvetica", 26, "bold"), bootstyle="primary").pack(side=LEFT, padx=(10, 8))
        tb.Label(header, text="Datalake Edition", font=("Helvetica", 13, "italic"), bootstyle="info").pack(side=LEFT)

        # ---------- SETTINGS ----------
        settings = tb.Labelframe(card, text="Settings", padding=8, bootstyle="Card")
        settings.pack(fill=X, pady=(5, 6))

        tb.Label(settings, text="Provider:", width=9, bootstyle="Card.TLabel").grid(row=0, column=0, sticky=W)
        tb.Radiobutton(settings, text="OpenAI", variable=self.provider, value="openai", command=self._on_provider_change).grid(row=0, column=1, sticky=W, padx=(0, 8))
        tb.Radiobutton(settings, text="Ollama", variable=self.provider, value="ollama", command=self._on_provider_change).grid(row=0, column=2, sticky=W)

        tb.Label(settings, text="Model:", width=7, bootstyle="Card.TLabel").grid(row=0, column=3, sticky=E)
        self.model_box = tb.Combobox(settings, textvariable=self.model_var, width=18)
        self.model_box.grid(row=0, column=4, padx=(4, 12))

        tb.Label(settings, text="Project:", width=7, bootstyle="Card.TLabel").grid(row=0, column=5, sticky=E)
        self.project_box = tb.Combobox(settings, textvariable=self.project_var, width=16)
        self.project_box.grid(row=0, column=6, padx=(4, 8))
        self._refresh_projects()

        tb.Button(settings, text="🔑 API Key", bootstyle=(INFO, "outline"), command=self.change_api_key, width=10).grid(row=0, column=7, padx=(4, 0))

        # ---------- PROMPT ----------
        prompt_frame = tb.Labelframe(card, text="Custom Prompt (optional)", padding=6, bootstyle="Card")
        prompt_frame.pack(fill=X, pady=(4, 8))
        self.prompt_text = tb.ScrolledText(prompt_frame, height=3, font=("Courier New", 10))
        self.prompt_text.pack(fill=X)

        # ---------- CONTROLS ----------
        controls = tb.Labelframe(card, text="Actions", padding=10, bootstyle="Card")
        controls.pack(fill=X, pady=(6, 8))

        btn_style = dict(width=16, padding=4)

        # Primary buttons (first row)
        row1 = tb.Frame(controls, bootstyle="Card")
        row1.pack(fill=X, pady=2)

        tb.Button(row1, text="🎤 Start Recording", bootstyle=PRIMARY, command=self.start_recording, **btn_style).pack(side=LEFT, padx=3)
        tb.Button(row1, text="⏹️ Stop & Transcribe", bootstyle=DANGER, command=self.stop_and_process, **btn_style).pack(side=LEFT, padx=3)
        tb.Button(row1, text="📁 Use Saved Audio", bootstyle=INFO, command=self.use_existing_audio, **btn_style).pack(side=LEFT, padx=3)
        tb.Button(row1, text="📊 Team Summary (Last 30d)", bootstyle=SUCCESS, command=self.show_team_summary, **btn_style).pack(side=LEFT, padx=3)
        tb.Button(row1, text="📂 Team Summary History (30d)", bootstyle=WARNING, command=self.show_team_summary_history, **btn_style).pack(side=LEFT, padx=3)

        # Management buttons (second row)
        row2 = tb.Frame(controls, bootstyle="Card")
        row2.pack(fill=X, pady=(5, 0))

        tb.Button(row2, text="👥 Manage Team", bootstyle=SECONDARY, command=self.manage_team_members, **btn_style).pack(side=LEFT, padx=3)
        tb.Button(row2, text="🧩 Manage Projects", bootstyle=SECONDARY, command=self.manage_projects, **btn_style).pack(side=LEFT, padx=3)
        tb.Button(row2, text="🧠 Team Background", bootstyle=SECONDARY, command=self.manage_background, **btn_style).pack(side=LEFT, padx=3)

        # ---------- STATUS ----------
        self.status_label = tb.Label(card, text="", font=("Helvetica", 11, "italic"), bootstyle=INFO)
        self.status_label.pack(pady=(8, 2))

        
    # ------- Helpers -------
    def _refresh_model_list(self, initial=False):
        """Refresh model dropdown based on selected provider."""
        prov = self.provider.get()
        if prov == "ollama":
            models = list_ollama_models()
            self.model_box.configure(values=models)
            if initial or not self.model_var.get() or self.model_var.get() not in models:
                self.model_var.set(models[0] if models else "llama3")
        else:
            defaults = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini"]
            self.model_box.configure(values=defaults)
            if initial or not self.model_var.get() or self.model_var.get() not in defaults:
                self.model_var.set(defaults[0])


    def _on_provider_change(self):
        """Called when provider changes — refresh model list immediately."""
        prov = self.provider.get()
        self._refresh_model_list()

        if prov == "ollama":
            models = list_ollama_models()
            self.model_var.set(models[0] if models else "llama3")
            self.status_label.config(text=f"🦙 Ollama models loaded: {len(models)} found.", bootstyle="info")
        else:
            self.model_var.set("gpt-4o-mini")
            self.status_label.config(text="🤖 Using OpenAI provider.", bootstyle="info")

        self.model_box.update_idletasks()



    def _refresh_projects(self):
        projects = load_projects()
        self.project_box.configure(values=projects)
        # Default to Datalake if present, else first
        if "Datalake" in projects:
            self.project_var.set("Datalake")
        else:
            self.project_var.set(projects[0])

    # ------- Actions -------
    def change_api_key(self):
        key = simpledialog.askstring("API Key", "Enter your OpenAI API key:")
        if key:
            set_key(".env", "OPENAI_API_KEY", key)
            os.environ["OPENAI_API_KEY"] = key
            messagebox.showinfo("API Key Updated", "API key updated successfully!")

    def start_recording(self):
        project = self.project_var.get()
        logger = get_logger(project)
        try:
            if is_recording():
                messagebox.showwarning("Already Recording", "Recording is already in progress!")
                return
            self.status_label.config(text=f"🎙️ Recording [{project}] ...", bootstyle=SUCCESS)
            self.root.update_idletasks()
            self.current_audio_path = start_recording(project_name=project)
            logger.info("Start recording clicked; file: %s", self.current_audio_path)
        except Exception as e:
            logger.exception("start_recording failed: %s", e)
            messagebox.showerror("Error", str(e))

    def stop_and_process(self):
        project = self.project_var.get()
        provider = self.provider.get()
        model = self.model_var.get().strip()
        logger = get_logger(project)

        try:
            if not is_recording():
                messagebox.showinfo("No Active Recording", "There is no recording currently running.")
                return

            self.status_label.config(text="⏳ Processing audio...", bootstyle=WARNING)
            self.root.update_idletasks()

            audio_path = stop_recording()
            self.status_label.config(text="🎧 Transcribing + Summarizing in background...", bootstyle=INFO)
            self.root.update_idletasks()

            def worker():
                try:
                    transcript = transcribe_audio(audio_path, project_name=project)
                    custom_prompt = self.prompt_text.get("1.0", "end").strip()
                    summary = summarize_text(
                        transcript,
                        user_prompt=custom_prompt,
                        provider=provider,
                        model_name=model,
                        project_name=project
                    )
                    # Auto-open in Chrome
                    show_in_browser(f"{project} - Meeting Summary", summary)
                    messagebox.showinfo("Next Meeting Ready", "Previous meeting is processing. You can start recording the next meeting now!")
                except Exception as e:
                    logger.exception("Processing failed: %s", e)
                    messagebox.showerror("Error", f"Processing failed: {e}")

            threading.Thread(target=worker, daemon=True).start()

        except Exception as e:
            logger.exception("stop_and_process failed: %s", e)
            self.status_label.config(text="")
            messagebox.showerror("Error", str(e))

    def use_existing_audio(self):
        project = self.project_var.get()
        logger = get_logger(project)
        audio_path = filedialog.askopenfilename(initialdir=str(os.path.expanduser(f"~/MeetingNoteMateData/{project}/audio_files")),
                                                title="Select Audio File",
                                                filetypes=[("Audio", "*.wav *.mp3 *.m4a *.flac"), ("All files", "*.*")])
        if audio_path:
            try:
                self.status_label.config(text="⏳ Processing selected audio...", bootstyle=WARNING)
                self.root.update_idletasks()
                def worker():
                    try:
                        transcript = transcribe_audio(audio_path, project_name=project)
                        custom_prompt = self.prompt_text.get("1.0", "end").strip()
                        summary = summarize_text(
                            transcript,
                            user_prompt=custom_prompt,
                            provider=self.provider.get(),
                            model_name=self.model_var.get().strip(),
                            project_name=project
                        )
                        show_in_browser(f"{project} - Meeting Summary", summary)
                        self.status_label.config(text="✅ Summary generated & opened in browser", bootstyle=SUCCESS)
                    except Exception as e:
                        logger.exception("Processing saved audio failed: %s", e)
                        messagebox.showerror("Error", f"Failed: {e}")
                threading.Thread(target=worker, daemon=True).start()
            except Exception as e:
                logger.exception("use_existing_audio failed: %s", e)
                messagebox.showerror("Error", str(e))

    def show_team_summary(self):
        project = self.project_var.get()
        provider = self.provider.get()
        model = self.model_var.get().strip()
        logger = get_logger(project)
        try:
            self.status_label.config(text="🧠 Generating 30-day team summary...", bootstyle=INFO)
            self.root.update_idletasks()
            def worker():
                try:
                    result = summarize_team_progress(project_name=project, provider=provider, model_name=model)
                    # summarize_team_progress already opens in browser
                    self.status_label.config(text="✅ Team summary opened in browser", bootstyle=SUCCESS)
                except Exception as e:
                    logger.exception("Team summary failed: %s", e)
                    messagebox.showerror("Error", str(e))
            threading.Thread(target=worker, daemon=True).start()
        except Exception as e:
            logger.exception("show_team_summary failed: %s", e)
            messagebox.showerror("Error", str(e))

    def show_team_summary_history(self):
        """Show a popup listing all team summaries from the last 30 days."""
        import datetime
        from pathlib import Path

        project = self.project_var.get()
        logger = get_logger(project)
        project_dir = Path.home() / "MeetingNoteMateData" / project / "team_summaries"
        project_dir.mkdir(parents=True, exist_ok=True)

        cutoff = datetime.datetime.now() - datetime.timedelta(days=30)
        files = []
        for f in sorted(project_dir.glob("*.txt"), reverse=True):
            try:
                ts_str = f.stem.split("_")[-2] + "_" + f.stem.split("_")[-1]
                ts = datetime.datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
                if ts >= cutoff:
                    files.append(f)
            except Exception:
                continue

        if not files:
            messagebox.showinfo("No History", "No team summaries found in the last 30 days.")
            return

        popup = tb.Toplevel(self.root)
        popup.title(f"Team Summary History — {project}")
        popup.geometry("600x400")

        tb.Label(popup, text=f"Team summaries for {project} (last 30 days):").pack(pady=8)

        listbox = Listbox(popup, selectmode="single")
        listbox.pack(fill=BOTH, expand=True, padx=12, pady=6)

        for f in files:
            listbox.insert(END, f.name)

        def open_selected():
            sel = listbox.curselection()
            if not sel:
                messagebox.showwarning("Select a File", "Please select a summary to open.")
                return
            filename = files[sel[0]]
            try:
                content = filename.read_text()
                show_in_browser(f"{project} — {filename.stem}", content)
                popup.destroy()
            except Exception as e:
                logger.exception("Failed to open team summary: %s", e)
                messagebox.showerror("Error", str(e))

        tb.Button(popup, text="🧭 Open Selected", bootstyle=PRIMARY, command=open_selected).pack(pady=10)


    # -------- Team/Projects/Background management --------
    def manage_team_members(self):
        project = self.project_var.get()
        current = load_team_members(project)

        popup = tb.Toplevel(self.root); popup.title(f"Manage Team — {project}"); popup.geometry("420x420")
        tb.Label(popup, text="Enter team members (one per line):").pack(pady=8)
        box = tb.ScrolledText(popup, height=15); box.pack(fill=BOTH, expand=True, padx=10, pady=8)
        if current: box.insert("1.0", "\n".join(current))

        def save():
            updated = [ln.strip() for ln in box.get("1.0", "end").splitlines() if ln.strip()]
            save_team_members(project, updated)
            popup.destroy()
            self.status_label.config(text=f"✅ Saved {len(updated)} team members for {project}.", bootstyle=SUCCESS)

        tb.Button(popup, text="💾 Save", bootstyle=PRIMARY, command=save).pack(pady=8)

    def manage_projects(self):
        projects = load_projects()
        popup = tb.Toplevel(self.root); popup.title("Manage Projects"); popup.geometry("420x420")
        tb.Label(popup, text="Enter projects (one per line):").pack(pady=8)
        box = tb.ScrolledText(popup, height=15); box.pack(fill=BOTH, expand=True, padx=10, pady=8)
        box.insert("1.0", "\n".join(projects))

        def save_fn():
            updated = [ln.strip() for ln in box.get("1.0", "end").splitlines() if ln.strip()]
            save_projects(updated)
            popup.destroy()
            # Refresh dropdown so it reflects immediately
            self._refresh_projects()
            self.status_label.config(text=f"✅ Projects updated: {', '.join(updated)}", bootstyle=SUCCESS)

        tb.Button(popup, text="💾 Save", bootstyle=PRIMARY, command=save_fn).pack(pady=8)

    def manage_background(self):
        project = self.project_var.get()
        current = load_background(project)

        popup = tb.Toplevel(self.root); popup.title(f"Team Background — {project}"); popup.geometry("560x520")
        tb.Label(popup, text="Enter one mapping per line as 'Name: expertise/area/notes'").pack(pady=8)

        box = tb.ScrolledText(popup, height=18); box.pack(fill=BOTH, expand=True, padx=10, pady=8)
        if current:
            lines = [f"{k}: {v}" for k, v in current.items()]
            box.insert("1.0", "\n".join(lines))

        def save():
            lines = [ln.strip() for ln in box.get("1.0", "end").splitlines() if ln.strip()]
            mapping = {}
            for ln in lines:
                if ":" in ln:
                    name, info = ln.split(":", 1)
                    mapping[name.strip()] = info.strip()
            save_background(project, mapping)
            popup.destroy()
            self.status_label.config(text=f"✅ Background saved for {project} ({len(mapping)} entries).", bootstyle=SUCCESS)

        tb.Button(popup, text="💾 Save", bootstyle=PRIMARY, command=save).pack(pady=8)

if __name__ == "__main__":
    root = tb.Window(themename="cosmo")
    app = MeetingNoteMateApp(root)
    root.mainloop()
