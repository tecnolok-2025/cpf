import os
import sys
import time
import socket
import subprocess
from pathlib import Path
import webbrowser

HOST = "127.0.0.1"
PORT = 8501
WAIT_SECONDS = 120

def log_path():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    folder = base / "CPF"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "cpf.log"

def log(msg: str):
    with open(log_path(), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")

def port_open() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=0.5):
            return True
    except Exception:
        return False

def workdir() -> str:
    # En PyInstaller, _MEIPASS apunta a la carpeta temporal donde se extrae todo
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def main():
    log("=== INICIO CPF ===")

    wd = workdir()
    app = os.path.join(wd, "app.py")

    if not os.path.exists(app):
        log("ERROR: app.py no encontrado")
        raise RuntimeError("No se encontró app.py")

    # IMPORTANTE:
    # Forzamos developmentMode=false para evitar el error:
    # "server.port does not work when global.developmentMode is true"
    cmd = [
        sys.executable, "-m", "streamlit", "run", app,
        "--global.developmentMode=false",
        "--server.headless=true",
        f"--server.address={HOST}",
        f"--server.port={PORT}",
        "--browser.gatherUsageStats=false",
    ]

    log("Ejecutando Streamlit: " + " ".join(cmd))

    log_file = open(log_path(), "a", encoding="utf-8")

    proc = subprocess.Popen(
        cmd,
        cwd=wd,
        stdout=log_file,
        stderr=log_file,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )

    start = time.time()
    while time.time() - start < WAIT_SECONDS:
        # Si el proceso murió, cortamos y dejamos log
        if proc.poll() is not None:
            log("ERROR: Streamlit terminó antes de levantar. Ver cpf.log")
            raise RuntimeError("Streamlit terminó antes de levantar. Revisá cpf.log")

        if port_open():
            url = f"http://{HOST}:{PORT}"
            log("Servidor OK → " + url)
            webbrowser.open(url)
            proc.wait()
            return

        time.sleep(0.5)

    log("ERROR: Streamlit no levantó en el tiempo de espera")
    proc.terminate()
    raise RuntimeError("Streamlit no levantó. Revisá el log en %LOCALAPPDATA%\\CPF\\cpf.log")

if __name__ == "__main__":
    main()
