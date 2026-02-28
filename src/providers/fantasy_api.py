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


def _heuristic_driver_price(position: int) -> float:
    # Basic market-like price curve when official fantasy prices are unavailable.
    return round(max(8.0, 32.0 - position * 1.35), 1)


def _heuristic_constructor_price(position: int) -> float:
    return round(max(10.0, 30.0 - position * 2.0), 1)


def _fetch_jolpi_fallback(timeout_seconds: int) -> tuple[list[Driver], list[Constructor], list[str]]:
    warnings: list[str] = []
    drivers: list[Driver] = []
    constructors: list[Constructor] = []
    try:
        d_res = requests.get("https://api.jolpi.ca/ergast/f1/current/drivers.json", timeout=timeout_seconds)
        d_res.raise_for_status()
        d_payload = d_res.json()
        d_items = (
            d_payload.get("MRData", {})
            .get("DriverTable", {})
            .get("Drivers", [])
        )
        for idx, item in enumerate(d_items, start=1):
            given = str(item.get("givenName") or "").strip()
            family = str(item.get("familyName") or "").strip()
            name = f"{given} {family}".strip() or str(item.get("driverId") or "Unknown Driver")
            drivers.append(
                Driver(
                    id=str(item.get("driverId") or f"drv_{idx}"),
                    name=name,
                    team="Unknown",
                    price=_heuristic_driver_price(idx),
                )
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Jolpica driver fallback unavailable: {exc}")

    try:
        c_res = requests.get("https://api.jolpi.ca/ergast/f1/current/constructors.json", timeout=timeout_seconds)
        c_res.raise_for_status()
        c_payload = c_res.json()
        c_items = (
            c_payload.get("MRData", {})
            .get("ConstructorTable", {})
            .get("Constructors", [])
        )
        for idx, item in enumerate(c_items, start=1):
            constructors.append(
                Constructor(
                    id=str(item.get("constructorId") or f"con_{idx}"),
                    name=str(item.get("name") or "Unknown Constructor"),
                    price=_heuristic_constructor_price(idx),
                )
            )
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Jolpica constructor fallback unavailable: {exc}")

    return drivers, constructors, warnings


def _fetch_official_feeds(timeout_seconds: int, raw_dir: Path, cache_dir: Path) -> tuple[list[Driver], list[Constructor], list[dict[str, Any]], dict[str, str], list[str]]:
    warnings: list[str] = []
    status = {
        "fantasy_drivers": "missing",
        "fantasy_constructors": "missing",
        "fantasy_events": "missing",
    }

    base = "https://fantasy.formula1.com/feeds"
    now = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    events_payload: Any = None
    drivers_payload: Any = None

    try:
        events_url = f"{base}/schedule/raceday_en.json"
        r = requests.get(events_url, timeout=timeout_seconds)
        r.raise_for_status()
        events_payload = r.json()
        save_json(cache_dir / "feeds_raceday.json", events_payload)
        save_json(raw_dir / f"feeds_raceday_{now}.json", events_payload)
        status["fantasy_events"] = f"live:{events_url}"
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Official feeds schedule unavailable: {exc}")
        cached = load_json(cache_dir / "feeds_raceday.json")
        if cached is not None:
            events_payload = cached
            status["fantasy_events"] = "cached:feeds"

    events_list: list[dict[str, Any]] = []
    if isinstance(events_payload, dict):
        events_data = events_payload.get("Data", {})
        if isinstance(events_data, dict):
            raw_events = events_data.get("Value", [])
            if isinstance(raw_events, list):
                events_list = [e for e in raw_events if isinstance(e, dict)]

    current_gameday = None
    for event in events_list:
        if str(event.get("GDIsCurrent")) == "1":
            current_gameday = event.get("GamedayId")
            break
    if current_gameday is None and events_list:
        current_gameday = events_list[0].get("CurrentGamedayId") or events_list[0].get("GamedayId")
    if current_gameday is None:
        current_gameday = 1

    try:
        players_url = f"{base}/drivers/{int(current_gameday)}_en.json"
        r = requests.get(players_url, timeout=timeout_seconds)
        r.raise_for_status()
        drivers_payload = r.json()
        save_json(cache_dir / "feeds_drivers.json", drivers_payload)
        save_json(raw_dir / f"feeds_drivers_{now}.json", drivers_payload)
        status["fantasy_drivers"] = f"live:{players_url}"
        status["fantasy_constructors"] = f"live:{players_url}"
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"Official feeds prices unavailable: {exc}")
        cached = load_json(cache_dir / "feeds_drivers.json")
        if cached is not None:
            drivers_payload = cached
            status["fantasy_drivers"] = "cached:feeds"
            status["fantasy_constructors"] = "cached:feeds"

    rows: list[dict[str, Any]] = []
    if isinstance(drivers_payload, dict):
        data = drivers_payload.get("Data", {})
        if isinstance(data, dict):
            value = data.get("Value", [])
            if isinstance(value, list):
                rows = [x for x in value if isinstance(x, dict)]

    drivers: list[Driver] = []
    constructors: list[Constructor] = []
    for item in rows:
        skill = int(item.get("Skill") or 0)
        player_id = str(item.get("PlayerId") or item.get("id") or "unknown")
        value = float(item.get("Value") or item.get("price") or 0.0)
        if value <= 0:
            continue
        if skill == 1:
            name = str(item.get("FUllName") or item.get("DisplayName") or item.get("name") or "Unknown Driver")
            team = str(item.get("TeamName") or "Unknown")
            drivers.append(Driver(id=player_id, name=name, team=team, price=value))
        elif skill == 2:
            name = str(item.get("DisplayName") or item.get("TeamName") or item.get("name") or "Unknown Constructor")
            constructors.append(Constructor(id=player_id, name=name, price=value))

    return drivers, constructors, events_list, status, warnings


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
            logger.info("Endpoint failed %s: %s", url, exc)
    cached = load_json(cache_file)
    if cached is not None:
        return cached, "cached"
    return [], "missing"


