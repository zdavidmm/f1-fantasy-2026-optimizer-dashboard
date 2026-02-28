from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any

import yaml

from .build_site import build_site
from .explain import build_transfer_plan, explain_lineup, suggest_chip
from .optimizer import optimize_lineups
from .providers.cache import ensure_dir, load_json, save_json
from .providers.fantasy_api import fetch_fantasy_data
from .providers.fastf1_provider import fetch_fastf1_signals
from .providers.openf1_provider import fetch_openf1_data


def _load_config(path: str = "config.yaml") -> dict[str, Any]:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def _to_plain_fantasy(fantasy_data: Any) -> dict[str, Any]:
    return {
        "drivers": [d.model_dump() for d in fantasy_data.drivers],
        "constructors": [c.model_dump() for c in fantasy_data.constructors],
        "events": fantasy_data.events,
    }


def _write_summary(path: Path, data: dict[str, Any]) -> None:
    balanced = data.get("lineups", {}).get("strategies", {}).get("balanced", {})
    lines = [
        "# F1 Fantasy 2026 Summary",
        "",
        f"Run timestamp (UTC): {data['meta']['generated_at_utc']}",
        "",
        "## Recommended lineup (Balanced)",
    ]
    for d in balanced.get("drivers", []):
        lines.append(f"- Driver: {d['name']} ({d['price']})")
    for c in balanced.get("constructors", []):
        lines.append(f"- Constructor: {c['name']} ({c['price']})")
    lines += [
        "",
        "## Expected points",
        f"- Total: {balanced.get('expected_points', {}).get('total', 0)}",
        f"- Breakdown: {json.dumps(balanced.get('expected_points', {}).get('breakdown', {}))}",
        "",
        "## Key reasons",
    ]
    for reason in data.get("explanations", {}).get("balanced", []):
        lines.append(f"- {reason}")

    lines += ["", "## Warnings / Missing Components"]
    warnings = data.get("warnings", [])
    if warnings:
        for w in warnings:
            lines.append(f"- {w}")
    else:
        lines.append("- None")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_pipeline(mode: str) -> dict[str, Any]:
    config = _load_config()
    generated_at = dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    fantasy = fetch_fantasy_data(config)
    fastf1 = fetch_fastf1_signals(config)
    openf1 = fetch_openf1_data()

    dataset = {
        "meta": {
            "generated_at_utc": generated_at,
            "mode": mode,
        },
        "fantasy": _to_plain_fantasy(fantasy),
        "signals": {
            "fastf1": fastf1,
            "openf1": openf1,
        },
    }

    lineups = optimize_lineups(dataset, config)
    previous_latest = load_json(config["providers"]["latest_json"])
    previous_balanced = None
    if isinstance(previous_latest, dict):
        previous_balanced = previous_latest.get("lineups", {}).get("strategies", {}).get("balanced")
    new_balanced = lineups.get("strategies", {}).get("balanced", {})

    transfer_plan = build_transfer_plan(previous_balanced, new_balanced, free_transfers=2)
    chip = suggest_chip(dataset["signals"], lineups)

    paradigms = [
        "constructors-first",
        "reliability-tax",
        "budget-growth",
        "transfer-discipline",
        "chip-principles",
    ]

    explanations = {}
    for strategy_name, lineup in lineups.get("strategies", {}).items():
        explanations[strategy_name] = explain_lineup(paradigms, lineup)

    warnings = []
    warnings.extend(fantasy.warnings)
    warnings.extend(fastf1.get("warnings", []))
    warnings.extend(openf1.get("warnings", []))
    warnings.extend(lineups.get("warnings", []))

    # Missing components are explicitly carried where data access is partial.
    missing_components = []
    if any("overtake" in w.lower() for w in warnings) or fastf1.get("status") != "ok":
        missing_components.append("overtakes")

    payload = {
        "meta": dataset["meta"],
        "event_schedule": dataset["fantasy"].get("events", []),
        "sources": {
            "fantasy_api": fantasy.source_status,
            "fastf1": {
                "status": fastf1.get("status"),
                "event": fastf1.get("event"),
            },
            "openf1": {
                "enabled": openf1.get("enabled"),
                "status": openf1.get("status"),
                "notes": openf1.get("notes", []),
            },
        },
        "lineups": lineups,
        "transfer_plan": transfer_plan,
        "chip_suggestion": chip,
        "explanations": explanations,
        "warnings": warnings,
        "missing_components": sorted(set(missing_components)),
    }

    latest_path = Path(config["providers"]["latest_json"])
    history_dir = ensure_dir(config["providers"]["history_dir"])
    summary_path = Path(config["providers"]["summary_md"])

    save_json(latest_path, payload)
    event_name = (fastf1.get("event", {}) or {}).get("name", "unknown_event").replace(" ", "_")
    hist_file = history_dir / f"{dt.datetime.utcnow().date().isoformat()}_{event_name}.json"
    save_json(hist_file, payload)
    _write_summary(summary_path, payload)

    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="F1 Fantasy 2026 optimizer pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    run_cmd = sub.add_parser("run", help="Fetch data and compute recommendations")
    run_cmd.add_argument("--mode", default="all", choices=["all", "live", "offline"])  # retained for future extensions

    sub.add_parser("build-site", help="Build static dashboard")

    args = parser.parse_args()

    if args.command == "run":
        payload = run_pipeline(args.mode)
        print(json.dumps({"status": "ok", "generated_at": payload["meta"]["generated_at_utc"]}, indent=2))
    elif args.command == "build-site":
        build_site("config.yaml")
        print(json.dumps({"status": "ok", "dist": "dist"}, indent=2))


if __name__ == "__main__":
    main()
