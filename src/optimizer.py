from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Any


@dataclass
class DriverAsset:
    id: str
    name: str
    team: str
    price: float
    expected_quali: float
    expected_sprint: float
    expected_race: float
    dnf_risk: float
    price_growth: float

    @property
    def expected_total(self) -> float:
        return self.expected_quali + self.expected_sprint + self.expected_race


@dataclass
class ConstructorAsset:
    id: str
    name: str
    price: float
    expected_quali: float
    expected_sprint: float
    expected_race: float
    expected_pitstop: float
    dnf_risk: float
    price_growth: float

    @property
    def expected_total(self) -> float:
        return self.expected_quali + self.expected_sprint + self.expected_race + self.expected_pitstop


def _normalize_name(name: str) -> str:
    return "".join(ch for ch in name.lower() if ch.isalpha())


def _build_assets(data: dict[str, Any], config: dict[str, Any]) -> tuple[list[DriverAsset], list[ConstructorAsset], list[str]]:
    warnings: list[str] = []
    weights = config["model_weights"]
    fast_signals = data["signals"]["fastf1"]
    openf1 = data["signals"]["openf1"]

    driver_sig = fast_signals.get("driver_signals", {})
    con_sig = fast_signals.get("constructor_signals", {})

    drivers: list[DriverAsset] = []
    for d in data["fantasy"]["drivers"]:
        key = str(d["name"]).split(" ")[-1][:3].upper()
        sig = driver_sig.get(key, {})
        q = float(sig.get("qualifying_form", 7.0))
        s = float(sig.get("sprint_form", 4.0))
        r = float(sig.get("race_form", 10.0))
        dnf_risk = float(sig.get("dnf_risk", 0.15))

        # Transparent expected-points model from weighted form components.
        expected_quali = weights["qualifying_form"] * q
        expected_sprint = weights["sprint_form"] * s
        expected_race = weights["race_form"] * r
        price_growth = max(0.0, (q + r) / 40.0)

        drivers.append(
            DriverAsset(
                id=str(d["id"]),
                name=str(d["name"]),
                team=str(d["team"]),
                price=float(d["price"]),
                expected_quali=expected_quali,
                expected_sprint=expected_sprint,
                expected_race=expected_race,
                dnf_risk=dnf_risk,
                price_growth=price_growth,
            )
        )

    constructors: list[ConstructorAsset] = []
    for c in data["fantasy"]["constructors"]:
        c_name = str(c["name"])
        matched = None
        c_norm = _normalize_name(c_name)
        for team_name, sig in con_sig.items():
            if _normalize_name(team_name) in c_norm or c_norm in _normalize_name(team_name):
                matched = sig
                break
        sig = matched or {}
        q = float(sig.get("pitstop_proxy", 5.0))
        s = float(sig.get("pitstop_proxy", 4.0))
        r = float(sig.get("pitstop_proxy", 8.0))
        pitstop = float(sig.get("pitstop_proxy", 5.0))
        dnf_risk = 1.0 - float(sig.get("reliability", 0.85))

        if openf1.get("enabled") and openf1.get("status") == "ok":
            pitstop += 0.5

        expected_quali = weights["qualifying_form"] * q
        expected_sprint = weights["sprint_form"] * s
        expected_race = weights["race_form"] * r
        expected_pitstop = weights["pitstop_constructor"] * pitstop
        price_growth = max(0.0, (q + pitstop) / 25.0)

        constructors.append(
            ConstructorAsset(
                id=str(c["id"]),
                name=c_name,
                price=float(c["price"]),
                expected_quali=expected_quali,
                expected_sprint=expected_sprint,
                expected_race=expected_race,
                expected_pitstop=expected_pitstop,
                dnf_risk=dnf_risk,
                price_growth=price_growth,
            )
        )

    if not drivers or not constructors:
        warnings.append("Insufficient assets to optimize lineup")
    return drivers, constructors, warnings


def _lineup_payload(drivers: list[DriverAsset], constructors: list[ConstructorAsset], strategy: str, cfg: dict[str, Any]) -> dict[str, Any]:
    risk_weight = float(cfg["risk_weights"][strategy])
    growth_weight = float(cfg["price_growth_weights"][strategy])

    d_quali = sum(d.expected_quali for d in drivers)
    d_sprint = sum(d.expected_sprint for d in drivers)
    d_race = sum(d.expected_race for d in drivers)
    c_quali = sum(c.expected_quali for c in constructors)
    c_sprint = sum(c.expected_sprint for c in constructors)
    c_race = sum(c.expected_race for c in constructors)
    c_pit = sum(c.expected_pitstop for c in constructors)

    expected_raw = d_quali + d_sprint + d_race + c_quali + c_sprint + c_race + c_pit
    dnf_risk = sum(d.dnf_risk for d in drivers) / len(drivers)
    c_risk = sum(c.dnf_risk for c in constructors) / len(constructors)
    downside_risk = 0.7 * dnf_risk + 0.3 * c_risk
    growth = sum(d.price_growth for d in drivers) + sum(c.price_growth for c in constructors)

    objective = expected_raw - risk_weight * downside_risk * 100 + growth_weight * growth * 10
    total_cost = sum(d.price for d in drivers) + sum(c.price for c in constructors)

    captain = max(drivers, key=lambda x: (x.expected_total, -x.dnf_risk, x.name))
    vice_captain = sorted(drivers, key=lambda x: (x.expected_total, -x.dnf_risk, x.name), reverse=True)[1]

    return {
        "strategy": strategy,
        "drivers": [d.__dict__ | {"expected_total": round(d.expected_total, 3)} for d in drivers],
        "constructors": [c.__dict__ | {"expected_total": round(c.expected_total, 3)} for c in constructors],
        "captain": captain.name,
        "multipliers": {"captain": 2, "vice_captain": 1.2, "vice_captain_name": vice_captain.name},
        "total_cost": round(total_cost, 2),
        "expected_points": {
            "total": round(expected_raw, 3),
            "objective_adjusted": round(objective, 3),
            "breakdown": {
                "qualifying": round(d_quali + c_quali, 3),
                "sprint": round(d_sprint + c_sprint, 3),
                "race": round(d_race + c_race, 3),
                "pitstop": round(c_pit, 3),
            },
        },
        "risk": {
            "downside_proxy": round(downside_risk, 4),
            "avg_driver_dnf_risk": round(dnf_risk, 4),
            "avg_constructor_dnf_risk": round(c_risk, 4),
        },
        "growth": {
            "price_growth_proxy": round(growth, 4),
        },
    }


