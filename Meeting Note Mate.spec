# Meeting Note Mate.spec – compatible with PyInstaller 6.16+

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []

# --- Collect all packages that need dynamic libs ---
for pkg in ['sounddevice', 'soundfile', 'pydub']:
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ['gui_app.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)

pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Meeting Note Mate',
    windowed=True,
    icon=None,
)

# ---- macOS bundle with custom Info.plist fields ----
app = BUNDLE(
    exe,
    name='Meeting Note Mate.app',
    bundle_identifier='com.abhishek.meetingnotemate',
    info_plist={
        "CFBundleName": "Meeting Note Mate",
        "CFBundleDisplayName": "Meeting Note Mate",
        "CFBundleShortVersionString": "1.0.0",
        "CFBundleVersion": "1.0.0",
        "NSMicrophoneUsageDescription": "This app records and summarizes your meetings.",
    },
)
