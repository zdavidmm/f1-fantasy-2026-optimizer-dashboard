# Data Sources

## Official Fantasy Feeds (`fantasy.formula1.com/feeds`)
- Primary live source for driver/constructor prices and game-day schedule.
- Uses `schedule/raceday_en.json` to detect current game day and `drivers/{gameday}_en.json` for prices.
- Raw payloads are stored in `public/data/raw/` for debugging.

## Legacy Fantasy API (`fantasy-api.formula1.com`)
- Secondary/best-effort fallback if feed parsing fails.
- Endpoints remain configurable in `config.yaml`.

## FastF1
- Pulls event schedule and session results (Q/S/R as available).
- Produces qualifying/race form and reliability proxies.
- Uses cache directory (`fastf1_cache/`) to reduce network overhead.

## OpenF1 (Optional)
- Enabled only when `OPENF1_API_KEY` is present.
- Without key, pipeline continues and labels OpenF1 as skipped.

## Freshness and Labels
`public/data/latest.json` includes per-source status and run timestamp.

## Limitations
- Overtakes may be unavailable from free endpoints and are then marked missing.
- Some Fantasy API endpoints may change shape; parser handles best effort but may degrade.
