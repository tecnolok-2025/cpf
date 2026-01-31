import subprocess
import sys
import webbrowser
import time

def main():
    subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.headless=true", "--server.port=8501"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
    )
    time.sleep(2)
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    main()
