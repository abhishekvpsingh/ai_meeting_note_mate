import sounddevice as sd
from scipy.io.wavfile import write
import datetime
import numpy as np
import threading
from path_utils import get_user_data_dir
import os

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
    data_dir = get_user_data_dir() / "audio_files"
    data_dir.mkdir(parents=True, exist_ok=True)
    filename = data_dir/f"meeting_{timestamp}.wav"
    write(filename, samplerate, audio_data)
    print(f"💾 Audio saved to {filename}")
    return filename
