import os
import sys
import time
import socket
import subprocess
import webbrowser
from pathlib import Path

APP_NAME = "CPF"
HOST = "127.0.0.1"
PORT = 8501


def _base_dir() -> Path:
    """
    When bundled with PyInstaller (onefile), sys._MEIPASS points to the temp extract folder.
    When running from source, use the folder of this file.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parent


def _log_path() -> Path:
    # Write logs to %LOCALAPPDATA%\CPF\cpf.log (or equivalent)
    local = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    log_dir = local / APP_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "cpf.log"


def _wait_port(host: str, port: int, timeout_s: int = 90) -> bool:
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False


def main():
    base = _base_dir()
    app_path = base / "app.py"  # <- tu app principal es app.py

    log_file = _log_path()
    with open(log_file, "a", encoding="utf-8") as lf:
        lf.write("\n--- Launch CPF ---\n")
        lf.write(f"base_dir={base}\n")
        lf.write(f"app_path={app_path}\n")

        if not app_path.exists():
            lf.write("ERROR: app.py not found next to launcher bundle.\n")
            raise FileNotFoundError(f"No se encontró app.py en {app_path}")

        # IMPORTANT: run Streamlit via python -m streamlit (robust for PyInstaller)
        cmd = [
            sys.executable, "-m", "streamlit", "run", str(app_path),
            "--server.address", HOST,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ]

        lf.write("CMD=" + " ".join(cmd) + "\n")

        # Start streamlit process
        # (No console window if you build with --windowed/--noconsole)
        proc = subprocess.Popen(
            cmd,
            stdout=lf,
            stderr=lf,
            cwd=str(base),
        )

        # Wait until port is ready, then open browser
        if _wait_port(HOST, PORT, timeout_s=90):
            url = f"http://{HOST}:{PORT}"
            lf.write(f"Opening browser: {url}\n")
            webbrowser.open(url)
        else:
            lf.write("ERROR: Streamlit did not start (port not open).\n")
            # Try to terminate to avoid hanging background process
            try:
                proc.terminate()
            except Exception:
                pass
            raise RuntimeError(
                f"No levantó el servidor en {HOST}:{PORT}. "
                f"Revisá el log en: {log_file}"
            )

        # Keep running while streamlit runs
        try:
            proc.wait()
        finally:
            lf.write("--- CPF exit ---\n")


if __name__ == "__main__":
    main()
