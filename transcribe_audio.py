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
