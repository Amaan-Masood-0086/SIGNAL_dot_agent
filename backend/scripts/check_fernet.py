"""One-off check: cryptography/Fernet available in the backend venv.

Run from backend/:  python scripts/check_fernet.py
"""

import cryptography
from cryptography.fernet import Fernet

key = Fernet.generate_key()
token = Fernet(key).encrypt(b"round-trip")
print("cryptography", cryptography.__version__)
print("fernet round-trip:", Fernet(key).decrypt(token) == b"round-trip")
