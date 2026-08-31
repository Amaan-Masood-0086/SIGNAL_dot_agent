"""ADR-10: admin-UI-editable provider credentials (supersedes ADR-09)

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-01

provider_credentials stores Fernet-ENCRYPTED provider keys (STT/LLM) set
through the admin UI, so keys can be rotated without a redeploy.

RLS STATEMENT (explicit, per ticket): provider_credentials is a
SYSTEM-LEVEL table, same tier as audit_log — it carries NO institution_id,
so Row-Level Security does not apply and is deliberately NOT enabled.
Access control instead comes from: (1) grants — signal_app gets
SELECT/INSERT/UPDATE only, DELETE stays revoked because deactivation is
soft, and (2) the application layer — only get_current_admin_staff
endpoints touch this table, and the API contract is write-only (no
response, log line, or audit entry ever carries the raw or decrypted value).
One env var still backs this feature: CREDENTIAL_ENCRYPTION_KEY (the Fernet
master key) — never committed, same rigor as the JWT keys (ADR-10 §2).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "signal_app"


def upgrade() -> None:
    op.create_table(
        "provider_credentials",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=8), nullable=False),
        # Fernet token (base64) — never the plaintext, never readable back
        # through any API surface.
        sa.Column("encrypted_value", sa.Text(), nullable=False),
        # Last 4 chars of the RAW value, stored separately, display-only.
        sa.Column("masked_suffix", sa.String(length=4), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        # Intentionally no FK to staff (audit_log precedent): the trail of
        # who stored what must survive any future staff-row changes.
        sa.Column("created_by_staff_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "provider IN ('stt', 'llm')", name="ck_provider_credentials_provider"
        ),
    )
    op.create_index(
        "ix_provider_credentials_provider_active",
        "provider_credentials",
        ["provider", "is_active"],
    )

    # Soft-delete semantics: INSERT new values, UPDATE is_active on
    # rotation/deactivation. DELETE is never granted to the app role.
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON provider_credentials TO {APP_ROLE}")
    op.execute(f"REVOKE DELETE ON provider_credentials FROM {APP_ROLE}, PUBLIC")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON provider_credentials FROM {APP_ROLE}")
    op.drop_index(
        "ix_provider_credentials_provider_active",
        table_name="provider_credentials",
    )
    op.drop_table("provider_credentials")
