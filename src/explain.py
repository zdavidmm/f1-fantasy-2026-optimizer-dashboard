from __future__ import annotations

from typing import Any

from .scoring_2026 import transfer_penalty


def suggest_chip(signals: dict[str, Any], lineups: dict[str, Any]) -> dict[str, Any]:
    fastf1 = signals.get("fastf1", {})
    warnings = fastf1.get("warnings", [])
    balanced = lineups.get("strategies", {}).get("balanced", {})
    risk = float(balanced.get("risk", {}).get("downside_proxy", 0.2))

    if risk < 0.12 and not warnings:
        return {
            "chip": "Limitless",
            "reason": "Weekend appears predictable with low downside risk and stable form gaps.",
        }
    if risk > 0.22:
        return {
            "chip": "Autopilot",
            "reason": "High uncertainty and elevated DNF-risk proxies suggest reducing manual captain ambiguity.",
        }
    return {
        "chip": "Wildcard",
        "reason": "Balanced state indicates medium variance; wildcard can restructure for compounding value growth.",
    }


def build_transfer_plan(previous_lineup: dict[str, Any] | None, new_lineup: dict[str, Any], free_transfers: int = 2) -> dict[str, Any]:
    if not previous_lineup:
        return {
            "transfers_used": 0,
            "free_transfers": free_transfers,
            "penalty": 0,
            "moves": [],
            "notes": ["No previous lineup found; transfer plan initialized without penalties."],
        }

    old_drivers = {d["name"] for d in previous_lineup.get("drivers", [])}
    old_ctors = {c["name"] for c in previous_lineup.get("constructors", [])}
    new_drivers = {d["name"] for d in new_lineup.get("drivers", [])}
    new_ctors = {c["name"] for c in new_lineup.get("constructors", [])}

    out_moves = sorted(new_drivers - old_drivers) + sorted(new_ctors - old_ctors)
    in_moves = sorted(old_drivers - new_drivers) + sorted(old_ctors - new_ctors)

    transfers = max(len(out_moves), len(in_moves))
    penalty = transfer_penalty(transfers, free_transfers)

    moves = []
    for out_name, in_name in zip(in_moves, out_moves):
        moves.append({"out": out_name, "in": in_name})

    return {
        "transfers_used": transfers,
        "free_transfers": free_transfers,
        "penalty": penalty.total,
        "moves": moves,
        "notes": [
            "Discipline rule: avoid -10 bleed unless objective-adjusted gain clearly exceeds hit.",
        ],
    }


def explain_lineup(paradigms: list[str], lineup: dict[str, Any]) -> list[str]:
    reasons = []
    breakdown = lineup.get("expected_points", {}).get("breakdown", {})
    risk = lineup.get("risk", {}).get("downside_proxy", 0.0)

    if "constructors-first" in paradigms:
        reasons.append(
            f"Constructors-first: pitstop+aggregate projection contributes {breakdown.get('pitstop', 0)} expected points."
        )
    if "reliability-tax" in paradigms:
        reasons.append(f"Reliability tax: downside proxy held at {risk} by avoiding fragile pairings.")
    if "budget-growth" in paradigms:
        reasons.append("Budget growth: lineup keeps high trend assets to compound future flexibility.")
    if "transfer-discipline" in paradigms:
        reasons.append("Transfer discipline: plan prioritizes minimal changes to avoid avoidable -10 penalties.")
    if "chip-principles" in paradigms:
        reasons.append("Chip principle: recommendation picks the chip aligned to predictability and captain certainty.")
    return reasons
