COMO EXECUTAR A SOLUÇÃO (MODO DESENVOLVIMENTO)

Pré-requisitos:
- Python 3.13 instalado.
- Pip e virtualenv configurados.

Passos:

1) Criar e ativar ambiente virtual:
   - Windows (PowerShell):
     python -m venv venv
     venv\Scripts\activate

2) Instalar dependências:
   pip install -r requirements.txt

3) Configurar chaves (caso vá usar IA real Gemini):
   - Definir variável de ambiente:
     GENAI_API_KEY= SUA_CHAVE_GEMINI

4) Executar EmpatIA Form:
   cd APP/backend
   python main.py

5) Executar EmpatIA Dashboard:
   cd APP-Dash/backend
   python main.py


COMO EXECUTAR A SOLUÇÃO (EXECUTÁVEIS .EXE)


Foram gerados executáveis com PyInstaller para facilitar a demonstração:

Executaveis
https://drive.google.com/drive/folders/1gT2ILqBG7QCBFyTb2DubLCTvYELwbDp-?hl=pt_BR
