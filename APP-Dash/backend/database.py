# database.py
from supabase import create_client
import os
from collections import Counter
from datetime import date, datetime, timedelta, timezone

# ============================================
# Configuração do Supabase
# ============================================
SUPABASE_URL = "https://aotcapkawsmgoehavldk.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")

if not SUPABASE_KEY:
    raise RuntimeError("A variável de ambiente SUPABASE_API_KEY não está definida.")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ============================================
# Função para salvar humor
# ============================================
def save_mood(mood: str, reason: str | None, ai_text: str):
    """
    Salva um registro de humor na tabela t_mood.
    """
    data = {
        "mood": mood,
        "reason": reason,
        "ai_response": ai_text,
    }
    return supabase.table("t_mood").insert(data).execute()


# ============================================
# Função para montar estatísticas do dashboard
# ============================================
def get_mood_stats():
    """
    Busca todos os registros da tabela t_mood e devolve:

      - total: int
      - most_frequent: str | None
      - distribution: dict[mood -> contagem]
      - weekly_trend: lista [{date: 'YYYY-MM-DD', count: int}]
      - rows: lista de registros brutos (para debug se precisar)
    """
    result = supabase.table("t_mood").select("*").execute()
    rows = result.data or []

    print("[DB] Registros recebidos do Supabase:", rows)

    if not rows:
        return {
            "total": 0,
            "most_frequent": None,
            "distribution": {},
            "weekly_trend": [],
            "rows": [],
        }

    total = len(rows)

    # -----------------------------------------
    # 1) Descobrir automaticamente a coluna de humor
    # -----------------------------------------
    first_row = rows[0]
    mood_field = None

    for key in first_row.keys():
        lk = key.lower()
        if "mood" in lk or "humor" in lk or "emo" in lk:  # emo = emoção/emotion
            mood_field = key
            break

    if mood_field is None:
        # fallback: se não achar nada, assume "mood"
        mood_field = "mood"

    # Distribuição de emoções
    dist_counter = Counter()
    for r in rows:
        value = r.get(mood_field)
        if isinstance(value, str):
            v = value.strip()
        else:
            v = value
        if v:
            dist_counter[v] += 1

    distribution = dict(dist_counter)

    # Emoção mais frequente
    most_frequent = dist_counter.most_common(1)[0][0] if dist_counter else None

    # -----------------------------------------
    # 2) Descobrir automaticamente a coluna de data/hora
    # -----------------------------------------
    time_field = None
    for key in first_row.keys():
        lk = key.lower()
        if any(x in lk for x in ["created", "inserted", "timestamp", "time", "data", "date"]):
            time_field = key
            break

    counts_by_date: dict[str, int] = {}

    today = date.today()
    today_str = today.isoformat()

    if time_field:
        # Temos uma coluna de data/hora; tentar agrupar pelos últimos 7 dias
        for r in rows:
            raw = r.get(time_field)
            if not raw:
                continue

            if isinstance(raw, str):
                try:
                    ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                except Exception:
                    # se não conseguir parsear, pula esse registro
                    continue
            elif isinstance(raw, datetime):
                ts = raw
            else:
                # tipo inesperado, ignora
                continue

            d = ts.date()
            d_str = d.isoformat()
            counts_by_date[d_str] = counts_by_date.get(d_str, 0) + 1
    else:
        # Não há nenhuma coluna de data/hora:
        # considera TODOS registros como sendo de "hoje"
        counts_by_date[today_str] = total

    # Gera últimos 7 dias
    labels = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]

    weekly_trend = [
        {"date": d, "count": counts_by_date.get(d, 0)}
        for d in labels
    ]

    stats = {
        "total": total,
        "most_frequent": most_frequent,
        "distribution": distribution,
        "weekly_trend": weekly_trend,
        "rows": rows,
    }

    print("[DB] Estatísticas calculadas:", stats)
    return stats


# ============================================
# Teste manual (rodar: python database.py)
# ============================================
if __name__ == "__main__":
    print("=== Teste rápido do get_mood_stats ===")
    s = get_mood_stats()
    print("Total:", s["total"])
    print("Distribuição:", s["distribution"])
    print("Mais frequente:", s["most_frequent"])
    print("Weekly trend:", s["weekly_trend"])
