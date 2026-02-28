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
  --bg: #f7efe1;
  --bg2: #f2deba;
  --panel: #fff9ef;
  --text: #17212b;
  --muted: #4f5f70;
  --accent: #c44536;
  --accent2: #0f766e;
  --ink: #1e293b;
  --line: #decfbb;
  --shadow: 0 12px 28px rgba(23, 33, 43, 0.12);
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: 'Palatino Linotype', Palatino, Georgia, serif;
  color: var(--text);
  background:
    radial-gradient(circle at 12% 12%, #fff3dc 0, transparent 38%),
    radial-gradient(circle at 88% 18%, #f8d7a5 0, transparent 30%),
    linear-gradient(180deg, var(--bg2), var(--bg));
}
.top {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--line);
  background: rgba(255, 249, 239, 0.92);
  backdrop-filter: blur(6px);
  position: sticky;
  top: 0;
  z-index: 10;
}
.top h1 { margin: 0; font-size: 1.45rem; letter-spacing: 0.03em; }
nav { margin-top: 0.35rem; }
nav a {
  margin-right: 0.8rem;
  color: var(--ink);
  text-decoration: none;
  font-weight: 700;
  border-bottom: 2px solid transparent;
}
nav a:hover { border-bottom-color: var(--accent); }
main { max-width: 1080px; margin: 1rem auto; padding: 1rem; animation: fadein 350ms ease-out; }
.hero {
  background: linear-gradient(130deg, #fffaf0 0%, #fce8c9 60%, #f8d4a3 100%);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1rem 1.1rem;
  box-shadow: var(--shadow);
  margin-bottom: 0.9rem;
}
.hero p { margin: 0.35rem 0; color: var(--muted); }
.stats { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 0.7rem; margin: 0.85rem 0; }
.stat {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.75rem;
}
.stat .k { font-size: 0.75rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.04em; }
.stat .v { font-size: 1.1rem; font-weight: 700; margin-top: 0.2rem; }
.card {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 0.9rem;
  box-shadow: var(--shadow);
}
.tab-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.6rem; }
button.tab {
  background: #f0dec4;
  border: 1px solid #d4bea0;
  padding: 0.5rem 0.85rem;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 700;
}
button.tab.active { background: var(--accent); color: #fff; border-color: var(--accent); }
pre {
  white-space: pre-wrap;
  background: #f7f0e4;
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 0.8rem;
}
.table { width:100%; border-collapse: collapse; }
.table th,.table td { border-bottom: 1px solid #e8ddcf; text-align:left; padding: .4rem; }
.table th { color: var(--muted); font-size: 0.85rem; }
.warn { color:#8a1c1c; font-weight:700; }
.pill {
  display: inline-block;
  border-radius: 999px;
  padding: 0.22rem 0.55rem;
  border: 1px solid #cab08d;
  background: #f8ead5;
  font-size: 0.8rem;
  margin-right: 0.4rem;
}
@keyframes fadein {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 900px) {
  .stats { grid-template-columns: repeat(2, minmax(0,1fr)); }
}
@media (max-width: 640px) {
  .top h1 { font-size: 1.2rem; }
  .stats { grid-template-columns: 1fr; }
  nav a { display: inline-block; margin-bottom: 0.35rem; }
}
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
            <p><span class='pill'>Captain {lineup['captain']}</span><span class='pill'>Cost {lineup['total_cost']}</span><span class='pill'>Solver {lineup.get('solver','n/a')}</span></p>
            <p>Expected points: {lineup['expected_points']['total']} (objective-adjusted {lineup['expected_points']['objective_adjusted']})</p>
            <h3>Drivers</h3>
            <table class='table'><tr><th>Name</th><th>Cost</th><th>Expected</th></tr>{drivers_rows}</table>
            <h3>Constructors</h3>
            <table class='table'><tr><th>Name</th><th>Cost</th><th>Expected</th></tr>{ctor_rows}</table>
            </section>"""
        )

    balanced = strategies.get("balanced", {})
    transfer = data.get("transfer_plan", {})
    chip = data.get("chip_suggestion", {})
    home_body = f"""
    <section class='hero'>
      <h2>Recommended Lineup Dashboard</h2>
      <p>Data timestamp: <strong>{data.get('meta', {}).get('generated_at_utc')}</strong></p>
      <div class='stats'>
        <div class='stat'><div class='k'>Balanced Points</div><div class='v'>{balanced.get('expected_points', {}).get('total', 'N/A')}</div></div>
        <div class='stat'><div class='k'>Balanced Cost</div><div class='v'>{balanced.get('total_cost', 'N/A')}</div></div>
        <div class='stat'><div class='k'>Transfer Penalty</div><div class='v'>{transfer.get('penalty', 0)}</div></div>
        <div class='stat'><div class='k'>Chip Suggestion</div><div class='v'>{chip.get('chip', 'N/A')}</div></div>
      </div>
    </section>
    <div class='card'><h2>Strategy Compare</h2><div class='tab-row'>{tabs}</div></div>
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
