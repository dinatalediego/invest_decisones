# invest_decisones

Quantitative sports-market research project focused on one question:

> **Is there a statistically exploitable inefficiency that survives out-of-sample testing, execution frictions, costs, and risk?**

This repository is a **paper-trading / research system only**. It does not place bets automatically and does not assume that a profitable strategy exists.

## Current operating principles

1. **Rigor > reproducibility > risk management > potential return > model complexity.**
2. **FREE-FIRST data policy:** initial acquisition budget is USD 0.
3. **Point-in-time validity:** a feature is usable only when `available_at <= prediction_time`.
4. **RAW is immutable:** source evidence is preserved before normalization.
5. **Market realism:** distinguish model edge from executable edge.
6. **NO BET is a valid decision.**
7. **Negative experiments are retained.**
8. **No real-money betting during the research program.**

## Research path

```text
DATA
  ↓
ENTITY RESOLUTION
  ↓
POINT-IN-TIME DATASET
  ↓
FEATURE ENGINEERING
  ↓
MODEL
  ↓
PROBABILITIES
  ↓
CALIBRATION
  ↓
MARKET ODDS + DE-VIG
  ↓
MODEL EDGE
  ↓
EXECUTION MODEL
  ↓
EXECUTABLE EDGE
  ↓
NO BET / PAPER BET
  ↓
BACKTEST + CLV + UNCERTAINTY
```

## Free-first stack

- Football-Data.co.uk — historical results, match statistics and odds.
- StatsBomb Open Data — event data, lineups and selected 360 data.
- football-data.org — fixtures, schedules and league tables.
- API-Football free tier — auxiliary recent data where useful.
- Future odds snapshots captured by this project when legally and technically allowed.

Paid data is not a dependency of the MVP. Any paid source requires a **Data Purchase Decision Memo**.

## Repository governance

- `configs/data_sources.yml` — source registry.
- `configs/datasets/epl_football_data_v0.1.yml` — first dataset/model contract.
- `configs/odds_snapshot_policy.yml` — point-in-time odds capture contract.
- `configs/experiment_registry.yml` — experiment preregistration template.
- `docs/research_contract.md` — approved research/data contract.
- `docs/DATA_SOURCE_DECISION_MEMO.md` — source decision template.
- `docs/runs/PHASE1_EPL_ELO_V0.1.md` — verified first experiment.

## Phase 1 — verified

The first complete vertical slice is reproducible:

**Football-Data → immutable RAW → SHA-256 → versioned EPL dataset → quality audit → Elo → OOS evaluation → market benchmark.**

Accepted dataset identity:

`fd_epl_v0.1_504af51e6c95`

Coverage:

- 4 complete EPL seasons;
- 1,520 canonical matches;
- 1,140 historical training matches;
- 380 out-of-sample matches in 2025/26;
- 100% coverage for Avg 1X2 pre and closing odds;
- zero invalid canonical rows.

2025/26 out-of-sample:

| Benchmark | Brier ↓ | Log Loss ↓ |
|---|---:|---:|
| Constant train prior | 0.6563 | 1.0845 |
| Elo v0.1 | 0.6156 | 1.0260 |
| De-vigged Avg closing market | **0.6077** | **1.0118** |

Conclusion:

> Elo contains useful predictive signal and beats the naive prior, but it does not beat the closing market. No betting edge is claimed.

## Reproduce Phase 1

```bash
python -m pip install -e .

python -m unittest discover -s tests -p "test_*.py" -v

python scripts/build_phase1_baseline.py \
  --season 2223:E0 \
  --season 2324:E0 \
  --season 2425:E0 \
  --season 2526:E0 \
  --test-season 2526 \
  --output-dir reports/generated/phase1
```

Generated external data and RAW files remain outside Git.

## Next gate

Build independent Poisson first, then evaluate whether Dixon-Coles is justified.

The broader research path remains:

**Elo → Poisson → calibration → odds → de-vig → EV → decision time → backtest → CLV → uncertainty.**

## Status

**Phase 1 closed / Phase 2 ready.**

No paid data source and no real-money betting have been approved.
