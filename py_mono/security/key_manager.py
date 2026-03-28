# py_mono/security/key_manager.py

from typing import Optional
from cryptography.fernet import Fernet
import json
import os
from pathlib import Path
import logging


# Workspace root is defined in config.py; reuse it
from py_mono.config import WORKSPACE_ROOT

KEYS_FILE = WORKSPACE_ROOT / ".keys.enc"


class KeyManager:
    """
    Encrypted API key storage for providers.

    - Never stores plaintext keys on disk.
    - Uses Fernet symmetric encryption.
    - Read master key from `LLM_MASTER_KEY` environment variable.
    - Keys never appear in logs.
    """

    def __init__(self, master_key: bytes | None = None):
        if master_key is None:
            raw = os.getenv("LLM_MASTER_KEY")
            if not raw:
                raise RuntimeError(
                    "LLM_MASTER_KEY environment variable not set. "
                    "For example on Windows: setx LLM_MASTER_KEY '<your_generated_key>'"
                )
            master_key = raw.encode()

        self.fernet = Fernet(master_key)
        self._keys: dict = self._load()

        # Prevent logging secrets
        self.__logger = logging.getLogger(__name__)
        self.__logger.setLevel(logging.INFO)

    def _load(self) -> dict:
        """Load and decrypt the keys file."""
        if not KEYS_FILE.exists():
            return {}

        try:
            encrypted = KEYS_FILE.read_bytes()
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted.decode("utf-8"))
        except Exception as e:
            self.__logger.error(
                f"Failed to load/decrypt keys from {KEYS_FILE}: {e}"
            )
            return {}

    def _save(self) -> None:
        """Encrypt and save keys."""
        try:
            plaintext = json.dumps(self._keys).encode("utf-8")
            encrypted = self.fernet.encrypt(plaintext)
            KEYS_FILE.write_bytes(encrypted)
        except Exception as e:
            self.__logger.error(
                f"Failed to write encrypted keys to {KEYS_FILE}: {e}"
            )
            raise

    def set(self, provider: str, api_key: str) -> None:
        """Store an encrypted API key for a provider."""
        if not provider.strip():
            raise ValueError("Provider name cannot be empty")
        if not api_key.strip():
            raise ValueError("API key cannot be empty")

        self._keys[provider] = api_key
        self._save()

    def get(self, provider: str) -> Optional[str]:
        """Retrieve a decrypted API key for a provider."""
        return self._keys.get(provider)

    def has(self, provider: str) -> bool:
        """Check whether a provider has a stored key."""
        return provider in self._keys

    def remove(self, provider: str) -> bool:
        """Remove a provider's key and save."""
        if provider not in self._keys:
            return False
        del self._keys[provider]
        self._save()
        return True

    def list_providers(self) -> list[str]:
        """List all providers that currently have keys."""
        return list(self._keys.keys())

    # Prevent keys from leaking in repr / str
    def __repr__(self) -> str:
        n_keys = len(self._keys)
        return f"<KeyManager n_keys={n_keys}>"

    def __str__(self) -> str:
        return repr(self)
