"""Admin console extension: provider model_name (non-secret setting)

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-01

The admin UI needs to set the LLM model name alongside the key (the key
stays encrypted; the model name is NOT a secret and is stored in plaintext
for display). Precedence: active stored model_name beats LLM_MODEL env.
Same system-level tier as provider_credentials: no RLS (no institution_id).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "provider_credentials",
        sa.Column("model_name", sa.String(length=120), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("provider_credentials", "model_name")
