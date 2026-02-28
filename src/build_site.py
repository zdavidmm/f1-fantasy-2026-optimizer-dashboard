from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import markdown
import yaml


def _read(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _write(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


def _base_html(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <link rel=\"stylesheet\" href=\"./assets/style.css\" />
</head>
<body>
  <header class=\"top\">
    <h1>F1 Fantasy 2026 Optimizer</h1>
    <nav>
      <a href=\"./index.html\">Home</a>
      <a href=\"./why.html\">Why This Lineup</a>
      <a href=\"./scoring.html\">Scoring Rules 2026</a>
      <a href=\"./freshness.html\">Data Freshness</a>
    </nav>
  </header>
  <main>{body}</main>
</body>
</html>
"""


def _style() -> str:
    return """
:root {
  --bg: #f5f1ea;
  --panel: #fffaf2;
  --text: #1f2933;
  --accent: #d1495b;
  --ink: #2b2d42;
}
body { margin:0; font-family: Georgia, 'Times New Roman', serif; background: radial-gradient(circle at top right, #ffddb0, var(--bg)); color:var(--text); }
.top { padding: 1rem 1.25rem; border-bottom: 1px solid #dccfbf; background: rgba(255,250,242,0.9); position: sticky; top:0; }
nav a { margin-right: 1rem; color: var(--ink); text-decoration: none; font-weight: 600; }
main { max-width: 1000px; margin: 1rem auto; padding: 1rem; }
.card { background: var(--panel); border: 1px solid #dfd3c3; border-radius: 10px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 8px 20px rgba(43,45,66,.07); }
button.tab { background: #f4e6d0; border: 1px solid #d5c2a8; padding: .5rem .75rem; margin-right: .5rem; cursor: pointer; }
button.tab.active { background: var(--accent); color: white; border-color: var(--accent); }
pre { white-space: pre-wrap; }
.table { width:100%; border-collapse: collapse; }
.table th,.table td { border-bottom: 1px solid #e8ddcf; text-align:left; padding: .35rem; }
.warn { color:#8a1c1c; font-weight:700; }
"""


def build_site(config_path: str = "config.yaml") -> None:
    config = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    latest_path = Path(config["providers"]["latest_json"])
    if not latest_path.exists():
        sample = Path("public/data/sample.json")
        latest_path.parent.mkdir(parents=True, exist_ok=True)
        latest_path.write_text(sample.read_text(encoding="utf-8"), encoding="utf-8")

    data = json.loads(latest_path.read_text(encoding="utf-8"))
    dist = Path("dist")
    (dist / "assets").mkdir(parents=True, exist_ok=True)
    _write(dist / "assets" / "style.css", _style())
    _write(dist / "data" / "latest.json", json.dumps(data, indent=2))

    strategies = data.get("lineups", {}).get("strategies", {})
    tabs = "".join([f"<button class='tab' onclick=\"showTab('{k}')\">{k}</button>" for k in strategies])
    panes = []
    for name, lineup in strategies.items():
        drivers_rows = "".join([f"<tr><td>{d['name']}</td><td>{d['price']}</td><td>{d['expected_total']}</td></tr>" for d in lineup["drivers"]])
        ctor_rows = "".join([f"<tr><td>{c['name']}</td><td>{c['price']}</td><td>{c['expected_total']}</td></tr>" for c in lineup["constructors"]])
        panes.append(
            f"""<section id='tab-{name}' class='card tab-pane' style='display:none'>
            <h2>{name.title()} Strategy</h2>
            <p>Captain: <strong>{lineup['captain']}</strong> | Cost: {lineup['total_cost']}</p>
            <p>Expected points: {lineup['expected_points']['total']} (objective-adjusted {lineup['expected_points']['objective_adjusted']})</p>
            <h3>Drivers</h3>
            <table class='table'><tr><th>Name</th><th>Cost</th><th>Expected</th></tr>{drivers_rows}</table>
            <h3>Constructors</h3>
            <table class='table'><tr><th>Name</th><th>Cost</th><th>Expected</th></tr>{ctor_rows}</table>
            </section>"""
        )

    home_body = f"""
    <div class='card'><h2>Recommended Lineup</h2><p>Updated: {data.get('meta', {}).get('generated_at_utc')}</p>{tabs}</div>
    {''.join(panes)}
    <script>
    const tabs=[...document.querySelectorAll('.tab')];
    function showTab(name){{document.querySelectorAll('.tab-pane').forEach(p=>p.style.display='none');document.getElementById('tab-'+name).style.display='block';tabs.forEach(t=>t.classList.remove('active'));tabs.find(t=>t.textContent===name).classList.add('active');}}
    if(tabs.length){{showTab(tabs[0].textContent);}}
    </script>
    """
    _write(dist / "index.html", _base_html("F1 Fantasy 2026 Optimizer", home_body))

    why_reasons = "".join([f"<li>{r}</li>" for r in data.get("explanations", {}).get("balanced", [])])
    transfer = data.get("transfer_plan", {})
    moves = "".join([f"<li>{m['out']} -> {m['in']}</li>" for m in transfer.get("moves", [])]) or "<li>No moves required.</li>"
    why_body = f"""
    <section class='card'>
      <h2>Why this lineup</h2>
      <ul>{why_reasons}</ul>
      <h3>Transfer plan</h3>
      <p>Transfers used: {transfer.get('transfers_used', 0)} | Free: {transfer.get('free_transfers', 2)} | Penalty: {transfer.get('penalty', 0)}</p>
      <ul>{moves}</ul>
      <h3>Chip suggestion</h3>
      <p><strong>{data.get('chip_suggestion', {}).get('chip', 'N/A')}</strong>: {data.get('chip_suggestion', {}).get('reason', 'N/A')}</p>
    </section>
    """
    _write(dist / "why.html", _base_html("Why This Lineup", why_body))

    scoring_md = _read("docs/SCORING_2026.md")
    _write(dist / "docs" / "SCORING_2026.md", scoring_md)
    scoring_html = markdown.markdown(scoring_md)
    scoring_body = f"<section class='card'>{scoring_html}<p><a href='./docs/SCORING_2026.md'>Raw markdown</a></p></section>"
    _write(dist / "scoring.html", _base_html("Scoring Rules 2026", scoring_body))

    src = data.get("sources", {})
    warn_lines = "".join([f"<li class='warn'>{w}</li>" for w in data.get("warnings", [])]) or "<li>None</li>"
    freshness_body = f"""
    <section class='card'>
      <h2>Data Freshness and Sources</h2>
      <p>Last run UTC: {data.get('meta', {}).get('generated_at_utc')}</p>
      <pre>{json.dumps(src, indent=2)}</pre>
      <h3>Warnings</h3>
      <ul>{warn_lines}</ul>
    </section>
    """
    _write(dist / "freshness.html", _base_html("Data Freshness", freshness_body))

    # Ensure latest is available under public/data as a primary artifact.
    latest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
