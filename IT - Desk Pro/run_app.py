"""
IT DeskPro - Application Runner
Launches Streamlit app directly via bootstrap for robust daemon & background execution.
"""
import sys
from pathlib import Path
from streamlit.web import bootstrap

if __name__ == "__main__":
    app_path = str(Path(__file__).resolve().parent / "app.py")
    flag_options = {
        "server.port": 8501,
        "server.headless": True,
        "browser.serverAddress": "localhost",
        "server.enableCORS": False,
        "server.enableXsrfProtection": False,
    }
    bootstrap.run(app_path, False, [], flag_options)

