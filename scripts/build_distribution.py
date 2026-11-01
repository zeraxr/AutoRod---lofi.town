#!/usr/bin/env python3
"""
Script Maestro de Empaquetado y Distribución para AutoRod v2.0
============================================================
Automatiza el flujo completo de construcción de releases para Windows:
 1. Validación de entorno, dependencias y assets del proyecto.
 2. Compilación de binarios mediante PyInstaller (sin UPX, con versión PE y manifiesto).
 3. Empaquetado del instalador asistido (.exe) mediante Inno Setup 6 (si está instalado).
 4. Creación del archivo comprimido portable (.zip) con estructura lista para ejecución.
 5. Cálculo y exportación de firmas criptográficas de integridad (SHA-256).

Uso:
    python scripts/build_distribution.py [--skip-installer] [--clean]
"""

import os
import sys
import shutil
import hashlib
import argparse
import subprocess
from pathlib import Path

VERSION = "2.0.0"
APP_NAME = "AutoRod"
ROOT_DIR = Path(__file__).resolve().parent.parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
RELEASE_DIR = ROOT_DIR / "release_artifacts"
SPEC_FILE = ROOT_DIR / "distribution" / "windows" / "autorod.spec"
ISS_FILE = ROOT_DIR / "distribution" / "installer" / "autorod_setup.iss"


def calculate_sha256(file_path: Path) -> str:
    """Calcula el hash criptográfico SHA-256 de un archivo."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def find_inno_setup_compiler() -> str | None:
    """Localiza el compilador de Inno Setup (ISCC.exe) en el sistema."""
    iscc_cmd = shutil.which("iscc")
    if iscc_cmd:
        return iscc_cmd

    default_paths = [
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LocalAppData", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    for path in default_paths:
        if path.is_file():
            return str(path)
    return None


def clean_artifacts() -> None:
    """Limpia carpetas residuales de compilaciones previas."""
    print("🧹 [1/5] Limpiando directorios de salida antiguos...")
    for dir_path in [BUILD_DIR, DIST_DIR, RELEASE_DIR, ROOT_DIR / "dist_installer"]:
        if dir_path.exists():
            shutil.rmtree(dir_path, ignore_errors=True)
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    print("   ✓ Carpetas limpias y preparadas.")


def run_pyinstaller() -> bool:
    """Ejecuta PyInstaller con el archivo de especificación oficial."""
    print("🔨 [2/5] Compilando ejecutable con PyInstaller (Modo Seguro: No-UPX + Manifest)...")
    if not SPEC_FILE.is_file():
        print(f"❌ Error: Archivo spec no encontrado: {SPEC_FILE}")
        return False

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        str(SPEC_FILE),
    ]

    try:
        res = subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)
        exe_path = DIST_DIR / APP_NAME / f"{APP_NAME}.exe"
        if not exe_path.is_file():
            print(f"❌ Error: No se encontró el ejecutable generado en {exe_path}")
            return False
        print(f"   ✓ Ejecutable compilado exitosamente: {exe_path}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error durante la compilación de PyInstaller: {exc}")
        return False


def build_installer() -> bool:
    """Compila el instalador con Inno Setup si está disponible."""
    print("📦 [3/5] Compilando instalador asistido de Windows (Inno Setup 6)...")
    iscc_path = find_inno_setup_compiler()
    if not iscc_path:
        print("   ⚠️  ISCC.exe (Inno Setup 6) no está instalado en este equipo.")
        print("      Para generar el instalador .exe localmente, instálalo con:")
        print("      winget install JRSoftware.InnoSetup")
        print("      (El pipeline de GitHub Actions lo compilará automáticamente en la nube).")
        return False

    if not ISS_FILE.is_file():
        print(f"❌ Error: Archivo ISS no encontrado en {ISS_FILE}")
        return False

    try:
        subprocess.run([iscc_path, str(ISS_FILE)], cwd=str(ROOT_DIR), check=True)
        installer_dir = ROOT_DIR / "dist_installer"
        installer_exe = installer_dir / f"{APP_NAME}-v{VERSION}-Setup.exe"
        if installer_exe.is_file():
            target_path = RELEASE_DIR / installer_exe.name
            shutil.copy2(installer_exe, target_path)
            print(f"   ✓ Instalador generado exitosamente: {target_path}")
            return True
        else:
            print("❌ No se encontró el archivo de salida del instalador.")
            return False
    except subprocess.CalledProcessError as exc:
        print(f"❌ Error al compilar con Inno Setup: {exc}")
        return False


def build_portable_zip() -> bool:
    """Genera el paquete portable comprimido (.zip)."""
    print("🗜️  [4/5] Creando paquete portable .zip...")
    source_dir = DIST_DIR / APP_NAME
    if not source_dir.is_dir():
        print(f"❌ Directorio fuente no encontrado: {source_dir}")
        return False

    zip_filename = f"{APP_NAME}-v{VERSION}-Portable"
    archive_base = RELEASE_DIR / zip_filename

    try:
        shutil.make_archive(str(archive_base), "zip", root_dir=str(DIST_DIR), base_dir=APP_NAME)
        final_zip = archive_base.with_suffix(".zip")
        print(f"   ✓ Paquete portable creado exitosamente: {final_zip}")
        return True
    except Exception as exc:
        print(f"❌ Error al empaquetar archivo ZIP: {exc}")
        return False


def generate_checksums() -> None:
    """Calcula y guarda los hashes criptográficos SHA-256 de los artefactos producidos."""
    print("🔒 [5/5] Generando hashes criptográficos de integridad (SHA-256)...")
    checksums_file = RELEASE_DIR / "SHA256SUMS.txt"
    entries = []

    for file_path in sorted(RELEASE_DIR.glob("*")):
        if file_path.is_file() and file_path.name != "SHA256SUMS.txt":
            sha256 = calculate_sha256(file_path)
            size_mb = file_path.stat().st_size / (1024 * 1024)
            entries.append((file_path.name, sha256, size_mb))

    with open(checksums_file, "w", encoding="utf-8") as f:
        for name, sha, size_mb in entries:
            f.write(f"{sha}  {name}\n")

    print(f"   ✓ Archivo de verificación generado: {checksums_file}\n")
    print("=" * 70)
    print("✨ RESUMEN DE ARTEFACTOS DE DISTRIBUCIÓN GENERADOS:")
    print("=" * 70)
    for name, sha, size_mb in entries:
        print(f"📦 Archivo : {name} ({size_mb:.2f} MB)")
        print(f"🔑 SHA-256 : {sha}\n")
    print("=" * 70)


def main() -> int:
    parser = argparse.ArgumentParser(description="AutoRod Distribution Builder")
    parser.add_argument("--skip-installer", action="store_true", help="Omitir generación del instalador Inno Setup")
    parser.add_argument("--clean", action="store_true", help="Solo limpiar artefactos anteriores")
    args = parser.parse_args()

    clean_artifacts()
    if args.clean:
        return 0

    print("=" * 70)
    print(f"🚀 INICIANDO PIPELINE DE DISTRIBUCIÓN: {APP_NAME} v{VERSION}")
    print("=" * 70)

    if not run_pyinstaller():
        return 1

    if not args.skip_installer:
        build_installer()

    if not build_portable_zip():
        return 1

    generate_checksums()
    print("🎉 Pipeline completado con éxito. Artefactos listos en 'release_artifacts/'.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
