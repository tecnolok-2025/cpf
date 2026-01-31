import subprocess
import sys
import webbrowser
import time
import socket

HOST = "127.0.0.1"
PORT = 8501

def wait_port(host: str, port: int, timeout_sec: int = 90) -> bool:
    """Espera hasta que haya algo escuchando en host:port."""
    end = time.time() + timeout_sec
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def main():
    # Arranca Streamlit (no abre navegador todavía)
    p = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless=true",
            f"--server.port={PORT}",
            "--server.address=127.0.0.1",
            "--browser.gatherUsageStats=false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Espera a que el servidor esté listo
    if wait_port(HOST, PORT, timeout_sec=90):
        webbrowser.open(f"http://localhost:{PORT}")
    else:
        # Si no levantó, cortamos para no dejar procesos colgados
        try:
            p.terminate()
        except Exception:
            pass

    # Mantener vivo el ejecutable mientras Streamlit corre
    p.wait()

if __name__ == "__main__":
    main()