def fetch_fantasy_data(config: dict[str, Any]) -> FantasyFetchResult:
    fantasy_cfg = config["fantasy_api"]
    provider_cfg = config["providers"]
    cache_dir = ensure_dir(provider_cfg["cache_dir"])
    raw_dir = ensure_dir(provider_cfg["raw_dir"])

    timeout_seconds = int(fantasy_cfg.get("timeout_seconds", 15))
    warnings: list[str] = []

    # Primary source: official fantasy feeds (live prices under fantasy.formula1.com/feeds).
    feed_drivers, feed_constructors, feed_events, feed_status, feed_warnings = _fetch_official_feeds(
        timeout_seconds=timeout_seconds,
        raw_dir=raw_dir,
        cache_dir=cache_dir,
    )
    warnings.extend(feed_warnings)
    if feed_drivers and feed_constructors:
        return FantasyFetchResult(
            drivers=feed_drivers,
            constructors=feed_constructors,
            events=feed_events,
            source_status=feed_status,
            warnings=warnings,
        )

    drivers_payload, drivers_status = _fetch_with_fallback(
        base_url=fantasy_cfg["base_url"],
        endpoints=fantasy_cfg["endpoints"]["drivers"],
        timeout_seconds=timeout_seconds,
        cache_file=cache_dir / "fantasy_drivers.json",
        raw_dir=raw_dir,
    )
    constructors_payload, constructors_status = _fetch_with_fallback(
        base_url=fantasy_cfg["base_url"],
        endpoints=fantasy_cfg["endpoints"]["constructors"],
        timeout_seconds=timeout_seconds,
        cache_file=cache_dir / "fantasy_constructors.json",
        raw_dir=raw_dir,
    )
    events_payload, events_status = _fetch_with_fallback(
        base_url=fantasy_cfg["base_url"],
        endpoints=fantasy_cfg["endpoints"]["events"],
        timeout_seconds=timeout_seconds,
        cache_file=cache_dir / "fantasy_events.json",
        raw_dir=raw_dir,
    )
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

    if not drivers or not constructors:
        jolpi_drivers, jolpi_constructors, jolpi_warnings = _fetch_jolpi_fallback(
            timeout_seconds=timeout_seconds
        )
        warnings.extend(jolpi_warnings)
        if not drivers and jolpi_drivers:
            drivers = jolpi_drivers
            drivers_status = "fallback:jolpica"
        if not constructors and jolpi_constructors:
            constructors = jolpi_constructors
            constructors_status = "fallback:jolpica"

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
