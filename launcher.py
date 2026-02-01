import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8501

APP_NAME = "CPF"
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / APP_NAME
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "cpf.log"


def log(msg: str) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")


def wait_port(host: str, port: int, timeout: int = 90) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def _show_error(message: str) -> None:
    # Un solo popup amigable (evita cascadas de ventanas)
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(APP_NAME, message)
        root.destroy()
    except Exception:
        print(message)


def open_browser_when_ready():
    try:
        if wait_port(HOST, PORT, timeout=90):
            webbrowser.open(f"http://{HOST}:{PORT}")
        else:
            raise RuntimeError(f"No levantó el servidor en {HOST}:{PORT}. Revisá el log en: {LOG_FILE}")
    except Exception as e:
        log(f"ERROR al abrir navegador: {e}")
        _show_error(str(e))


def main() -> None:
    try:
        log("Iniciando CPF...")

        # Ajustes por env (además de flags)
        os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
        os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
        os.environ.setdefault("STREAMLIT_SERVER_ADDRESS", HOST)
        os.environ.setdefault("STREAMLIT_SERVER_PORT", str(PORT))

        # app.py vive en la carpeta extraída por PyInstaller (o al lado si corrés .py normal)
        app_path = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "app.py"
        if not app_path.exists():
            raise FileNotFoundError(f"No encuentro app.py en: {app_path}")

        # Abrir navegador cuando el server esté listo (en paralelo)
        threading.Thread(target=open_browser_when_ready, daemon=True).start()

        # IMPORTANTÍSIMO:
        # Ejecutar Streamlit en el MISMO proceso.
        # No usar subprocess con sys.executable, porque en PyInstaller eso re-ejecuta el mismo .exe y puede entrar en bucle.
        try:
            from streamlit.web import cli as stcli
        except Exception as e:
            raise RuntimeError(
                "No se pudo importar Streamlit dentro del ejecutable. "
                "Revisá que PyInstaller esté incluyendo Streamlit. "
                f"Detalle: {e}"
            )

        sys.argv = [
            "streamlit",
            "run",
            str(app_path),
            "--server.headless=true",
            f"--server.address={HOST}",
            f"--server.port={PORT}",
            "--browser.gatherUsageStats=false",
        ]
        log(f"Ejecutando: {' '.join(sys.argv)}")
        stcli.main()

    except Exception as e:
        log(f"FATAL: {e}")
        _show_error(str(e))
        raise


if __name__ == "__main__":
    main()
