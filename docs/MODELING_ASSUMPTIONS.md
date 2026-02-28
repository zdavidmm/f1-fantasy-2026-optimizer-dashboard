# Expected Points Model (Transparent)

For each asset, expected points for the next event are computed as:

- Driver:
  - `E_quali = w_quali * qualifying_form`
  - `E_sprint = w_sprint * sprint_form`
  - `E_race = w_race * race_form`
- Constructor:
  - same structure plus `E_pitstop = w_pitstop * pitstop_proxy`

Weights are configured in `config.yaml` (`model_weights`).

## Secondary Objectives
- Downside risk proxy from DNF risk values.
- Price growth proxy from form trends.

Strategy tuning:
- Safe: high risk penalty, low growth weight.
- Balanced: medium risk and growth.
- High-variance: low risk penalty, high growth/upside emphasis.

## Determinism
Solver is deterministic by default. If future stochastic extensions are added, `--seed` should be exposed and documented.
