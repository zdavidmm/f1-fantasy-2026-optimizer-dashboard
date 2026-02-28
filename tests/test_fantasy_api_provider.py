from pathlib import Path

from src.providers.fantasy_api import fetch_fantasy_data


class _DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def _config(tmp_path: Path):
    return {
        "fantasy_api": {
            "base_url": "https://fantasy-api.formula1.com",
            "timeout_seconds": 2,
            "endpoints": {
                "drivers": ["/drivers"],
                "constructors": ["/constructors"],
                "events": ["/events"],
            },
        },
        "providers": {
            "cache_dir": str(tmp_path / "provider_cache"),
            "raw_dir": str(tmp_path / "raw"),
        },
    }


def test_fetch_fantasy_data_best_effort_parsing(monkeypatch, tmp_path):
    payloads = {
        "/feeds/schedule/raceday_en.json": {"Data": {"Value": [{"GamedayId": 1, "GDIsCurrent": 1, "CurrentGamedayId": 1}]}},
        "/feeds/drivers/1_en.json": {
            "Data": {
                "Value": [
                    {"PlayerId": 101, "Skill": 1, "FUllName": "Driver One", "TeamName": "TeamA", "Value": 12.5},
                    {"PlayerId": 201, "Skill": 2, "DisplayName": "Ctor One", "Value": 20.0},
                ]
            }
        },
        "/drivers": {"players": [{"id": 1, "full_name": "Driver One", "team_name": "TeamA", "price": 12.5}]},
        "/constructors": {"constructors": [{"constructor_id": "c1", "name": "Ctor One", "cost": 20}]},
        "/events": {"events": [{"id": 10, "name": "GP"}]},
    }

    def fake_get(url, timeout):
        for suffix, payload in payloads.items():
            if url.endswith(suffix):
                return _DummyResponse(payload)
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr("src.providers.fantasy_api.requests.get", fake_get)
    res = fetch_fantasy_data(_config(tmp_path))

    assert len(res.drivers) == 1
    assert res.drivers[0].name == "Driver One"
    assert len(res.constructors) == 1
    assert res.constructors[0].name == "Ctor One"
    assert len(res.events) == 1
    assert res.source_status["fantasy_drivers"].startswith("live:https://fantasy.formula1.com/feeds/")


def test_fetch_fantasy_data_fallback_to_synthetic_when_unavailable(monkeypatch, tmp_path):
    def always_fail(url, timeout):
        raise RuntimeError("network down")

    monkeypatch.setattr("src.providers.fantasy_api.requests.get", always_fail)
    res = fetch_fantasy_data(_config(tmp_path))

    assert len(res.drivers) >= 8
    assert len(res.constructors) >= 5
    assert res.source_status["fantasy_drivers"] == "missing"
    assert any("synthetic fallback" in w for w in res.warnings)
