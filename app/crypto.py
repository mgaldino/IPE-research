import base64
import os
from typing import Tuple

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def derive_key(passphrase: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390_000,
    )
    return base64.urlsafe_b64encode(kdf.derive(passphrase.encode("utf-8")))


def encrypt_secret(passphrase: str, plaintext: str, salt: bytes) -> bytes:
    key = derive_key(passphrase, salt)
    fernet = Fernet(key)
    return fernet.encrypt(plaintext.encode("utf-8"))


def decrypt_secret(passphrase: str, token: bytes, salt: bytes) -> str:
    key = derive_key(passphrase, salt)
    fernet = Fernet(key)
    return fernet.decrypt(token).decode("utf-8")


def new_salt() -> bytes:
    return os.urandom(16)


def prepare_encrypted_secret(passphrase: str, plaintext: str) -> Tuple[bytes, bytes]:
    salt = new_salt()
    token = encrypt_secret(passphrase, plaintext, salt)
    return token, salt
