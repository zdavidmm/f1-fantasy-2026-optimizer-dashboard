# Troubleshooting

## FastF1 failures
- Symptom: provider status `unavailable`.
- Action: confirm network and FastF1 version, clear `fastf1_cache/` if corrupted.

## Fantasy API endpoint changes
- Symptom: warnings about parse failures or empty lists.
- Action: update endpoint list in `config.yaml`, inspect `public/data/raw/` snapshots.

## OpenF1 disabled
- Symptom: `OPENF1_API_KEY not set` warning.
- Action: add key in repository secret and local `.env` (do not commit `.env`).

## GitHub Pages deployment not visible
- Ensure repository Pages source is set to **GitHub Actions**.
- Check Actions run logs for `upload-pages-artifact` and `deploy-pages` success.

## Missing overtake data
- This is expected on some weekends/sources.
- Scoring sets overtake contribution to 0 and marks `missing_components`.
