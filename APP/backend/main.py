# backend/main.py
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

import webview

from database import save_mood
from empatIA_service import EmpatIAService
from security import encrypt_text  # 🔐 NOVO


def get_html_path() -> Path:
    """
    Retorna o caminho do index.html tanto em modo desenvolvimento
    quanto empacotado em .exe pelo PyInstaller.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Rodando empacotado (main.exe). O PyInstaller monta tudo em _MEIPASS.
        base_dir = Path(sys._MEIPASS)
    else:
        # Rodando via "python main.py" (dev).
        # Estamos em APP/backend, então o pai do pai é APP/.
        base_dir = Path(__file__).resolve().parent.parent

    return base_dir / "frontend" / "pages" / "index.html"


# BASE_DIR continua valendo para arquivos locais do backend (logs, etc.)
BASE_DIR = Path(__file__).resolve().parent
html_path = get_html_path()

# pasta de logs locais
storage_path = BASE_DIR / "data"
storage_path.mkdir(exist_ok=True)

# 🔒 Agora o arquivo de log passa a ser criptografado (.enc)
log_file = storage_path / "moods_log.enc"


class API:
    def __init__(self) -> None:
        self.ia = EmpatIAService()  # IA real + fallback

    def submit_mood(self, payload: dict) -> dict:
        mood = payload.get("mood")
        reason = payload.get("reason")

        ai_text = self.ia.ia_response(mood, reason)

        # 1) Salva localmente (CRIPTOGRAFADO)
        self._save_local_encrypted(mood, reason, ai_text)

        # 2) Salva no Supabase
        try:
            save_mood(mood, reason, ai_text)
        except Exception as e:
            print("Erro ao salvar no Supabase:", e)

        return {"ok": True, "ai_response": ai_text}

    def _save_local_encrypted(self, mood, reason, ai_text) -> None:
        """
        Log local CRIPTOGRAFADO em arquivo.

        Mesmo que alguém copie o arquivo moods_log.enc, não conseguirá
        ler os dados sem a chave empatIA.key.
        """
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mood": mood,
            "reason": reason,
            "ai_response": ai_text,
        }
        plain = json.dumps(entry, ensure_ascii=False)

        try:
            cipher = encrypt_text(plain)

            # escreve em modo binário, uma linha por registro
            with log_file.open("ab") as f:
                f.write(cipher + b"\n")

        except Exception as e:
            print("Erro ao salvar log local criptografado:", e)


if __name__ == "__main__":
    print("Carregando HTML em:", html_path, "existe?", html_path.exists())

    api = API()

    window = webview.create_window(
        "EmpatIA - Termômetro Emocional",
        html_path.as_uri(),
        js_api=api,
        width=1000,
        height=800,
        text_select=False,
    )
    webview.start()
