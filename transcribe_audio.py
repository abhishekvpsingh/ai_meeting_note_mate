# transcribe_audio.py
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from pathlib import Path
from datetime import datetime
import tempfile
import os
from path_utils import get_project_data_dir, get_logger


def diarize_audio(audio_path: str) -> list[tuple[str, str]]:
    """
    Return a list of (speaker, text_segment) tuples using pyannote diarization.
    Falls back gracefully if diarization fails.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()
        token = os.getenv("HUGGINGFACE_TOKEN")

        if not token:
            print("[WARN] No Hugging Face token found in environment. Set HUGGINGFACE_TOKEN in your .env file.")

        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization")
        diarization = pipeline(audio_path)
        segments = []
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segment_info = f"{speaker}: {turn.start:.1f}s–{turn.end:.1f}s"
                segments.append((speaker, segment_info))
        return segments
    except Exception as e:
        print(f"[WARN] Diarization failed: {e}")
        return []

def transcribe_audio(audio_input, project_name: str = "Datalake") -> str:
    """
    Transcribes an audio file using faster-whisper and enriches with speaker diarization if possible.
    Saves transcript under the project's transcripts folder.
    """
    logger = get_logger(project_name)

    # Resolve the path
    if hasattr(audio_input, "name"):
        audio_path = Path(audio_input.name)
    else:
        audio_path = Path(audio_input)

    if not audio_path.is_absolute():
        audio_path = get_project_data_dir(project_name) / "audio_files" / audio_path

    if not audio_path.exists():
        logger.error("Audio file not found: %s", audio_path)
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info("Transcribing audio: %s", audio_path)

    # 1️⃣ Transcribe using Faster Whisper
    model = WhisperModel("base", compute_type="int8")
    segments, info = model.transcribe(str(audio_path))
    raw_transcript = " ".join(segment.text.strip() for segment in segments).strip()

    # 2️⃣ Attempt diarization to label speakers
    logger.info("Running speaker diarization...")
    try:
        diarization = diarize_audio(str(audio_path))
    except Exception as e:
        logger.warning("Diarization failed: %s", e)
        diarization = []

    # 3️⃣ Combine transcription + speaker info (simple mapping)
    if diarization:
        logger.info("Merging diarization labels into transcript...")
        labeled_transcript = []
        text_chunks = raw_transcript.split(". ")
        for i, (spk, seg) in enumerate(diarization):
            chunk = text_chunks[i] if i < len(text_chunks) else ""
            labeled_transcript.append(f"{spk}: {chunk.strip()}")
        final_transcript = "\n".join(labeled_transcript)
    else:
        final_transcript = raw_transcript

    # 4️⃣ Save transcript file
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = get_project_data_dir(project_name) / "transcripts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"transcript_{ts}.txt"
    with open(out_path, "w") as f:
        f.write(final_transcript)

    logger.info(
        "Transcription saved: %s (language=%s, duration=%.2fs, speakers=%d)",
        out_path, info.language, info.duration, len(set(s for s, _ in diarization)) if diarization else 0,
    )
    return final_transcript
