"""Generate Fernet keys for CREDENTIAL_ENCRYPTION_KEY (ADR-10).

Prints two keys: one for the TEST runner (committed to the runner script —
test-only, encrypts nothing real) and one for dev .env (never committed).
"""

from cryptography.fernet import Fernet

print("TEST:", Fernet.generate_key().decode())
print("DEV:", Fernet.generate_key().decode())
