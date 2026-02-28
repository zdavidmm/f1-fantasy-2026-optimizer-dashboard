# Data Sources

## Fantasy API (`fantasy-api.formula1.com`)
- Intended for driver/constructor IDs, prices, and event structures.
- Endpoints are configurable in `config.yaml`.
- Parser is resilient: best-effort field extraction + schema validation.
- Raw payloads are stored in `public/data/raw/` for debugging.
- Fallback path: cached payloads or synthetic pool if endpoint unavailable.

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
