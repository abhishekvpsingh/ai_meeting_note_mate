#!/bin/bash

# Navigate to the project directory (optional but recommended)
cd "$(dirname "$0")"

# Activate the virtual environment
source note-env/bin/activate

# Run the Python GUI application
python gui_app.py
