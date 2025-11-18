from __future__ import annotations

from collections import Counter
from datetime import datetime, date, timedelta
from pathlib import Path

import webview

from database import get_mood_stats
from empatIA_service import EmpatIADashboardService, EmpatIAContext


BASE_DIR = Path(__file__).resolve().parent
# index.html em: frontend/pages/index.html
html_path = BASE_DIR.parent / "frontend" / "pages" / "index.html"


class API:
    """
    API exposta para o JavaScript via pywebview.
    O JS chama: window.pywebview.api.get_dashboard_data(period)
    """

    # campos possíveis de data/hora nos registros
    TIME_FIELDS = ["created_at", "inserted_at", "timestamp", "time", "data", "date"]

    def __init__(self) -> None:
        # serviço de IA exclusivo do dashboard
        self.ia_service = EmpatIADashboardService()

    # ---------- HELPERS DE DATA ----------

    def _extract_row_date(self, row) -> date | None:
        """
        Tenta converter algum campo de data/hora do registro em date.
        """
        for field in self.TIME_FIELDS:
            if field in row and row[field]:
                value = row[field]

                # string ISO
                if isinstance(value, str):
                    try:
                        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                        return dt.date()
                    except Exception:
                        continue

                # datetime
                if isinstance(value, datetime):
                    return value.date()

        return None

    def _filter_rows_by_period(self, rows, period: str):
        """
        Filtra registros pelo período:
        - daily   : hoje
        - weekly  : últimos 7 dias
        - monthly : mês atual
        - yearly  : ano atual

        Retorna: (lista[(date, row)], start_date, end_date)
        """
        today = date.today()

        if period == "daily":
            start = today
        elif period == "weekly":
            start = today - timedelta(days=6)
        elif period == "monthly":
            start = today.replace(day=1)
        elif period == "yearly":
            start = today.replace(month=1, day=1)
        else:
            # fallback: sem filtro (quase infinito)
            start = date.min

        filtered: list[tuple[date, dict]] = []

        for row in rows:
            d = self._extract_row_date(row)
            if d is None:
                continue
            if start <= d <= today:
                filtered.append((d, row))

        return filtered, start, today

    # ---------- MÉTODO CHAMADO PELO FRONT ----------

    def get_dashboard_data(self, period: str = "daily") -> dict:
        """
        Lê registros do Supabase via get_mood_stats,
        aplica filtro de período e devolve dados agregados
        para o dashboard.

        period: "daily" | "weekly" | "monthly" | "yearly"
        """
        print(f"[PY] get_dashboard_data chamado com period={period!r}")

        try:
            raw_stats = get_mood_stats() or {}
        except Exception as e:
            print("[PY] Erro ao buscar dados do Supabase:", e)
            return {
                "total_entries": 0,
                "most_frequent_mood": None,
                "mood_counts": {},
                "weekly_trend": [],
                "ai_general_advice": (
                    "Não foi possível carregar os dados no momento. "
                    "Verifique a conexão e tente novamente."
                ),
            }

        # Se vier dict com rows, usa; se vier lista, assume que já é lista de registros
        if isinstance(raw_stats, dict):
            rows = raw_stats.get("rows", [])
        else:
            rows = raw_stats

        print(f"[PY] Registros recebidos: {len(rows)}")

        # --- aplica filtro de período ---
        filtered, start, end = self._filter_rows_by_period(rows, period)
        print(f"[PY] Registros após filtro ({period}): {len(filtered)}  | intervalo: {start} -> {end}")

        mood_counts: Counter = Counter()
        counts_by_date: dict[str, int] = {}

        for d, row in filtered:
            mood = (row.get("mood") or "").strip()
            if mood:
                mood_counts[mood] += 1

            d_str = d.isoformat()
            counts_by_date[d_str] = counts_by_date.get(d_str, 0) + 1

        total_entries = sum(mood_counts.values())

        # emoção mais frequente
        most_frequent_mood = None
        if mood_counts:
            most_frequent_mood = max(mood_counts, key=mood_counts.get)

        # série temporal: todos os dias no intervalo [start, end]
        days_range = (end - start).days
        if days_range < 0:
            days_range = 0

        labels = [
            (start + timedelta(days=i)).isoformat()
            for i in range(days_range + 1)
        ]

        weekly_trend = [
            {"date": d, "count": counts_by_date.get(d, 0)}
            for d in labels
        ]

        # -------- IA do dashboard (EmpatIADashboardService) --------
        ctx = EmpatIAContext(
            period=period,
            start_date=start,
            end_date=end,
        )
        ai_advice = self.ia_service.build_advice(mood_counts, ctx)

        result = {
            "total_entries": total_entries,
            "most_frequent_mood": most_frequent_mood,
            "mood_counts": dict(mood_counts),
            "weekly_trend": weekly_trend,
            "ai_general_advice": ai_advice,
        }

        print(f"[PY] Dashboard stats ({period}) gerados:", result)
        return result

    # opcional: usado pelo botão "Voltar" (se existir no HTML)
    def close_app(self):
        webview.destroy_window()


if __name__ == "__main__":
    print("Carregando Dashboard HTML em:", html_path)
    print("Arquivo HTML existe?", html_path.exists())

    api = API()

    if not html_path.exists():
        html_content = """
        <html>
            <head><title>EmpatIA Dashboard</title></head>
            <body>
                <h1>EmpatIA Dashboard</h1>
                <p>Arquivo index.html não encontrado no caminho configurado.</p>
            </body>
        </html>
        """
        window = webview.create_window(
            "EmpatIA Dashboard - Clima Emocional",
            html=html_content,
            js_api=api,
            width=1200,
            height=800,
            text_select=False,
        )
    else:
        window = webview.create_window(
            "EmpatIA Dashboard - Clima Emocional",
            html_path.as_uri(),
            js_api=api,
            width=1200,
            height=800,
            text_select=False,
        )

    webview.start()
