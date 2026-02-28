# Weekly Workflow

1. Pipeline runs daily at 06:00 UTC and on every push to `main`.
2. Providers fetch live data from Fantasy API, FastF1, and optional OpenF1.
3. Scoring + expected points signals are updated.
4. Optimizer computes Safe/Balanced/High-variance lineups.
5. Transfer plan compares previous Balanced lineup to current recommendation and applies -10 per extra transfer over free transfers.
6. Site is rebuilt and deployed to GitHub Pages.

## Transfer Discipline Rule of Thumb
- Prefer <= free transfers unless objective-adjusted gain is materially above transfer hit.
- Batch structural changes with Wildcard windows.
