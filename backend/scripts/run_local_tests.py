"""Run isolated PostgreSQL tests using the local test URL, without printing secrets.

The pytest fixture creates its own random database and removes only that
database. This runner never migrates or clears the configured app database.
"""
import os
import sys
from pathlib import Path
from dotenv import dotenv_values
import pytest
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    settings = dotenv_values(root / ".env")
    if not os.environ.get("SIGNAL_TEST_DATABASE_URL"):
        value = settings.get("SIGNAL_TEST_DATABASE_URL")
        if not value:
            raise SystemExit("Configure SIGNAL_TEST_DATABASE_URL for isolated PostgreSQL tests")
        os.environ["SIGNAL_TEST_DATABASE_URL"] = value
    os.chdir(root)
    os.environ["CREDENTIAL_ENCRYPTION_KEY"] = Fernet.generate_key().decode()
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    os.environ["JWT_PRIVATE_KEY"] = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
    os.environ["JWT_PUBLIC_KEY"] = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
    os.environ["ENVIRONMENT"] = "synthetic_only"
    sys.path.insert(0, str(root))
    raise SystemExit(pytest.main(sys.argv[1:]))
