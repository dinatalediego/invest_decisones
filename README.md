# invest_decisones

Quantitative sports-market research project focused on one question:

> **Is there a statistically exploitable inefficiency that survives out-of-sample testing, execution frictions, costs, and risk?**

This repository starts as a **paper-trading / research system only**. It does not place bets automatically and does not assume that a profitable strategy exists.

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
- `configs/odds_snapshot_policy.yml` — point-in-time odds capture contract.
- `configs/experiment_registry.yml` — experiment preregistration template.
- `docs/research_contract.md` — approved research/data contract.
- `docs/DATA_SOURCE_DECISION_MEMO.md` — source decision template.

## First proof

Before adding advanced models or paid data, demonstrate:

**Elo → Poisson → probabilities → calibration → odds → de-vig → EV → decision time → backtest → CLV → uncertainty.**

## Status

Foundation / Phase 0. No paid data source has been approved.
