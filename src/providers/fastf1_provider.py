from __future__ import annotations

import datetime as dt
from typing import Any

from .cache import ensure_dir


def _to_datetime(value: Any) -> dt.datetime | None:
    if value is None:
        return None
    if hasattr(value, "to_pydatetime"):
        value = value.to_pydatetime()
    if isinstance(value, dt.datetime):
        return value
    return None


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
        now = dt.datetime.utcnow()
        season = 2026

        schedule = fastf1.get_event_schedule(season, include_testing=False)
        event_row = None

        if not schedule.empty:
            completed_rows = []
            for _, row in schedule.iterrows():
                race_date = _to_datetime(row.get("EventDate"))
                if race_date and race_date <= now:
                    completed_rows.append((race_date, row))

            if completed_rows:
                completed_rows.sort(key=lambda x: x[0], reverse=True)
                event_row = completed_rows[0][1]
            else:
                # No completed rounds in current season: fallback to previous season.
                prev_schedule = fastf1.get_event_schedule(season - 1, include_testing=False)
                prev_completed = []
                for _, row in prev_schedule.iterrows():
                    race_date = _to_datetime(row.get("EventDate"))
                    if race_date and race_date <= now:
                        prev_completed.append((race_date, row))
                if prev_completed:
                    prev_completed.sort(key=lambda x: x[0], reverse=True)
                    event_row = prev_completed[0][1]
                    season -= 1

        if event_row is None:
            result["warnings"].append("No completed event rows available from FastF1")
            return result

        round_number = int(event_row["RoundNumber"])
        event_name = str(event_row["EventName"])
        result["event"] = {"round": round_number, "name": event_name, "season": season}

        sessions = {
            "Q": {"kind": "qualifying"},
            "R": {"kind": "race"},
            "S": {"kind": "sprint"},
        }

        driver_scores: dict[str, dict[str, float]] = {}
        for code, meta in sessions.items():
            try:
                sess = fastf1.get_session(season, round_number, code)
                sess.load(telemetry=False, laps=False, weather=False, messages=False)
                res = sess.results
                if res is None or getattr(res, "empty", True):
                    # Keep this quiet; missing rows for incomplete weekends are common.
                    continue
                for _, row in res.iterrows():
                    abbr = str(row.get("Abbreviation") or "UNK")
                    team = str(row.get("TeamName") or "Unknown")
                    pos = row.get("Position")
                    if pos is None:
                        continue
                    pos_int = int(pos)
                    form_points = max(0, 22 - pos_int * 2)
                    d = driver_scores.setdefault(
                        abbr,
                        {
                            "name": str(row.get("FullName") or abbr),
                            "team": team,
                            "qualifying_form": 0.0,
                            "race_form": 0.0,
                            "sprint_form": 0.0,
                            "dnf_risk": 0.12,
                        },
                    )
                    d[f"{meta['kind']}_form"] = float(form_points)
                    status = str(row.get("Status") or "")
                    if "Finished" not in status and meta["kind"] in {"race", "sprint"}:
                        d["dnf_risk"] = min(0.8, d["dnf_risk"] + 0.20)
            except Exception as exc:  # noqa: BLE001
                msg = str(exc).lower()
                if "does not exist for this event" in msg or "invalid session type" in msg:
                    # Non-sprint weekends should not raise warning noise.
                    continue
                result["warnings"].append(f"session {code} failed: {exc}")

        constructor: dict[str, dict[str, float]] = {}
        for ds in driver_scores.values():
            team = ds["team"]
            c = constructor.setdefault(
                team,
                {
                    "pitstop_proxy": 5.0,
                    "reliability": 0.88,
                },
            )
            c["reliability"] = min(c["reliability"], 1.0 - ds["dnf_risk"])
            c["pitstop_proxy"] = max(c["pitstop_proxy"], (ds["race_form"] + ds["qualifying_form"]) / 8.0)

        if not driver_scores:
            result["status"] = "degraded"
            result["warnings"].append("FastF1 returned no session results; using default signal priors")
        else:
            result["status"] = "ok"

        result["driver_signals"] = driver_scores
        result["constructor_signals"] = constructor
        return result
    except Exception as exc:  # noqa: BLE001
        result["warnings"].append(f"fastf1 provider failed: {exc}")
        return result
