"""
PyInstaller entry point — starts Streamlit and opens a browser tab.
"""
import os
import sys
import threading
import webbrowser


def resource(rel):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def open_browser(url, delay=3):
    def _open():
        import time
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


if __name__ == "__main__":
    os.environ["GANJOOR_DB"] = resource("ganjoor.db")

    port = "8501"
    url  = f"http://localhost:{port}"

    open_browser(url)

    sys.argv = [
        "streamlit", "run",
        resource("ganjoor_app.py"),
        f"--server.port={port}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]

    from streamlit.web import cli as stcli
    sys.exit(stcli.main())
