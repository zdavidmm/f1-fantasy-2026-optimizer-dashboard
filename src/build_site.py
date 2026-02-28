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
  <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\"> 
  <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>
  <link href=\"https://fonts.googleapis.com/css2?family=Sora:wght@400;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap\" rel=\"stylesheet\">
  <link rel=\"stylesheet\" href=\"./assets/style.css\" />
</head>
<body>
  <div class=\"bg-mesh\" aria-hidden=\"true\"></div>
  <header class=\"top\">
    <div class=\"brand\">F1 Fantasy 2026 Optimizer</div>
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
  --bg: #0d1117;
  --bg-soft: #111827;
  --text: #e5e7eb;
  --muted: #9ca3af;
  --card: rgba(17, 24, 39, 0.72);
  --card-strong: rgba(15, 23, 42, 0.86);
  --line: rgba(148, 163, 184, 0.25);
  --accent: #f97316;
  --accent-2: #0ea5e9;
  --good: #10b981;
  --warn: #f59e0b;
  --danger: #ef4444;
  --radius: 16px;
  --shadow: 0 18px 45px rgba(0, 0, 0, 0.35);
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  font-family: Sora, system-ui, -apple-system, Segoe UI, sans-serif;
  color: var(--text);
  background: radial-gradient(circle at 12% 18%, #172554 0%, transparent 38%),
              radial-gradient(circle at 88% 4%, #7c2d12 0%, transparent 30%),
              linear-gradient(160deg, #05070b, #0a1120 42%, #111827);
  min-height: 100vh;
}
.bg-mesh {
  position: fixed;
  inset: 0;
  pointer-events: none;
  background-image: linear-gradient(rgba(255,255,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.03) 1px, transparent 1px);
  background-size: 34px 34px;
  mask-image: radial-gradient(circle at center, black 35%, transparent 100%);
}
.top {
  position: sticky;
  top: 0;
  z-index: 15;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.65rem;
  padding: 0.95rem 1.2rem;
  backdrop-filter: blur(14px);
  background: rgba(2, 6, 23, 0.66);
  border-bottom: 1px solid var(--line);
}
.brand {
  font-family: Fraunces, serif;
  font-size: clamp(1.1rem, 2.6vw, 1.5rem);
  font-weight: 700;
  letter-spacing: .02em;
}
nav { display: flex; flex-wrap: wrap; gap: .45rem; }
nav a {
  color: #dbeafe;
  text-decoration: none;
  font-weight: 600;
  font-size: .88rem;
  padding: .44rem .72rem;
  border-radius: 999px;
  border: 1px solid transparent;
  background: rgba(15, 23, 42, 0.4);
}
nav a:hover {
  border-color: rgba(14, 165, 233, 0.45);
  background: rgba(30, 41, 59, 0.75);
}
main {
  max-width: 1160px;
  margin: 1rem auto 2.5rem;
  padding: 0 1rem;
  animation: rise .35s ease-out;
}
.hero {
  border-radius: calc(var(--radius) + 4px);
  border: 1px solid var(--line);
  background: linear-gradient(145deg, rgba(14,165,233,0.15), rgba(249,115,22,0.15));
  padding: clamp(1rem, 2vw, 1.4rem);
  box-shadow: var(--shadow);
}
.hero h1 {
  font-family: Fraunces, serif;
  margin: 0;
  font-size: clamp(1.3rem, 2.8vw, 2rem);
}
.hero p { margin: .45rem 0 0; color: var(--muted); }
.stats {
  margin-top: .9rem;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: .7rem;
}
.stat {
  border-radius: 12px;
  padding: .75rem;
  background: var(--card);
  border: 1px solid var(--line);
}
.stat .k { color: var(--muted); font-size: .73rem; text-transform: uppercase; letter-spacing: .06em; }
.stat .v { margin-top: .25rem; font-size: 1.1rem; font-weight: 800; }
.grid { display: grid; grid-template-columns: 1fr; gap: .9rem; margin-top: .9rem; }
.card {
  border-radius: var(--radius);
  border: 1px solid var(--line);
  background: var(--card-strong);
  box-shadow: var(--shadow);
  padding: 1rem;
}
.card h2 { margin: 0 0 .55rem; font-size: 1.05rem; }
.tab-row { display: flex; flex-wrap: wrap; gap: .5rem; }
button.tab {
  border-radius: 999px;
  border: 1px solid rgba(148,163,184,.35);
  color: #e2e8f0;
  background: rgba(30, 41, 59, 0.7);
  font-weight: 700;
  font-size: .83rem;
  padding: .45rem .8rem;
  cursor: pointer;
}
button.tab.active {
  background: linear-gradient(90deg, var(--accent), var(--accent-2));
  border-color: transparent;
  color: #0b1020;
}
.kpis { display: flex; flex-wrap: wrap; gap: .45rem; margin: .4rem 0 .75rem; }
.pill {
  border-radius: 999px;
  padding: .28rem .62rem;
  font-size: .76rem;
  font-weight: 700;
  border: 1px solid rgba(148,163,184,.35);
  background: rgba(30, 41, 59, 0.6);
}
.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0,1fr));
  gap: .65rem;
  margin-bottom: .8rem;
}
.metric {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: .65rem;
  background: rgba(15, 23, 42, .55);
}
.metric .label { font-size: .74rem; color: var(--muted); }
.metric .value { font-size: 1rem; font-weight: 700; margin-top: .22rem; }
.bars { margin: .7rem 0 .85rem; }
.bar { margin-bottom: .5rem; }
.bar .meta { display: flex; justify-content: space-between; font-size: .8rem; color: var(--muted); margin-bottom: .2rem; }
.bar .track {
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(148, 163, 184, .15);
}
.bar .fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--accent-2), var(--accent));
}
.two-col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: .8rem;
}
.table { width: 100%; border-collapse: collapse; }
.table th,.table td { padding: .42rem; text-align: left; border-bottom: 1px solid rgba(148,163,184,.2); }
.table th { color: var(--muted); font-size: .78rem; font-weight: 600; letter-spacing: .03em; }
.table td { font-size: .9rem; }
ul { margin: .3rem 0 .4rem 1rem; }
li { margin-bottom: .25rem; }
pre {
  white-space: pre-wrap;
  background: rgba(15,23,42,.62);
  border-radius: 12px;
  border: 1px solid var(--line);
  padding: .75rem;
}
.warn { color: #fca5a5; }
.note { color: #93c5fd; }
@keyframes rise {
  from { transform: translateY(8px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
@media (max-width: 980px) {
  .stats { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .two-col { grid-template-columns: 1fr; }
}
@media (max-width: 620px) {
  .stats { grid-template-columns: 1fr; }
  .metric-grid { grid-template-columns: 1fr; }
}
"""


def _strategy_panel(name: str, lineup: dict[str, Any]) -> str:
    drivers_rows = "".join(
        [f"<tr><td>{d['name']}</td><td>{d['price']}</td><td>{d['expected_total']}</td></tr>" for d in lineup["drivers"]]
    )
    ctors_rows = "".join(
        [f"<tr><td>{c['name']}</td><td>{c['price']}</td><td>{c['expected_total']}</td></tr>" for c in lineup["constructors"]]
    )

    br = lineup.get("expected_points", {}).get("breakdown", {})
    bvals = {
        "Qualifying": float(br.get("qualifying", 0)),
        "Sprint": float(br.get("sprint", 0)),
        "Race": float(br.get("race", 0)),
        "Pitstop": float(br.get("pitstop", 0)),
    }
    max_b = max(1.0, max(bvals.values()))
    bars = "".join(
        [
            (
                f"<div class='bar'><div class='meta'><span>{k}</span><span>{v:.2f}</span></div>"
                f"<div class='track'><div class='fill' style='width:{(v/max_b)*100:.1f}%'></div></div></div>"
            )
            for k, v in bvals.items()
        ]
    )

    return f"""
    <section id='tab-{name}' class='card tab-pane' style='display:none'>
      <h2>{name.title()} Strategy</h2>
      <div class='kpis'>
        <span class='pill'>Captain: {lineup['captain']}</span>
        <span class='pill'>Cost: {lineup['total_cost']}</span>
        <span class='pill'>Solver: {lineup.get('solver', 'n/a')}</span>
        <span class='pill'>Risk: {lineup.get('risk', {}).get('downside_proxy', 'n/a')}</span>
      </div>
      <div class='metric-grid'>
        <div class='metric'><div class='label'>Expected Points</div><div class='value'>{lineup.get('expected_points', {}).get('total', 0)}</div></div>
        <div class='metric'><div class='label'>Objective Adjusted</div><div class='value'>{lineup.get('expected_points', {}).get('objective_adjusted', 0)}</div></div>
      </div>
      <div class='bars'>{bars}</div>
      <div class='two-col'>
        <div>
          <h3>Drivers</h3>
          <table class='table'><tr><th>Name</th><th>Cost</th><th>Expected</th></tr>{drivers_rows}</table>
        </div>
        <div>
          <h3>Constructors</h3>
          <table class='table'><tr><th>Name</th><th>Cost</th><th>Expected</th></tr>{ctors_rows}</table>
        </div>
      </div>
    </section>
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
    panes = "".join([_strategy_panel(name, lineup) for name, lineup in strategies.items()])

    balanced = strategies.get("balanced", {})
    transfer = data.get("transfer_plan", {})
    chip = data.get("chip_suggestion", {})

    home_body = f"""
    <section class='hero'>
      <h1>Lineup Optimizer + Dashboard</h1>
      <p>Generated at {data.get('meta', {}).get('generated_at_utc', 'N/A')} UTC</p>
      <div class='stats'>
        <div class='stat'><div class='k'>Balanced Expected</div><div class='v'>{balanced.get('expected_points', {}).get('total', 'N/A')}</div></div>
        <div class='stat'><div class='k'>Balanced Cost</div><div class='v'>{balanced.get('total_cost', 'N/A')}</div></div>
        <div class='stat'><div class='k'>Transfer Penalty</div><div class='v'>{transfer.get('penalty', 0)}</div></div>
        <div class='stat'><div class='k'>Chip Suggestion</div><div class='v'>{chip.get('chip', 'N/A')}</div></div>
      </div>
    </section>
    <section class='grid'>
      <div class='card'>
        <h2>Strategy Switcher</h2>
        <div class='tab-row'>{tabs}</div>
      </div>
      {panes}
    </section>
    <script>
    const tabs=[...document.querySelectorAll('.tab')];
    function showTab(name){{
      document.querySelectorAll('.tab-pane').forEach(p=>p.style.display='none');
      const pane=document.getElementById('tab-'+name);
      if(pane) pane.style.display='block';
      tabs.forEach(t=>t.classList.toggle('active', t.textContent===name));
    }}
    if(tabs.length) showTab(tabs[0].textContent);
    </script>
    """
    _write(dist / "index.html", _base_html("F1 Fantasy 2026 Optimizer", home_body))

    why_reasons = "".join([f"<li>{r}</li>" for r in data.get("explanations", {}).get("balanced", [])])
    moves = "".join([f"<li>{m['out']} -> {m['in']}</li>" for m in transfer.get("moves", [])]) or "<li>No moves required.</li>"
    why_body = f"""
    <section class='hero'>
      <h1>Why This Lineup</h1>
      <p>Evidence-backed recommendations using current signals and constraints.</p>
    </section>
    <section class='grid'>
      <section class='card'>
        <h2>Paradigm Evidence</h2>
        <ul>{why_reasons}</ul>
      </section>
      <section class='card'>
        <h2>Transfer Plan</h2>
        <p>Used: {transfer.get('transfers_used', 0)} | Free: {transfer.get('free_transfers', 2)} | Penalty: {transfer.get('penalty', 0)}</p>
        <ul>{moves}</ul>
      </section>
      <section class='card'>
        <h2>Chip Suggestion</h2>
        <p><strong>{chip.get('chip', 'N/A')}</strong> - {chip.get('reason', 'N/A')}</p>
      </section>
    </section>
    """
    _write(dist / "why.html", _base_html("Why This Lineup", why_body))

    scoring_md = _read("docs/SCORING_2026.md")
    _write(dist / "docs" / "SCORING_2026.md", scoring_md)
    scoring_html = markdown.markdown(scoring_md)
    scoring_body = f"""
    <section class='hero'>
      <h1>Scoring Rules 2026</h1>
      <p>Source-aligned rules encoded in the scoring engine.</p>
    </section>
    <section class='card'>{scoring_html}<p><a href='./docs/SCORING_2026.md'>View raw markdown</a></p></section>
    """
    _write(dist / "scoring.html", _base_html("Scoring Rules 2026", scoring_body))

    src = data.get("sources", {})
    warnings = data.get("warnings", [])
    notes = src.get("openf1", {}).get("notes", []) if isinstance(src.get("openf1"), dict) else []
    warn_lines = "".join([f"<li class='warn'>{w}</li>" for w in warnings]) or "<li>None</li>"
    note_lines = "".join([f"<li class='note'>{n}</li>" for n in notes]) or "<li>None</li>"
    freshness_body = f"""
    <section class='hero'>
      <h1>Data Freshness & Sources</h1>
      <p>Run timestamp: {data.get('meta', {}).get('generated_at_utc', 'N/A')} UTC</p>
    </section>
    <section class='grid'>
      <section class='card'>
        <h2>Source Status</h2>
        <pre>{json.dumps(src, indent=2)}</pre>
      </section>
      <section class='card'>
        <h2>Warnings</h2>
        <ul>{warn_lines}</ul>
        <h2>Notes</h2>
        <ul>{note_lines}</ul>
      </section>
    </section>
    """
    _write(dist / "freshness.html", _base_html("Data Freshness", freshness_body))

    latest_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
