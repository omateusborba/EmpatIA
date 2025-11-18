from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, Optional

import os
from google import genai


# ------------------ CONTEXTO DO PERÍODO ------------------

@dataclass
class EmpatIAContext:
    """
    Contexto do período analisado no dashboard.
    """
    period: str        # "daily" | "weekly" | "monthly" | "yearly"
    start_date: date   # data inicial do filtro
    end_date: date     # data final do filtro


# ------------------ SERVIÇO DE IA DO DASHBOARD ------------------

class EmpatIADashboardService:
    """
    Serviço de IA exclusivo do DASHBOARD.

    - Se tiver GENAI_API_KEY -> usa Gemini para gerar um texto mais rico.
    - Se não tiver ou der erro -> usa regras locais para gerar o conselho.
    """

    # chaves consideradas "negativas" e "positivas"
    NEGATIVE_KEYS = {"sad", "triste", "stressed", "estressado"}
    POSITIVE_KEYS = {"happy", "feliz", "excited", "animado"}

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self.api_key: Optional[str] = os.getenv("GENAI_API_KEY")
        self.model_name: str = model_name
        self.client: Optional[genai.Client] = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("[EmpatIADashboardService] Cliente GenAI inicializado.")
            except Exception as e:
                print("[EmpatIADashboardService] Erro ao inicializar GenAI, usando modo regras:", e)
                self.client = None
        else:
            print("[EmpatIADashboardService] GENAI_API_KEY não encontrada. Usando modo regras.")

    # ==================== MÉTODO PÚBLICO ====================

    def build_advice(
        self,
        mood_counts: Dict[str, int],
        ctx: EmpatIAContext,
    ) -> str:
        """
        Gera a recomendação que aparece no card:
        'Recomendação da IA para o Clima Emocional da Equipe'
        """
        if self.client is not None:
            try:
                return self._advice_gemini(mood_counts, ctx)
            except Exception as e:
                print("[EmpatIADashboardService] Erro ao chamar Gemini, caindo para modo regras:", e)

        # fallback
        return self._advice_regras(mood_counts, ctx)

    # ==================== IA REAL (GEMINI) ====================

    def _advice_gemini(
        self,
        mood_counts: Dict[str, int],
        ctx: EmpatIAContext,
    ) -> str:
        total = sum(mood_counts.values())
        label_period = self._label_period(ctx.period)
        range_str = self._format_range(ctx.start_date, ctx.end_date)

        prompt = f"""
        Você é o módulo de IA de um dashboard chamado EmpatIA, que monitora o clima emocional de uma equipe.

        Dados agregados do período:
        - Período interno: {ctx.period}
        - Descrição do período: {label_period}
        - Intervalo de datas: {range_str}
        - Total de registros: {total}
        - Distribuição de humores (mood_counts): {mood_counts}

        Instruções:
        - Responda em português do Brasil.
        - Fale com o gestor/líder da equipe, não com um indivíduo.
        - Faça uma leitura breve do clima emocional geral (mais positivo, mais negativo ou misto).
        - Dê de 2 a 3 recomendações práticas de gestão de pessoas
          (ex.: 1:1, feedbacks, pausas, celebrações, escuta ativa, etc.).
        - Evite jargões técnicos demais.
        - Responda em até 3 parágrafos curtos.
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        text = getattr(response, "text", "").strip()
        if not text:
            return self._advice_regras(mood_counts, ctx)

        return text

    # ==================== MODO REGRAS ====================

    def _advice_regras(
        self,
        mood_counts: Dict[str, int],
        ctx: EmpatIAContext,
    ) -> str:
        total = sum(mood_counts.values())
        label_period = self._label_period(ctx.period)
        range_str = self._format_range(ctx.start_date, ctx.end_date)

        if total == 0:
            return (
                "Ainda não há dados suficientes para avaliar o clima emocional "
                f"{label_period} ({range_str}). "
                "Incentive a equipe a registrar como se sente para que o EmpatIA "
                "possa apoiar melhor as decisões de cuidado e gestão."
            )

        negative = sum(
            count for mood, count in mood_counts.items()
            if mood.lower() in self.NEGATIVE_KEYS
        )
        positive = sum(
            count for mood, count in mood_counts.items()
            if mood.lower() in self.POSITIVE_KEYS
        )

        neg_pct = (negative / total) * 100 if total else 0
        pos_pct = (positive / total) * 100 if total else 0

        base = (
            f"No período analisado {label_period} ({range_str}), "
            f"foram registrados {total} estados emocionais."
        )

        if negative > positive and neg_pct >= 40:
            detalhe = (
                f" Aproximadamente {neg_pct:.1f}% dos registros indicam emoções "
                "negativas, como tristeza ou estresse."
            )
            recomendacao = (
                " Este é um sinal de atenção para a liderança: vale reforçar a escuta ativa, "
                "revisar cargas e prazos, abrir espaço para conversas sinceras sobre pressão "
                "e incentivar pausas saudáveis durante o dia."
            )
        elif positive >= negative and pos_pct >= 40:
            detalhe = (
                f" Cerca de {pos_pct:.1f}% dos registros apontam para emoções "
                "positivas, como alegria, motivação e animação."
            )
            recomendacao = (
                " É um bom momento para consolidar práticas que funcionam, como reconhecimento "
                "frequente, celebração de resultados e autonomia equilibrada. Mantenha esses rituais "
                "vivos e compartilhe casos positivos dentro da equipe."
            )
        else:
            detalhe = (
                " Os dados mostram um equilíbrio entre emoções positivas e negativas."
            )
            recomendacao = (
                " Isso indica um time com desafios reais, mas também com forças importantes. "
                "Use esse cenário para se aproximar da equipe, promover diálogos estruturados "
                "sobre bem-estar e identificar focos específicos de tensão para tratamento."
            )

        return base + detalhe + recomendacao

    # ==================== HELPERS ====================

    def _label_period(self, period: str) -> str:
        """
        Converte 'daily', 'weekly', etc. em rótulo amigável.
        """
        period = (period or "").lower()
        mapping = {
            "daily": "neste dia",
            "weekly": "nesta semana",
            "monthly": "neste mês",
            "yearly": "neste ano",
        }
        return mapping.get(period, "no período selecionado")

    def _format_range(self, start: date, end: date) -> str:
        """
        Formata o intervalo de datas como dd/mm/aaaa a dd/mm/aaaa.
        """
        if not isinstance(start, date) or not isinstance(end, date):
            return "período não definido"

        if start == end:
            return start.strftime("%d/%m/%Y")

        return f"{start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}"
