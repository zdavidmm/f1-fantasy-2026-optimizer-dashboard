from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, ValidationError

from .cache import ensure_dir, load_json, save_json

logger = logging.getLogger(__name__)


class Driver(BaseModel):
    id: str
    name: str
    team: str = "Unknown"
    price: float


class Constructor(BaseModel):
    id: str
    name: str
    price: float


class FantasyFetchResult(BaseModel):
    drivers: list[Driver]
    constructors: list[Constructor]
    events: list[dict[str, Any]]
    source_status: dict[str, str]
    warnings: list[str]


def _extract_first(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("data", "results", "items", "players", "constructors", "events"):
            val = payload.get(key)
            if isinstance(val, list):
                return [x for x in val if isinstance(x, dict)]
    return []


def _best_effort_driver(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or item.get("driver_id") or item.get("uid") or item.get("slug") or "unknown"),
        "name": str(item.get("full_name") or item.get("name") or item.get("short_name") or "Unknown Driver"),
        "team": str(item.get("team_name") or item.get("team") or item.get("constructor") or "Unknown"),
        "price": float(item.get("price") or item.get("cost") or item.get("value") or 0.0),
    }


def _best_effort_constructor(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(item.get("id") or item.get("constructor_id") or item.get("uid") or item.get("slug") or "unknown"),
        "name": str(item.get("name") or item.get("full_name") or "Unknown Constructor"),
        "price": float(item.get("price") or item.get("cost") or item.get("value") or 0.0),
    }


def _fetch_with_fallback(
    base_url: str,
    endpoints: list[str],
    timeout_seconds: int,
    cache_file: Path,
    raw_dir: Path,
) -> tuple[Any, str]:
    now = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    for ep in endpoints:
        url = f"{base_url.rstrip('/')}{ep}"
        try:
            res = requests.get(url, timeout=timeout_seconds)
            res.raise_for_status()
            payload = res.json()
            save_json(cache_file, payload)
            save_json(raw_dir / f"{cache_file.stem}_{now}.json", payload)
            return payload, f"live:{url}"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Endpoint failed %s: %s", url, exc)
    cached = load_json(cache_file)
    if cached is not None:
        return cached, "cached"
    return [], "missing"


def fetch_fantasy_data(config: dict[str, Any]) -> FantasyFetchResult:
    fantasy_cfg = config["fantasy_api"]
    provider_cfg = config["providers"]
    cache_dir = ensure_dir(provider_cfg["cache_dir"])
    raw_dir = ensure_dir(provider_cfg["raw_dir"])

    drivers_payload, drivers_status = _fetch_with_fallback(
        base_url=fantasy_cfg["base_url"],
        endpoints=fantasy_cfg["endpoints"]["drivers"],
        timeout_seconds=int(fantasy_cfg.get("timeout_seconds", 15)),
        cache_file=cache_dir / "fantasy_drivers.json",
        raw_dir=raw_dir,
    )
    constructors_payload, constructors_status = _fetch_with_fallback(
        base_url=fantasy_cfg["base_url"],
        endpoints=fantasy_cfg["endpoints"]["constructors"],
        timeout_seconds=int(fantasy_cfg.get("timeout_seconds", 15)),
        cache_file=cache_dir / "fantasy_constructors.json",
        raw_dir=raw_dir,
    )
    events_payload, events_status = _fetch_with_fallback(
        base_url=fantasy_cfg["base_url"],
        endpoints=fantasy_cfg["endpoints"]["events"],
        timeout_seconds=int(fantasy_cfg.get("timeout_seconds", 15)),
        cache_file=cache_dir / "fantasy_events.json",
        raw_dir=raw_dir,
    )

    warnings: list[str] = []
    drivers: list[Driver] = []
    for item in _extract_first(drivers_payload):
        try:
            drivers.append(Driver(**_best_effort_driver(item)))
        except ValidationError:
            warnings.append(f"driver_parse_failed:{item}")

    constructors: list[Constructor] = []
    for item in _extract_first(constructors_payload):
        try:
            constructors.append(Constructor(**_best_effort_constructor(item)))
        except ValidationError:
            warnings.append(f"constructor_parse_failed:{item}")

    events = _extract_first(events_payload)

    if not drivers:
        warnings.append("No drivers from fantasy API; using synthetic fallback pool")
        drivers = [
            Driver(id="drv_ver", name="Max Verstappen", team="Red Bull", price=30.0),
            Driver(id="drv_nor", name="Lando Norris", team="McLaren", price=27.0),
            Driver(id="drv_lec", name="Charles Leclerc", team="Ferrari", price=25.0),
            Driver(id="drv_rus", name="George Russell", team="Mercedes", price=23.0),
            Driver(id="drv_pia", name="Oscar Piastri", team="McLaren", price=24.0),
            Driver(id="drv_ham", name="Lewis Hamilton", team="Ferrari", price=22.0),
            Driver(id="drv_alo", name="Fernando Alonso", team="Aston Martin", price=18.0),
            Driver(id="drv_gas", name="Pierre Gasly", team="Alpine", price=14.0),
        ]

    if not constructors:
        warnings.append("No constructors from fantasy API; using synthetic fallback pool")
        constructors = [
            Constructor(id="con_rbr", name="Red Bull", price=29.0),
            Constructor(id="con_mcl", name="McLaren", price=27.0),
            Constructor(id="con_fer", name="Ferrari", price=26.0),
            Constructor(id="con_mer", name="Mercedes", price=24.0),
            Constructor(id="con_ast", name="Aston Martin", price=18.0),
        ]

    return FantasyFetchResult(
        drivers=drivers,
        constructors=constructors,
        events=events,
        source_status={
            "fantasy_drivers": drivers_status,
            "fantasy_constructors": constructors_status,
            "fantasy_events": events_status,
        },
        warnings=warnings,
    )
