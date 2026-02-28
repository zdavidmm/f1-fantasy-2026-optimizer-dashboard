# F1 Fantasy 2026 Lineup Optimizer + Dashboard

[![build-and-deploy](https://github.com/YOUR_GITHUB_USERNAME/f1-fantasy-2026-optimizer-dashboard/actions/workflows/build.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/f1-fantasy-2026-optimizer-dashboard/actions/workflows/build.yml)

Static F1 Fantasy optimizer that fetches live data, computes recommended lineups (Safe/Balanced/High-variance), creates transfer/chip recommendations, and deploys a dashboard to GitHub Pages.

## Quickstart

```bash
make setup && make run && make serve
```

Then open `http://localhost:8000`.

## What each run produces
- `public/data/latest.json`
- `public/data/history/YYYY-MM-DD_event.json`
- `public/data/summary.md`
- `dist/` static site bundle for Pages deployment

## Commands
- `python -m src.cli run --mode all`
- `python -m src.cli build-site`

## GitHub Pages setup
1. Push repository to GitHub with default branch `main`.
2. In repository settings, open **Pages**.
3. Set source to **GitHub Actions**.
4. Workflow `.github/workflows/build.yml` deploys on push, schedule (`06:00 UTC` daily), and manual dispatch.

## Optional OpenF1 real-time integration
- Add secret `OPENF1_API_KEY` in GitHub repository secrets.
- For local development, set in `.env` (see `.env.example`).

## Scoring Rules
- Implemented in `src/scoring_2026.py`
- Documented in `docs/SCORING_2026.md`

## Docs
- `docs/PRINCIPLES.md`
- `docs/WORKFLOW.md`
- `docs/DATA_SOURCES.md`
- `docs/MODELING_ASSUMPTIONS.md`
- `docs/TROUBLESHOOTING.md`

## Known limitations
- Overtakes can be unavailable on some feeds; scoring sets component to `0` and surfaces `missing_components`.
- Fantasy API endpoint shapes may change; parser is best effort and falls back to cached/synthetic pools.
- FastF1 can lag during live weekends depending on source availability.
