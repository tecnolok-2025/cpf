import subprocess
import sys
import webbrowser
import time
import socket

HOST = "127.0.0.1"
PORT = 8501

def wait_port(host: str, port: int, timeout_sec: int = 90) -> bool:
    """Wait until something is listening on host:port."""
    end = time.time() + timeout_sec
    while time.time() < end:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def main():
    # Start Streamlit (do not open browser yet)
    p = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.headless=true",
            f"--server.port={PORT}",
            f"--server.address={HOST}",
            "--browser.gatherUsageStats=false",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # Wait for server, then open ONE browser tab
    if wait_port(HOST, PORT, timeout_sec=90):
        webbrowser.open(f"http://localhost:{PORT}")
    else:
        try:
            p.terminate()
        except Exception:
            pass

    # Keep the process alive while Streamlit runs
    p.wait()

if __name__ == "__main__":
    main()
