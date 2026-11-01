# -*- mode: python ; coding: utf-8 -*-
"""
Especificación SOTA de PyInstaller para AutoRod v2.0
Configurado con las mejores prácticas de seguridad, reputación y distribución:
 - Sin compresión UPX (desactivado para eliminar falsos positivos de antivirus).
 - Inclusión de manifiesto PE formal de Windows con compatibilidad Windows 10/11.
 - Inclusión de archivo de recursos de versión (CompanyName, LegalCopyright, etc.).
 - Recolección completa de subsistemas UI (Flet Flutter Engine) y visión (OpenCV).
 - Soporte para salida onedir estructurada lista para instaladores e instaladores portables.
"""

import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

project_root = Path.cwd().resolve()
src_dir = project_root / "src"

# Recolectar Flet y dependencias críticas
flet_datas, flet_binaries, flet_hiddenimports = collect_all("flet")
flet_desktop_datas, flet_desktop_binaries, flet_desktop_hiddenimports = collect_all("flet_desktop")
opencv_datas, opencv_binaries, opencv_hiddenimports = collect_all("cv2")
mss_datas, mss_binaries, mss_hiddenimports = collect_all("mss")

datas = [
    (str(src_dir / "autorod" / "assets"), "autorod/assets"),
    (str(project_root / "config.toml"), "."),
] + flet_datas + flet_desktop_datas + opencv_datas + mss_datas

binaries = flet_binaries + flet_desktop_binaries + opencv_binaries + mss_binaries

hiddenimports = [
    "autorod",
    "autorod.bootstrap",
    "autorod.config",
    "autorod.domain",
    "autorod.domain.models",
    "autorod.domain.ports",
    "autorod.application",
    "autorod.infrastructure",
    "autorod.infrastructure.capture.mss_capture",
    "autorod.infrastructure.vision.geometric_strategy",
    "autorod.infrastructure.vision.template_match_strategy",
    "autorod.infrastructure.input.win32.sendinput",
    "autorod.infrastructure.input.win32.interception",
    "autorod.infrastructure.ui.flet.app",
    "flet",
    "flet_desktop",
    "numpy",
    "cv2",
    "mss",
] + flet_hiddenimports + flet_desktop_hiddenimports + opencv_hiddenimports + mss_hiddenimports

block_cipher = None

a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(src_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "turtle", "test", "unittest"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Ejecutable Windowed (sin consola negra de fondo)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="AutoRod",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                      # VITAL: UPX desactivado para prevenir falsos positivos AV
    console=False,                  # Aplicación de escritorio limpia
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_dir / "autorod" / "assets" / "icons" / "logo.ico"),
    version=str(project_root / "distribution" / "windows" / "file_version_info.txt"),
    manifest=str(project_root / "distribution" / "windows" / "autorod.manifest"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,                      # VITAL: Sin compresión UPX
    upx_exclude=[],
    name="AutoRod",
)
