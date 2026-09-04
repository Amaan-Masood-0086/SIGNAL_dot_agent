"""One-off local-dev helper: generate throwaway keys and write backend/.env.

NOT part of the application; delete-safe. Everything it writes is a
throwaway for a local synthetic-only run — never reuse any of it elsewhere.

Two things were wrong with the previous version, and both only bite on a
fresh machine, which is exactly where this script gets used:

  * it clobbered an existing .env without asking, so running it on a working
    setup destroyed real configuration;
  * the file it wrote was missing TENANT_DATABASE_URL and
    CREDENTIAL_ENCRYPTION_KEY, so the app it set up would refuse to serve
    caretaker traffic (correctly — see `_verified_tenant_engine`) and the
    error would look like a code fault rather than a missing setting.
"""

import os
import sys

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

if os.path.exists(".env"):
    sys.exit(
        "backend/.env already exists — refusing to overwrite it. "
        "Delete it first if you really want a fresh throwaway set."
    )

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
    # Privileged path: migrations, /auth/token, admin cross-institution reads.
    "DATABASE_URL=postgresql+psycopg://signal:signal_dev_only@localhost:5432/signal_dev",
    # Tenant path: the unprivileged role from migration 0001, so RLS binds.
    # REQUIRED — there is deliberately no fallback to DATABASE_URL.
    "TENANT_DATABASE_URL=postgresql+psycopg://signal_app:signal_app@localhost:5432/signal_dev",
    "SIGNAL_TEST_DATABASE_URL=postgresql+psycopg://signal:signal_dev_only@localhost:5432/signal_dev",
    f'JWT_PRIVATE_KEY="{priv.replace(chr(10), "\\n").strip()}"',
    f'JWT_PUBLIC_KEY="{pub.replace(chr(10), "\\n").strip()}"',
    "JWT_ISSUER=signal-api",
    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15",
    # ADR-10 gives this no default on purpose, so generate one rather than
    # leave it out. A NEW key makes previously stored provider credentials
    # undecryptable — on a fresh machine that is fine, because the provider
    # keys are re-entered through the admin console anyway.
    f"CREDENTIAL_ENCRYPTION_KEY={Fernet.generate_key().decode()}",
]
with open(".env", "w", encoding="utf-8") as handle:
    handle.write("\n".join(lines) + "\n")
print("written .env")
