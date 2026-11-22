import os
import signal
import subprocess
import sys
import time

def main():
    # 1. Ellenőrizzük a létező fájlokat
    if not os.path.exists("backend/main.py") or not os.path.exists("client/app.py"):
        print("❌ Hiba: Nem találom a 'backend/main.py'-t vagy a 'client/app.py'-t!")
        return

    print("🚀 FastAPI Backend indítása...")
    # 2. Az --app-dir backend megmondja az uvicornnak, hogy a backend mappából dolgozzon,
    # így a belső importok (core, vision, invoices) tökéletesen fognak működni.
    backend_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--app-dir", "backend", "--reload", "--host", "127.0.0.1", "--port", "8000"]
    )

    time.sleep(2)

    print("⚡ Streamlit Frontend indítása...")
    streamlit_process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "client/app.py",
            "--server.maxUploadSize",
            "50",
        ]
    )

    def signal_handler(sig, frame):
        print("\n🛑 Leállítás folyamatban...")
        backend_process.terminate()
        streamlit_process.terminate()
        backend_process.wait()
        streamlit_process.wait()
        print("👋 Minden szolgáltatás leállítva.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        backend_process.wait()
        streamlit_process.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
