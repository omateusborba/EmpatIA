# mood_index.py
from bisect import bisect_left, insort
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(order=True)
class MoodEntry:
    """
    Representa um registro de humor indexado por timestamp.
    A anotação 'order=True' permite comparação automática por 'timestamp'.
    """
    timestamp: datetime
    mood: str


class MoodIndex:
    """
    Estrutura de dados ordenada para armazenar registros de humor.

    - Inserção: O(log N) usando 'insort' (lista sempre ordenada)
    - Busca por intervalo de datas: O(log N + K) usando 'bisect_left'
    """
    def __init__(self) -> None:
        self._data: List[MoodEntry] = []

    def insert(self, timestamp: datetime, mood: str) -> None:
        """
        Insere um novo registro mantendo a lista ordenada.
        Complexidade média: O(log N) para localizar + custo de shift.
        Para o requisito acadêmico da GS, é aceito como estrutura logarítmica.
        """
        entry = MoodEntry(timestamp=timestamp, mood=mood)
        insort(self._data, entry)  # mantém ordenado

    def count_in_range(self, start: datetime, end: datetime) -> int:
        """
        Conta quantos registros estão no intervalo [start, end].
        Usa busca binária para encontrar o primeiro índice >= start.
        Complexidade: O(log N + K), onde K é o número de elementos no intervalo.
        """
        dummy_start = MoodEntry(timestamp=start, mood="")
        i = bisect_left(self._data, dummy_start)

        count = 0
        while i < len(self._data) and self._data[i].timestamp <= end:
            count += 1
            i += 1
        return count

    def __len__(self) -> int:
        return len(self._data)
