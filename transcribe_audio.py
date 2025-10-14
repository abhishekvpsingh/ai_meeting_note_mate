from faster_whisper import WhisperModel
from path_utils import get_user_data_dir
from pathlib import Path
import datetime

def transcribe_audio(audio_input):
    """
    Transcribes an audio file using faster-whisper.
    Accepts: filename, full path, or open file object.
    """
    # Determine the actual path
    if hasattr(audio_input, "name"):  # open file
        audio_path = Path(audio_input.name)
    else:
        audio_path = Path(audio_input)

    # If only a filename is provided, resolve it inside user data dir
    if not audio_path.is_absolute():
        audio_path = get_user_data_dir() / "audio_files" / audio_path

    # Ensure file exists
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # Load whisper model
    model = WhisperModel("base", compute_type="int8")

    # Transcribe
    segments, info = model.transcribe(str(audio_path))
    transcript_text = " ".join(segment.text for segment in segments).strip()

    # Save transcript
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_dir = get_user_data_dir() / "transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)

    transcript_path = transcript_dir / f"transcript_{timestamp}.txt"
    with open(transcript_path, "w") as f:
        f.write(transcript_text)

    print(f"📝 Transcription complete. Saved to {transcript_path}")
    return transcript_text
