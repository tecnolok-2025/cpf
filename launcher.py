import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path


APP_NAME = "CPF"
HOST = "127.0.0.1"
PORT = 8501


def get_app_dir() -> Path:
    # Carpeta del programa (instalado) o del bundle (PyInstaller)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)  # pylint: disable=no-member
    return Path(__file__).resolve().parent


def get_log_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    log_dir = base / APP_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "cpf.log"


def wait_port(host: str, port: int, timeout_s: int = 60) -> bool:
    end = time.time() + timeout_s
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.25)
    return False


def run_streamlit(app_py: str, log_file: Path):
    # Ejecuta Streamlit programáticamente (mejor para PyInstaller)
    try:
        from streamlit.web import bootstrap

        # Redirigimos salida a log
        sys.stdout = open(log_file, "a", encoding="utf-8", buffering=1)
        sys.stderr = open(log_file, "a", encoding="utf-8", buffering=1)

        args = [
            "streamlit",
            "run",
            app_py,
            "--server.address", HOST,
            "--server.port", str(PORT),
            "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ]
        bootstrap.run(args[2], False, args, flag_options={})
    except Exception as e:
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"\n[LAUNCHER] ERROR al iniciar Streamlit: {e}\n")
        finally:
            raise


def main():
    app_dir = get_app_dir()
    log_path = get_log_path()
    app_path = app_dir / "app.py"

    # Si por algún motivo no está, lo dejamos claro en el log
    if not app_path.exists():
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[LAUNCHER] No encuentro app.py en: {app_path}\n")
        raise RuntimeError(f"No encuentro app.py en {app_path}")

    # Arrancar Streamlit en un thread
    t = threading.Thread(target=run_streamlit, args=(str(app_path), log_path), daemon=True)
    t.start()

    # Esperar a que levante el puerto y recién ahí abrir el navegador
    if wait_port(HOST, PORT, timeout_s=90):
        webbrowser.open(f"http://{HOST}:{PORT}")
        # Mantener vivo el proceso principal
        while True:
            time.sleep(1)
    else:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write("[LAUNCHER] Streamlit no levantó (no abrió el puerto). Revisar este log.\n")
        raise RuntimeError("Streamlit no levantó. Ver cpf.log")


if __name__ == "__main__":
    main()
