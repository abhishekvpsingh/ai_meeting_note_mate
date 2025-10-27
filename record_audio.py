# record_audio.py
import sounddevice as sd
from scipy.io.wavfile import write
import numpy as np
import threading
from datetime import datetime
from path_utils import get_project_data_dir, get_logger

_frames = []
_recording = False
_recording_thread = None
_current_file = None
_current_project = "Datalake"

def is_recording() -> bool:
    return _recording

def callback(indata, frames_count, time, status):
    if status:
        # Sounddevice status warnings (xruns, etc.)
        get_logger(_current_project).warning("Audio status: %s", status)
    _frames.append(indata.copy())

def start_recording(project_name: str = "Datalake", samplerate: int = 44100):
    global _recording, _frames, _recording_thread, _current_file, _current_project
    logger = get_logger(project_name)
    if _recording:
        logger.warning("Attempted to start recording, but a recording is already in progress.")
        raise RuntimeError("Recording already in progress! Please stop before starting again.")

    _current_project = project_name
    _recording = True
    _frames = []

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pdir = get_project_data_dir(project_name)
    out_dir = pdir / "audio_files"
    _current_file = out_dir / f"{project_name.lower()}_meeting_{ts}.wav"

    logger.info("Recording started: %s", _current_file)
    _recording_thread = threading.Thread(target=_record_loop, args=(samplerate,), daemon=True)
    _recording_thread.start()
    return _current_file

def _record_loop(samplerate: int):
    global _recording
    logger = get_logger(_current_project)
    try:
        with sd.InputStream(callback=callback, channels=1, samplerate=samplerate):
            while _recording:
                sd.sleep(100)
    except Exception as e:
        logger.exception("Error in audio input stream: %s", e)
        _recording = False

def stop_recording(samplerate: int = 44100):
    global _recording, _current_file
    logger = get_logger(_current_project)
    if not _recording:
        logger.warning("Stop requested but no active recording.")
        raise RuntimeError("No active recording to stop.")

    _recording = False
    if not _frames:
        logger.error("No audio frames captured; nothing to write.")
        raise RuntimeError("Recording had no audio frames.")

    audio_data = np.concatenate(_frames, axis=0)
    write(_current_file, samplerate, audio_data)
    logger.info("Audio saved to %s (frames=%d)", _current_file, len(_frames))
    return _current_file
