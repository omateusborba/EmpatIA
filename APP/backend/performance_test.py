# performance_test.py
import time
from datetime import datetime, timedelta

from mood_index import MoodIndex


def run_test(n: int) -> None:
    """
    Simula N inserções e algumas buscas em intervalo de datas.
    Mostra tempo de execução para inserir e buscar.
    """
    print(f"\n=== Teste com N = {n:,} registros ===")
    idx = MoodIndex()

    base_time = datetime.now()

    # Inserção de N registros simulados
    t0 = time.perf_counter()
    for i in range(n):
        ts = base_time + timedelta(minutes=i)
        mood = "happy" if i % 2 == 0 else "sad"
        idx.insert(ts, mood)
    t1 = time.perf_counter()

    insert_time = t1 - t0
    print(f"Inserção de {n:,} registros em {insert_time:.4f} s")

    # Busca em um intervalo pequeno (últimos 60 minutos)
    start = base_time + timedelta(minutes=n - 60)
    end = base_time + timedelta(minutes=n - 1)

    t2 = time.perf_counter()
    count = idx.count_in_range(start, end)
    t3 = time.perf_counter()

    search_time = t3 - t2
    print(f"Busca em intervalo (60 min) retornou {count} registros em {search_time:.6f} s")


if __name__ == "__main__":
    for n in (1_000, 10_000, 100_000):
        run_test(n)
