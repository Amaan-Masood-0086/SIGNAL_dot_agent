"""One-off local-dev helper: generate a throwaway RS256 keypair and write
backend/.env for the smoke run. NOT part of the application; delete-safe.
"""

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
priv = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8,
    serialization.NoEncryption(),
).decode()
pub = key.public_key().public_bytes(
    serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo,
).decode()

lines = [
    "ENVIRONMENT=synthetic_only",
    "DATABASE_URL=postgresql+psycopg://signal:signal_dev_only@localhost:5432/signal_dev",
    f'JWT_PRIVATE_KEY="{priv.replace(chr(10), "\\n").strip()}"',
    f'JWT_PUBLIC_KEY="{pub.replace(chr(10), "\\n").strip()}"',
    "JWT_ISSUER=signal-api",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15",
]
with open(".env", "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
print("written .env")
