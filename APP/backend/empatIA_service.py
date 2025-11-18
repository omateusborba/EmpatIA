from __future__ import annotations
from typing import Optional
from google import genai
import os


class EmpatIAService:
    """
    Camada de serviço de IA do EmpatIA.

    - Se tiver GENAI_API_KEY configurada -> usa Gemini.
    - Se não tiver ou der erro -> usa resposta baseada em regras.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash") -> None:
        self.api_key: Optional[str] = os.getenv("GENAI_API_KEY")
        self.model_name: str = model_name
        self.client: Optional[genai.Client] = None

        if self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("[EmpatIAService] Cliente GenAI inicializado com sucesso.")
            except Exception as e:
                print("[EmpatIAService] Erro ao inicializar GenAI, usando modo regras:", e)
                self.client = None
        else:
            print("[EmpatIAService] GENAI_API_KEY não encontrada. Usando modo regras.")

    # ------------------ MÉTODO PÚBLICO ------------------
    def ia_response(self, mood: Optional[str], reason: Optional[str]) -> str:
        """
        Gera uma resposta empática.

        1. Tenta usar Gemini (se disponível).
        2. Se não der, usa a resposta baseada em regras locais.
        """
        # Se não veio humor, nem adianta chamar IA
        if not mood:
            return "Não entendi como você está se sentindo. Tente selecionar um dos estados disponíveis."

        # Tenta IA real, se o client existir
        if self.client is not None:
            try:
                return self._ia_response_gemini(mood, reason)
            except Exception as e:
                print("[EmpatIAService] Erro ao chamar Gemini, caindo para modo regras:", e)

        # Fallback: regras locais
        return self._ia_response_regras(mood, reason)

    # ------------------ IMPLEMENTAÇÃO IA REAL ------------------
    def _ia_response_gemini(self, mood: str, reason: Optional[str]) -> str:
        """Chama o modelo Gemini para gerar uma resposta empática."""
        prompt = f"""
        Você é um assistente chamado EmpatIA, especializado em bem-estar emocional no ambiente de trabalho.

        Humor do colaborador: {mood}
        Motivo informado: {reason or "não informado"}

        Regras:
        - Responda em português do Brasil.
        - Seja empático, acolhedor e respeitoso.
        - Dê orientações práticas e realistas.
        - Responda em no máximo 2 parágrafos curtos.
        - Não use linguagem excessivamente técnica.
        - Use frases motivacionais, baseado no humor e no motivo.
        - Caso o humor for triste, e o colaborador possuir algum motivo pesado, recomende ajuda profissional!
        """

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt
        )

        text = getattr(response, "text", "").strip()
        if not text:
            # Se a IA não retornar nada útil, cai pro modo regras
            return self._ia_response_regras(mood, reason)

        return text

    # ------------------ IMPLEMENTAÇÃO BASEADA EM REGRAS ------------------
    def _ia_response_regras(self, mood: str, reason: Optional[str]) -> str:
        """Chat com a EmpatIA usando apenas regras locais (sem IA externa)."""
        base = f"Percebi que você está se sentindo {mood.lower()}."

        if mood in ("Triste", "Estressado"):
            extra = (
                "\n\nSugestão: experimente fazer uma pausa breve, respirar fundo por alguns minutos "
                "e, se possível, falar com alguém de confiança. Você não está sozinho(a)."
            )
        elif mood == "Neutro":
            extra = (
                "\n\nSugestão: que tal definir uma pequena meta positiva para hoje, algo que traga "
                "um senso de realização ao final do dia?"
            )
        elif mood in ("Feliz", "Animado"):
            extra = (
                "\n\nSugestão: aproveite essa boa energia para avançar em algo importante e, se puder, "
                "compartilhá-la com alguém do seu time. 🙂"
            )
        else:
            extra = ""

        if reason:
            base += f' Você compartilhou: "{reason}".'

        return base + extra