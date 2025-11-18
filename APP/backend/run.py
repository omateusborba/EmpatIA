import webview
from main import API
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
html_path = BASE_DIR / "Front-end" / "pages" / "index.html"

api = API()

webview.create_window(
    "EmpatIA - Termômetro Emocional",
    html_path.as_uri(),
    js_api=api,
    width=1000,
    height=800,
    confirm_close=True,
    text_select=True
)

webview.start()
