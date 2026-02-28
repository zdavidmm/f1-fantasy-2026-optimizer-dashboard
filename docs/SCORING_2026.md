# Official F1 Fantasy 2026 Scoring Rules (Encoded)

This repository encodes the scoring logic in `src/scoring_2026.py`.

## Qualifying
- Driver result points: P1..P10 = 10..1, else 0.
- Driver penalty: `-5` for NC/DSQ/no time set.
- Constructor = sum of two drivers qualifying points + Q2/Q3 bonus ladder:
  - neither Q2: `-1`
  - one Q2: `+1`
  - both Q2: `+3`
  - one Q3: `+5`
  - both Q3: `+10`
- Constructor DSQ penalty: `-5` per DSQ driver.

## Sprint
- Driver:
  - positions gained: `+1` each
  - positions lost: `-1` each
  - overtakes: `+1` each (if missing, set 0 and mark missing)
  - fastest lap: `+5`
  - sprint result P1..P8 = `8..1`, else 0
  - DNF/DSQ/NC: `-10`
- Constructor = sum of two driver sprint scores; DSQ `-10` per DSQ driver.

## Race
- Driver:
  - positions gained/lost: `+1/-1`
  - overtakes: `+1` each (if missing, set 0 and mark missing)
  - fastest lap: `+10`
  - DOTD: `+10`
  - race result P1..P10 = `25,18,15,12,10,8,6,4,2,1`
  - DNF/DSQ/NC: `-20`
- Constructor:
  - sum of two drivers race points excluding DOTD
  - pitstop points:
    - `>3.0s` => 0
    - `2.50-2.99` => 2
    - `2.20-2.49` => 5
    - `2.00-2.19` => 10
    - `<2.0` => 20
  - fastest pitstop: `+5`
  - DSQ: `-20` per DSQ driver
  - new pitstop world record: `+15` (threshold configurable in `config.yaml`)

## Team Management
- Additional transfers beyond free transfers: `-10` each.

## Missing Data Policy
If a component (for example overtakes) is unavailable:
- score contribution defaults to `0`
- component name is included in `missing_components`

## Example
If a race driver gains 3 positions, has no overtake data, gets fastest lap, finishes P4, no DOTD, status OK:
- delta: +3
- overtakes: +0 (missing)
- FL: +10
- result: +12
- total: 25, with `missing_components: ["overtakes"]`
