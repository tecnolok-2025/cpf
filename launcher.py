import subprocess
import sys
import webbrowser
import time

def main():
    p = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "app.py",
         "--server.headless=true", "--server.port=8501"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    time.sleep(3)
    webbrowser.open("http://localhost:8501")

    # 🔴 CLAVE: mantener vivo el ejecutable
    p.wait()

if __name__ == "__main__":
    main()
