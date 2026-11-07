"""Módulo de detección del entorno de ejecución (Portable vs Instalación por Setup)."""

from enum import Enum
from pathlib import Path
import os
import sys
import logging

logger = logging.getLogger(__name__)


class InstallationType(str, Enum):
    """Tipo de empaquetado o instalación de AutoRod en el sistema operativo."""
    PORTABLE = "portable"
    INSTALLED = "installed"
    DEVELOPMENT = "development"


def detect_installation_type() -> InstallationType:
    """
    Detecta de forma heurística y determinista si AutoRod se ejecuta como:
    - 'installed': Instalado formalmente en el sistema mediante instalador/setup (Inno Setup, NSIS, WiX/MSI).
    - 'portable': Ejecutable autónomo extraído de archivo .zip en carpeta de usuario/descargas/pendrive.
    - 'development': Ejecución interpretada directa mediante Python sin empaquetar.

    Permite anulación para pruebas unitarias mediante la variable de entorno 'AUTOROD_FORCE_INSTALL_TYPE'.
    """
    # 0. Override explícito para pruebas y testing
    forced = os.environ.get("AUTOROD_FORCE_INSTALL_TYPE", "").strip().lower()
    if forced == "installed":
        return InstallationType.INSTALLED
    elif forced == "portable":
        return InstallationType.PORTABLE
    elif forced == "development":
        return InstallationType.DEVELOPMENT

    # 1. Ejecución en entorno de desarrollo (código fuente Python puro)
    if not getattr(sys, "frozen", False) and "__compiled__" not in globals():
        return InstallationType.DEVELOPMENT

    exe_path = Path(sys.executable).resolve()
    exe_dir = exe_path.parent

    # 2. Comprobación de artefactos de desinstalador creados por instaladores de Windows
    uninstaller_markers = (
        "unins000.exe",
        "unins001.exe",
        "uninstall.exe",
        "unins000.dat",
        "uninstall.dat"
    )
    if any((exe_dir / marker).exists() for marker in uninstaller_markers):
        logger.debug("[UPDATER] Detectado instalador por presencia de uninstaller: %s", exe_dir)
        return InstallationType.INSTALLED

    # 3. Comprobación de rutas estándar del sistema para programas instalados
    program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)")
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    local_programs = os.path.join(local_app_data, "Programs") if local_app_data else ""

    exe_dir_str = str(exe_dir).lower()
    if (
        (program_files and exe_dir_str.startswith(str(program_files).lower()))
        or (program_files_x86 and exe_dir_str.startswith(str(program_files_x86).lower()))
        or (local_programs and exe_dir_str.startswith(str(local_programs).lower()))
    ):
        logger.debug("[UPDATER] Detectado instalador por ruta estándar del sistema: %s", exe_dir)
        return InstallationType.INSTALLED

    # 4. Comprobación de claves de registro de desinstalación de Windows (HKCU / HKLM)
    if sys.platform == "win32":
        try:
            import winreg
            for root_key in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                try:
                    with winreg.OpenKey(root_key, r"Software\Microsoft\Windows\CurrentVersion\Uninstall") as uninstall_key:
                        num_subkeys = winreg.QueryInfoKey(uninstall_key)[0]
                        for i in range(num_subkeys):
                            try:
                                subkey_name = winreg.EnumKey(uninstall_key, i)
                                if "autorod" in subkey_name.lower():
                                    with winreg.OpenKey(uninstall_key, subkey_name) as app_key:
                                        install_loc, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                                        if install_loc and Path(install_loc).resolve() == exe_dir:
                                            logger.debug("[UPDATER] Detectado instalador por registro Windows: %s", subkey_name)
                                            return InstallationType.INSTALLED
                            except Exception:
                                continue
                except Exception:
                    continue
        except Exception as exc:
            logger.debug("[UPDATER] Omitida comprobación de registro: %s", exc)

    # 5. Si no cumple ninguno de los anteriores, se trata de una versión Portable
    logger.debug("[UPDATER] Detectada versión Portable: %s", exe_dir)
    return InstallationType.PORTABLE


def is_installed_setup() -> bool:
    """
    Retorna True si AutoRod está instalado formalmente mediante un instalador/setup,
    o False si es una versión portable autónoma o entorno de desarrollo.
    """
    return detect_installation_type() == InstallationType.INSTALLED
