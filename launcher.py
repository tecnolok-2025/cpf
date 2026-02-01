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

def log(msg):
    with open(log_path(), "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} | {msg}\n")

def port_open():
    try:
        with socket.create_connection((HOST, PORT), timeout=0.5):
            return True
    except:
        return False

def workdir():
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

    cmd = [
        sys.executable, "-m", "streamlit", "run", app,
        "--server.headless=true",
        f"--server.address={HOST}",
        f"--server.port={PORT}",
        "--browser.gatherUsageStats=false"
    ]

    log("Ejecutando Streamlit")

    log_file = open(log_path(), "a", encoding="utf-8")

    proc = subprocess.Popen(
        cmd,
        cwd=wd,
        stdout=log_file,
        stderr=log_file,
        stdin=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    )

    start = time.time()
    while time.time() - start < WAIT_SECONDS:
        if port_open():
            url = f"http://{HOST}:{PORT}"
            log("Servidor OK → " + url)
            webbrowser.open(url)
            proc.wait()
            return
        time.sleep(0.5)

    log("ERROR: Streamlit no levantó")
    proc.terminate()
    raise RuntimeError("Streamlit no levantó. Ver cpf.log")

if __name__ == "__main__":
    main()
