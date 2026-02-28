from __future__ import annotations

import datetime as dt
from typing import Any

from .cache import ensure_dir


def fetch_fastf1_signals(config: dict[str, Any]) -> dict[str, Any]:
    cache_dir = ensure_dir(config["fastf1"]["cache_dir"])
    result: dict[str, Any] = {
        "source": "fastf1",
        "status": "unavailable",
        "event": None,
        "driver_signals": {},
        "constructor_signals": {},
        "warnings": [],
    }

    try:
        import fastf1  # type: ignore
    except Exception as exc:  # noqa: BLE001
        result["warnings"].append(f"fastf1 import failed: {exc}")
        return result

    try:
        fastf1.Cache.enable_cache(str(cache_dir))
        schedule = fastf1.get_event_schedule(2026, include_testing=False)
        now = dt.datetime.utcnow()

        event_row = None
        if not schedule.empty:
            for _, row in schedule.iterrows():
                race_date = row.get("EventDate")
                if race_date is not None and hasattr(race_date, "to_pydatetime"):
                    race_date = race_date.to_pydatetime()
                if isinstance(race_date, dt.datetime) and race_date >= now - dt.timedelta(days=3):
                    event_row = row
                    break
            if event_row is None:
                event_row = schedule.iloc[-1]

        if event_row is None:
            result["warnings"].append("No event rows returned by FastF1")
            return result

        round_number = int(event_row["RoundNumber"])
        event_name = str(event_row["EventName"])
        result["event"] = {"round": round_number, "name": event_name}

        sessions = {
            "Q": {"kind": "qualifying", "weight": 1.0},
            "R": {"kind": "race", "weight": 1.0},
            "S": {"kind": "sprint", "weight": 1.0},
        }

        driver_scores: dict[str, dict[str, float]] = {}
        for code, meta in sessions.items():
            try:
                sess = fastf1.get_session(2026, round_number, code)
                sess.load(telemetry=False, laps=False, weather=False, messages=False)
                res = sess.results
                if res is None or getattr(res, "empty", True):
                    result["warnings"].append(f"No results for session {code}")
                    continue
                for _, row in res.iterrows():
                    abbr = str(row.get("Abbreviation") or "UNK")
                    team = str(row.get("TeamName") or "Unknown")
                    pos = row.get("Position")
                    if pos is None:
                        continue
                    pos_int = int(pos)
                    form_points = max(0, 22 - pos_int * 2)
                    d = driver_scores.setdefault(abbr, {
                        "name": str(row.get("FullName") or abbr),
                        "team": team,
                        "qualifying_form": 0.0,
                        "race_form": 0.0,
                        "sprint_form": 0.0,
                        "dnf_risk": 0.12,
                    })
                    d[f"{meta['kind']}_form"] = float(form_points)
                    status = str(row.get("Status") or "")
                    if "Finished" not in status and meta["kind"] in {"race", "sprint"}:
                        d["dnf_risk"] = min(0.8, d["dnf_risk"] + 0.20)
            except Exception as exc:  # noqa: BLE001
                result["warnings"].append(f"session {code} failed: {exc}")

        constructor: dict[str, dict[str, float]] = {}
        for ds in driver_scores.values():
            team = ds["team"]
            c = constructor.setdefault(team, {
                "pitstop_proxy": 5.0,
                "reliability": 0.88,
            })
            c["reliability"] = min(c["reliability"], 1.0 - ds["dnf_risk"])
            c["pitstop_proxy"] = max(c["pitstop_proxy"], (ds["race_form"] + ds["qualifying_form"]) / 8.0)

        result["status"] = "ok"
        result["driver_signals"] = driver_scores
        result["constructor_signals"] = constructor
        return result
    except Exception as exc:  # noqa: BLE001
        result["warnings"].append(f"fastf1 provider failed: {exc}")
        return result
