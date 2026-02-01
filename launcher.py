import os
import sys
import time
import socket
import subprocess
from pathlib import Path
import webbrowser

APP_HOST = "127.0.0.1"
APP_PORT = 8501
WAIT_SECONDS = 120  # aumentamos la espera

def appdata_log_path() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
    folder = base / "CPF"
    folder.mkdir(parents=True, exist_ok=True)
    return folder / "cpf.log"

def log(msg: str):
    p = appdata_log_path()
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with p.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False

def get_workdir() -> str:
    # En PyInstaller, los archivos pueden estar en _MEIPASS (onefile) o en carpeta (onedir)
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS  # type: ignore
    return str(Path(__file__).resolve().parent)

def main():
    # limpiar log al inicio (opcional)
    log("========== INICIO CPF ==========")

    workdir = get_workdir()
    log(f"Workdir: {workdir}")

    # Ruta al app.py dentro del paquete
    app_path = Path(workdir) / "app.py"
    if not app_path.exists():
        log(f"ERROR: No existe app.py en {app_path}")
        raise RuntimeError(f"No se encontró app.py en {app_path}")

    # Ejecutamos streamlit con el mismo python embebido
    cmd = [
        sys.executable, "-m", "streamlit", "run", str(app_path),
        "--server.headless=true",
        f"--server.address={APP_HOST}",
        f"--server.port={APP_PORT}",
        "--browser.gatherUsageStats=false",
    ]

    log(f"Ejecutando: {' '.join(cmd)}")

    # Abrimos log en modo append para capturar salida
    log_file = appdata_log_path().open("a", encoding="utf-8")

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=workdir,
            stdout=log_file,
            stderr=log_file,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
    except Exception as e:
        log(f"ERROR al iniciar streamlit: {e}")
        raise

    # Esperar a que el puerto esté activo
    start = time.time()
    while time.time() - start < WAIT_SECONDS:
        if port_open(APP_HOST, APP_PORT):
            url = f"http://{APP_HOST}:{APP_PORT}"
            log(f"Servidor OK en {url}")
            webbrowser.open(url)
            break
        time.sleep(0.5)
    else:
        log("ERROR: Streamlit no levantó a tiempo. Ver logs anteriores para detalle.")
        # matar el proceso si quedó vivo
        try:
            proc.terminate()
        except Exception:
            pass
        raise RuntimeError(
            f"No levantó el servidor en {APP_HOST}:{APP_PORT}. Revisá el log en: {appdata_log_path()}"
        )

    # Mantener vivo el proceso
    try:
        proc.wait()
    finally:
        log("========== FIN CPF ==========")

if __name__ == "__main__":
    main()
