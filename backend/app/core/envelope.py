"""Canonical response envelope — TRD §4 Response Format.

{ "success": bool, "data": {}, "meta": { "request_id", "timestamp", "version" } }
"""

from __future__ import annotations

import datetime
import uuid
from typing import Any

API_VERSION = "v1"


def envelope(data: Any, *, success: bool = True) -> dict:
    return {
        "success": success,
        "data": data,
        "meta": {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "version": API_VERSION,
        },
    }
