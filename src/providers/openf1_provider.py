from __future__ import annotations

import os
from typing import Any

import requests


def fetch_openf1_data() -> dict[str, Any]:
    api_key = os.getenv("OPENF1_API_KEY")
    if not api_key:
        return {
            "enabled": False,
            "status": "skipped",
            "warnings": ["OPENF1_API_KEY not set; real-time OpenF1 integration skipped"],
            "signals": {},
        }

    headers = {"Authorization": f"Bearer {api_key}"}
    payload: dict[str, Any] = {
        "enabled": True,
        "status": "ok",
        "warnings": [],
        "signals": {},
    }

    try:
        meetings = requests.get("https://api.openf1.org/v1/meetings?year=2026", headers=headers, timeout=15)
        meetings.raise_for_status()
        meetings_data = meetings.json()
        payload["signals"]["meetings_count"] = len(meetings_data) if isinstance(meetings_data, list) else 0
    except Exception as exc:  # noqa: BLE001
        payload["status"] = "degraded"
        payload["warnings"].append(f"OpenF1 meetings fetch failed: {exc}")

    return payload
