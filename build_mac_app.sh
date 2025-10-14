#!/bin/bash
# ===============================================
# build_mac_app.sh — Automated build for Meeting Note Mate
# ===============================================

# Stop on first error
set -e

PROJECT_DIR="/Users/abhisheksingh/CodingPlayArea/PROJECTS/meeting_note_mate_v3"
VENV_PATH="$PROJECT_DIR/note-env"
SPEC_FILE="$PROJECT_DIR/Meeting Note Mate.spec"
APP_NAME="Meeting Note Mate.app"

echo "🚀 Starting build process for $APP_NAME..."

# Step 1 — Activate virtual environment
if [ -d "$VENV_PATH" ]; then
  echo "🔹 Activating virtual environment..."
  source "$VENV_PATH/bin/activate"
else
  echo "❌ Virtual environment not found at $VENV_PATH"
  exit 1
fi

# Step 2 — Clean old builds
echo "🧹 Cleaning old build directories..."
rm -rf "$PROJECT_DIR/build" "$PROJECT_DIR/dist"

# Step 3 — Ensure key dependencies
echo "📦 Ensuring PyInstaller and audio deps..."
pip install --upgrade pip setuptools wheel
pip install pyinstaller sounddevice soundfile pydub

# Step 4 — Build the app
echo "🏗️  Building macOS .app bundle..."
pyinstaller "$SPEC_FILE" --clean --noconfirm

# Step 5 — Display build result
if [ -d "$PROJECT_DIR/dist/$APP_NAME" ]; then
  echo "✅ Build complete! App available at:"
  echo "   $PROJECT_DIR/dist/$APP_NAME"
else
  echo "❌ Build failed. Check the output above for errors."
  exit 1
fi

# Step6 - Create DMG for easy distribution
DMG_PATH="$PROJECT_DIR/release/Meeting-Note-Mate.dmg"
mkdir -p "$PROJECT_DIR/release"
echo "💿 Creating DMG..."
hdiutil create -volname "Meeting Note Mate" \
  -srcfolder "$PROJECT_DIR/dist/$APP_NAME" \
  -ov -format UDZO "$DMG_PATH"
echo "📦 DMG created at: $DMG_PATH"


echo "🎉 Done! You can now run:"
echo "   dist/$APP_NAME/Contents/MacOS/Meeting\\ Note\\ Mate"
