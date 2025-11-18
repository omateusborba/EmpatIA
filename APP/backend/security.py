from __future__ import annotations

from cryptography.fernet import Fernet
from pathlib import Path

# Arquivo onde a chave de criptografia será armazenada
KEY_PATH = Path(__file__).resolve().parent / "empatIA.key"


def _load_or_create_key() -> bytes:
    """
    Carrega a chave de criptografia do arquivo, se existir.
    Caso contrário, gera uma nova chave e salva em disco.
    """
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes()

    key = Fernet.generate_key()
    KEY_PATH.write_bytes(key)
    return key


# Instância global do Fernet para ser usada na aplicação
_FERNET = Fernet(_load_or_create_key())


def encrypt_text(plain_text: str) -> bytes:
    """
    Recebe um texto em claro (string) e devolve os bytes criptografados.
    """
    return _FERNET.encrypt(plain_text.encode("utf-8"))


def decrypt_text(token: bytes) -> str:
    """
    Recebe bytes criptografados e devolve o texto em claro (string).
    """
    return _FERNET.decrypt(token).decode("utf-8")
