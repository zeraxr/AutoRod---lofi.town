"""Utilidades de soporte para la interfaz Flet de AutoRod."""

from typing import Any
from pathlib import Path
import sys
import flet as ft


def get_asset_path(relative_path: str) -> Path:
    """
    Resuelve la ruta absoluta de un recurso dentro de assets tanto en desarrollo
    como empaquetado con PyInstaller / ejecutable standalone.
    """
    # 1. Relativo al paquete src/autorod/assets
    pkg_assets = Path(__file__).resolve().parents[3] / "assets" / relative_path
    if pkg_assets.is_file():
        return pkg_assets

    # 2. Relativo al directorio de trabajo
    cwd_candidate = Path("src/autorod/assets") / relative_path
    if cwd_candidate.is_file():
        return cwd_candidate.resolve()

    # 3. Soporte para ejecutable congelado
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).parent
        cand1 = exe_dir / "assets" / relative_path
        if cand1.is_file():
            return cand1
        cand2 = exe_dir / "_internal" / "autorod" / "assets" / relative_path
        if cand2.is_file():
            return cand2

    return pkg_assets


def get_control_page(control: ft.Control | None) -> ft.Page | None:
    """
    Retorna la página a la que pertenece el control de forma 100% segura.
    En Flet 1.0+, acceder a control.page cuando no está en página lanza RuntimeError.
    Esta función intercepta la excepción y retorna None.
    """
    if control is None:
        return None
    try:
        return control.page
    except Exception:
        return None


def is_control_mounted(control: ft.Control | None) -> bool:
    """Verifica si un control está montado en una página activa sin lanzar RuntimeError."""
    return get_control_page(control) is not None


def safe_update(control: ft.Control | None) -> None:
    """Actualiza un control de Flet de forma segura, ignorando si aún no está montado en página."""
    if control is None:
        return
    try:
        page = get_control_page(control)
        if page is not None:
            control.update()
    except Exception:
        pass


def safe_page_update(page: ft.Page | None) -> None:
    """
    Sincroniza y fuerza el redibujado de la página raíz de Flet.
    Esencial para que Flutter Desktop en Windows no congele el pintado de frames
    y refresque métricas/video cuando la ventana pierde el foco o corre en segundo plano.
    """
    if page is None:
        return
    try:
        page.update()
    except Exception:
        pass


def terminate_child_processes() -> None:
    """
    Termina todos los procesos secundarios y descendientes (como flet.exe / Flutter runtime)
    para evitar que queden ventanas zombi congeladas con la pantalla 'Working...'
    cuando el proceso maestro de Python se cierra o se ejecuta la parada de emergencia.
    """
    import os
    import sys
    import subprocess
    import ctypes
    from ctypes import wintypes

    current_pid = os.getpid()

    # 1. Terminación directa Win32 Toolhelp32 de todo el árbol de procesos hijos y nietos
    try:
        kernel32 = ctypes.windll.kernel32
        TH32CS_SNAPPROCESS = 0x00000002
        PROCESS_TERMINATE = 0x0001

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", wintypes.DWORD),
                ("cntUsage", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
                ("th32ModuleID", wintypes.DWORD),
                ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD),
                ("pcPriClassBase", wintypes.LONG),
                ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260)
            ]

        h_snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if h_snap != -1 and h_snap != 0xFFFFFFFFFFFFFFFF:
            pe = PROCESSENTRY32()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32)

            child_pids: set[int] = set()
            all_procs: list[tuple[int, int, str]] = []

            if kernel32.Process32First(h_snap, ctypes.byref(pe)):
                while True:
                    exe_name = pe.szExeFile.decode("latin-1", errors="ignore").lower()
                    all_procs.append((pe.th32ProcessID, pe.th32ParentProcessID, exe_name))
                    if pe.th32ParentProcessID == current_pid:
                        child_pids.add(pe.th32ProcessID)
                    if not kernel32.Process32Next(h_snap, ctypes.byref(pe)):
                        break

            # Búsqueda recursiva de procesos nietos/descendientes
            added = True
            while added:
                added = False
                for pid, ppid, _ in all_procs:
                    if ppid in child_pids and pid not in child_pids:
                        child_pids.add(pid)
                        added = True

            # Terminar todos los procesos del árbol descendiente (excluyendo estrictamente el proceso actual)
            for pid, ppid, exe_name in all_procs:
                if (pid in child_pids or (exe_name.startswith("flet") and ppid == current_pid)) and pid != current_pid:
                    h_proc = kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
                    if h_proc:
                        kernel32.TerminateProcess(h_proc, 0)
                        kernel32.CloseHandle(h_proc)

            kernel32.CloseHandle(h_snap)
    except Exception:
        pass

    # 2. Respaldo selectivo con taskkill para procesos hijos (nunca sobre el proceso actual)
    if sys.platform == "win32":
        for cpid in child_pids if 'child_pids' in locals() else []:
            if cpid != current_pid:
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/PID", str(cpid)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=0.4,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                    )
                except Exception:
                    pass


def close_app_window(page: ft.Page | None) -> None:
    """
    Cierra la ventana nativa de Flet de forma asíncrona segura.
    En Flet 1.0+, page.window.destroy() es una corrutina async que debe ser
    planificada en el loop de eventos; de lo contrario produce RuntimeWarning
    y deja la interfaz en carga infinita.
    """
    if page is None:
        return

    if not hasattr(page, "window"):
        terminate_child_processes()
        return

    async def _destroy_coro() -> None:
        try:
            await page.window.destroy()
        except Exception:
            pass

    try:
        fut = page.run_task(_destroy_coro)
        try:
            fut.result(timeout=0.4)
        except Exception:
            pass
    except Exception:
        pass
    finally:
        terminate_child_processes()
