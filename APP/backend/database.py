from supabase import create_client
from datetime import datetime, timezone
import os


SUPABASE_URL="https://aotcapkawsmgoehavldk.supabase.co"
SUPABASE_KEY= os.getenv("SUPABASE_API_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_mood(mood: str, reason: str | None, ai_text: str):
    data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),  # 👈 STRING, não datetime
        "mood": mood,
        "reason": reason,
        "ai_response": ai_text,
    }
    result = supabase.table("t_mood").insert(data).execute()
    return result

def get_mood_stats():
    response = supabase.table("t_mood").select("*").execute()
    return response.data