# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Language Review — Screen Recorder.

Build commands:
  Windows: pyinstaller language_review_app.spec
  macOS:   pyinstaller language_review_app.spec

Output: dist/LanguageReviewApp  (macOS)
        dist/LanguageReviewApp.exe  (Windows)
"""

import sys
from pathlib import Path

block_cipher = None

# Locate bundled FFmpeg binary (must be placed at project root before building)
_ffmpeg_src = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
_ffmpeg_binaries = [(_ffmpeg_src, ".")] if Path(_ffmpeg_src).exists() else []

a = Analysis(
    ["src/main.py"],
    pathex=["."],
    binaries=_ffmpeg_binaries,
    datas=[],
    hiddenimports=["PyQt6.QtCore", "PyQt6.QtWidgets", "PyQt6.QtGui"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="LanguageReviewApp",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,   # windowed (no console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
