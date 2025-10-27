# transcribe_audio.py
from faster_whisper import WhisperModel
from pathlib import Path
from datetime import datetime
from path_utils import get_project_data_dir, get_logger

def transcribe_audio(audio_input, project_name: str = "Datalake") -> str:
    """
    Transcribes an audio file using faster-whisper.
    Accepts: filename, full path, or open file object.
    Saves transcript under the project's transcripts folder.
    """
    logger = get_logger(project_name)

    # Resolve the path
    if hasattr(audio_input, "name"):
        audio_path = Path(audio_input.name)
    else:
        audio_path = Path(audio_input)

    if not audio_path.is_absolute():
        # Try resolving within project audio_files
        audio_path = get_project_data_dir(project_name) / "audio_files" / audio_path

    if not audio_path.exists():
        logger.error("Audio file not found: %s", audio_path)
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info("Transcribing audio: %s", audio_path)

    # Load Whisper model (base/int8 — fast & light)
    model = WhisperModel("base", compute_type="int8")
    segments, info = model.transcribe(str(audio_path))
    transcript_text = " ".join(segment.text for segment in segments).strip()

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = get_project_data_dir(project_name) / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"transcript_{ts}.txt"
    with open(out_path, "w") as f:
        f.write(transcript_text)

    logger.info("Transcription saved: %s (language=%s, duration=%.2fs)", out_path, info.language, info.duration)
    return transcript_text
