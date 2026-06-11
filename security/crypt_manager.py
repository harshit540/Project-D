import os
import base64
import uuid
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from core.logger import logger

class CryptManager:
    _fernet_instance = None

    @classmethod
    def _get_fernet(cls):
        if cls._fernet_instance is None:
            # Generate a consistent machine-bound unique key
            machine_id = str(uuid.getnode())
            salt = b"synchub_secure_salt_88"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000
            )
            key = base64.urlsafe_b64encode(kdf.derive(machine_id.encode()))
            cls._fernet_instance = Fernet(key)
        return cls._fernet_instance

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        if not plaintext:
            return ""
        try:
            fernet = cls._get_fernet()
            return fernet.encrypt(plaintext.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failure: {e}")
            raise RuntimeError("Could not secure credentials.") from e

    @classmethod
    def decrypt(cls, ciphertext: str) -> str:
        if not ciphertext:
            return ""
        try:
            fernet = cls._get_fernet()
            return fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failure: {e}")
            raise RuntimeError("Could not restore credentials.") from e