def _solve_with_pulp(drivers: list[DriverAsset], constructors: list[ConstructorAsset], budget: float, strategy: str, cfg: dict[str, Any]) -> tuple[list[DriverAsset], list[ConstructorAsset]]:
    import pulp  # type: ignore

    risk_w = float(cfg["risk_weights"][strategy])
    growth_w = float(cfg["price_growth_weights"][strategy])

    prob = pulp.LpProblem(f"lineup_{strategy}", pulp.LpMaximize)

    x_d = {d.id: pulp.LpVariable(f"d_{d.id}", cat="Binary") for d in drivers}
    x_c = {c.id: pulp.LpVariable(f"c_{c.id}", cat="Binary") for c in constructors}

    obj_d = [x_d[d.id] * (d.expected_total - risk_w * d.dnf_risk * 10 + growth_w * d.price_growth * 5) for d in drivers]
    obj_c = [x_c[c.id] * (c.expected_total - risk_w * c.dnf_risk * 10 + growth_w * c.price_growth * 5) for c in constructors]
    prob += pulp.lpSum(obj_d + obj_c)

    prob += pulp.lpSum(x_d[d.id] for d in drivers) == 5
    prob += pulp.lpSum(x_c[c.id] for c in constructors) == 2
    prob += pulp.lpSum(x_d[d.id] * d.price for d in drivers) + pulp.lpSum(x_c[c.id] * c.price for c in constructors) <= budget

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    chosen_d = [d for d in drivers if x_d[d.id].value() == 1]
    chosen_c = [c for c in constructors if x_c[c.id].value() == 1]
    if len(chosen_d) != 5 or len(chosen_c) != 2:
        raise RuntimeError("No feasible lineup from pulp")
    return chosen_d, chosen_c


def _solve_with_bruteforce(drivers: list[DriverAsset], constructors: list[ConstructorAsset], budget: float, strategy: str, cfg: dict[str, Any]) -> tuple[list[DriverAsset], list[ConstructorAsset]]:
    risk_w = float(cfg["risk_weights"][strategy])
    growth_w = float(cfg["price_growth_weights"][strategy])

    best_selection: tuple[list[DriverAsset], list[ConstructorAsset]] | None = None
    best_key: tuple[float, float, list[str], list[str]] | None = None

    for d_combo in itertools.combinations(drivers, 5):
        d_cost = sum(d.price for d in d_combo)
        if d_cost > budget:
            continue
        for c_combo in itertools.combinations(constructors, 2):
            cost = d_cost + sum(c.price for c in c_combo)
            if cost > budget:
                continue
            raw = sum(d.expected_total for d in d_combo) + sum(c.expected_total for c in c_combo)
            risk = sum(d.dnf_risk for d in d_combo) / 5
            growth = sum(d.price_growth for d in d_combo) + sum(c.price_growth for c in c_combo)
            score = raw - risk_w * risk * 100 + growth_w * growth * 10
            key = (
                score,
                -cost,
                sorted(d.name for d in d_combo),
                sorted(c.name for c in c_combo),
            )
            if best_key is None or key > best_key:
                best_key = key
                best_selection = (list(d_combo), list(c_combo))

    if best_selection is None:
        raise RuntimeError("No feasible lineup from bruteforce")
    return best_selection


def optimize_lineups(dataset: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    drivers, constructors, warnings = _build_assets(dataset, config)
    budget = float(config["budget_cap"])
    out: dict[str, Any] = {"strategies": {}, "warnings": warnings}

    if len(drivers) < 5 or len(constructors) < 2:
        out["warnings"].append("Not enough players for optimization")
        return out

    for strategy in config["optimizer"]["strategies"]:
        try:
            sel_d, sel_c = _solve_with_pulp(drivers, constructors, budget, strategy, config)
            method = "pulp"
        except Exception:
            sel_d, sel_c = _solve_with_bruteforce(drivers, constructors, budget, strategy, config)
            method = "bruteforce"

        out["strategies"][strategy] = _lineup_payload(sel_d, sel_c, strategy, config) | {"solver": method}

    return out
