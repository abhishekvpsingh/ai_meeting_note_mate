#!/bin/bash
set -e

echo "🚀 Setting up Meeting Note Mate (Python 3.12, macOS)..."

# -------------------------------
# 1️⃣ Create and activate virtual environment
# -------------------------------
if [ ! -d "note-env" ]; then
  echo "📦 Creating virtual environment (note-env)..."
  python3.12 -m venv note-env
fi

# shellcheck disable=SC1091
source note-env/bin/activate

echo "✅ Virtual environment activated."

# -------------------------------
# 2️⃣ Upgrade pip & build tools
# -------------------------------
echo "⬆️ Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# -------------------------------
# 3️⃣ Core framework + utilities
# -------------------------------
echo "📦 Installing core GUI, utility, and audio dependencies..."
pip install \
  "ttkbootstrap==1.10.1" \
  "python-dotenv==1.0.1" \
  "sounddevice==0.4.6" \
  "numpy==1.26.4" \
  "scipy==1.12.0" \
  "requests==2.32.3" \
  "markdown==3.7" \
  "Pillow==10.3.0" \
  "tqdm==4.67.1"

# -------------------------------
# 4️⃣ LLM stack (OpenAI + Ollama compatible)
# -------------------------------
echo "🧠 Installing OpenAI client stack (no proxy errors)..."
pip install \
  "openai==1.47.1" \
  "httpx==0.27.0" \
  "httpcore==1.0.5"

# -------------------------------
# 5️⃣ Install prebuilt AV wheel for Python 3.12
# -------------------------------
echo "🎧 Installing prebuilt AV wheel (no FFmpeg compile)..."
pip install "av==12.0.0" --only-binary=:all:

# -------------------------------
# 6️⃣ Install Faster-Whisper dependencies manually
# -------------------------------
echo "🔧 Installing Faster-Whisper compatible dependencies..."
pip install \
  "ctranslate2==4.6.0" \
  "onnxruntime==1.23.2" \
  "tokenizers==0.15.2" \
  "huggingface-hub==0.36.0" \
  "pyyaml>=6.0" \
  "tqdm>=4.66.0" \
  "numpy>=1.26.0"

# -------------------------------
# 7️⃣ Install Faster-Whisper itself (without deps)
# -------------------------------
echo "🎙️ Installing Faster-Whisper (no dependency conflicts)..."
pip install "faster-whisper==1.0.1" --no-deps

# -------------------------------
# 8️⃣ Verification block
# -------------------------------
echo ""
echo "🧪 Running verification..."
python - <<'PY'
import av, ctranslate2, onnxruntime, tokenizers
from faster_whisper import WhisperModel
from openai import OpenAI

print("✅ av:", av.__version__)
print("✅ ctranslate2:", ctranslate2.__version__)
print("✅ onnxruntime:", onnxruntime.__version__)
print("✅ tokenizers:", tokenizers.__version__)

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
print("✅ OpenAI client initialized OK")

model = WhisperModel("tiny")
print("✅ Faster-Whisper initialized OK")
PY

echo ""
echo "🎉 Setup completed successfully for Meeting Note Mate!"
