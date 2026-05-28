import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from django.conf import settings


class EncryptionError(ValueError):
    pass


def _get_encryption_key() -> bytes:
    key_b64 = settings.ENCRYPTION_KEY
    if not key_b64:
        raise EncryptionError("ENCRYPTION_KEY must be set")

    try:
        key = base64.b64decode(key_b64)
    except (TypeError, ValueError) as exc:
        raise EncryptionError("ENCRYPTION_KEY must be valid base64") from exc

    if len(key) != 32:
        raise EncryptionError("ENCRYPTION_KEY must decode to 32 bytes")

    return key


def encrypt_value(plaintext: str) -> str:
    key = _get_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    return base64.b64encode(nonce + ciphertext).decode()


def decrypt_value(ciphertext_b64: str) -> str:
    key = _get_encryption_key()
    raw = base64.b64decode(ciphertext_b64)
    nonce, ciphertext = raw[:12], raw[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode()
