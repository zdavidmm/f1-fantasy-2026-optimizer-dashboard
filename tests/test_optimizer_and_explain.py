from src.explain import build_transfer_plan, suggest_chip
from src.optimizer import optimize_lineups


def _base_dataset():
    drivers = [
        {"id": "d1", "name": "Max Verstappen", "team": "Red Bull", "price": 30.0},
        {"id": "d2", "name": "Lando Norris", "team": "McLaren", "price": 27.0},
        {"id": "d3", "name": "Charles Leclerc", "team": "Ferrari", "price": 25.0},
        {"id": "d4", "name": "George Russell", "team": "Mercedes", "price": 23.0},
        {"id": "d5", "name": "Oscar Piastri", "team": "McLaren", "price": 24.0},
        {"id": "d6", "name": "Lewis Hamilton", "team": "Ferrari", "price": 22.0},
        {"id": "d7", "name": "Fernando Alonso", "team": "Aston Martin", "price": 18.0},
    ]
    constructors = [
        {"id": "c1", "name": "Red Bull", "price": 29.0},
        {"id": "c2", "name": "McLaren", "price": 27.0},
        {"id": "c3", "name": "Ferrari", "price": 26.0},
        {"id": "c4", "name": "Mercedes", "price": 24.0},
    ]
    return {
        "fantasy": {"drivers": drivers, "constructors": constructors, "events": []},
        "signals": {
            "fastf1": {
                "driver_signals": {
                    "VER": {"qualifying_form": 18, "sprint_form": 12, "race_form": 20, "dnf_risk": 0.08, "team": "Red Bull", "name": "Max Verstappen"},
                    "NOR": {"qualifying_form": 16, "sprint_form": 10, "race_form": 18, "dnf_risk": 0.10, "team": "McLaren", "name": "Lando Norris"},
                    "LEC": {"qualifying_form": 14, "sprint_form": 8, "race_form": 16, "dnf_risk": 0.11, "team": "Ferrari", "name": "Charles Leclerc"},
                    "RUS": {"qualifying_form": 12, "sprint_form": 7, "race_form": 14, "dnf_risk": 0.12, "team": "Mercedes", "name": "George Russell"},
                    "PIA": {"qualifying_form": 13, "sprint_form": 8, "race_form": 15, "dnf_risk": 0.12, "team": "McLaren", "name": "Oscar Piastri"},
                    "HAM": {"qualifying_form": 11, "sprint_form": 7, "race_form": 13, "dnf_risk": 0.13, "team": "Ferrari", "name": "Lewis Hamilton"},
                    "ALO": {"qualifying_form": 8, "sprint_form": 5, "race_form": 10, "dnf_risk": 0.18, "team": "Aston Martin", "name": "Fernando Alonso"},
                },
                "constructor_signals": {
                    "Red Bull": {"pitstop_proxy": 9.0, "reliability": 0.93},
                    "McLaren": {"pitstop_proxy": 8.5, "reliability": 0.92},
                    "Ferrari": {"pitstop_proxy": 8.0, "reliability": 0.90},
                    "Mercedes": {"pitstop_proxy": 7.5, "reliability": 0.89},
                },
                "warnings": [],
            },
            "openf1": {"enabled": False, "status": "skipped"},
        },
    }


def _config():
    return {
        "budget_cap": 180.0,
        "model_weights": {
            "qualifying_form": 0.30,
            "race_form": 0.35,
            "sprint_form": 0.10,
            "reliability": 0.15,
            "pitstop_constructor": 0.10,
        },
        "risk_weights": {"safe": 0.30, "balanced": 0.15, "high_variance": 0.05},
        "price_growth_weights": {"safe": 0.05, "balanced": 0.10, "high_variance": 0.15},
        "optimizer": {"strategies": ["safe", "balanced", "high_variance"]},
    }


def test_optimizer_returns_three_strategies_with_valid_roster_and_budget():
    result = optimize_lineups(_base_dataset(), _config())
    assert set(result["strategies"].keys()) == {"safe", "balanced", "high_variance"}

    for lineup in result["strategies"].values():
        assert len(lineup["drivers"]) == 5
        assert len(lineup["constructors"]) == 2
        assert lineup["total_cost"] <= 180.0
        assert lineup["captain"] in {d["name"] for d in lineup["drivers"]}
        assert lineup["expected_points"]["total"] > 0


def test_build_transfer_plan_applies_minus_ten_per_extra_transfer():
    old = {
        "drivers": [{"name": "A"}, {"name": "B"}, {"name": "C"}, {"name": "D"}, {"name": "E"}],
        "constructors": [{"name": "X"}, {"name": "Y"}],
    }
    new = {
        "drivers": [{"name": "A"}, {"name": "B"}, {"name": "F"}, {"name": "G"}, {"name": "H"}],
        "constructors": [{"name": "X"}, {"name": "Z"}],
    }
    plan = build_transfer_plan(old, new, free_transfers=2)
    assert plan["transfers_used"] == 4
    assert plan["penalty"] == -20
    assert len(plan["moves"]) == 4


def test_chip_suggestion_paths():
    lineups_low_risk = {"strategies": {"balanced": {"risk": {"downside_proxy": 0.10}}}}
    out1 = suggest_chip({"fastf1": {"warnings": []}}, lineups_low_risk)
    assert out1["chip"] == "Limitless"

    lineups_high_risk = {"strategies": {"balanced": {"risk": {"downside_proxy": 0.30}}}}
    out2 = suggest_chip({"fastf1": {"warnings": []}}, lineups_high_risk)
    assert out2["chip"] == "Autopilot"

    lineups_mid_risk = {"strategies": {"balanced": {"risk": {"downside_proxy": 0.18}}}}
    out3 = suggest_chip({"fastf1": {"warnings": ["session delayed"]}}, lineups_mid_risk)
    assert out3["chip"] == "Wildcard"
