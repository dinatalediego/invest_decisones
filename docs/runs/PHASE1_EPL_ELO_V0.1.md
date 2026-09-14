# Phase 1 Evidence — EPL Football-Data v0.1 + Elo Baseline

**Run date:** 2026-09-14  
**Status:** ACCEPTED AS REPRODUCIBLE BASELINE  
**GitHub Actions run:** 34861642251  
**Evidence artifact:** phase1-dataset-elo-evidence  
**Real-money status:** PROHIBITED

## Executive result

Phase 1 closes the first end-to-end quantitative research slice:

```text
Football-Data.co.uk
        ↓
immutable RAW + SHA-256
        ↓
canonical EPL dataset
        ↓
versioned manifest
        ↓
quality / missingness / odds audit
        ↓
point-in-time-safe Elo baseline
        ↓
out-of-sample 2025/26
        ↓
constant-prior benchmark
        ↓
de-vigged closing-market benchmark
```

The pipeline is reproducible and the baseline behaves scientifically as expected:

- Elo materially improves on a naive train-only constant prior.
- Elo does **not** beat the de-vigged closing market on the 2025/26 test season.
- Therefore Phase 1 establishes a useful predictive baseline but provides **no evidence yet of a betting edge**.

---

## Dataset identity

**Dataset version:** `fd_epl_v0.1_504af51e6c95`

The version identity is based on:

- canonical schema version;
- season;
- league;
- immutable RAW SHA-256 content hashes.

Retrieval timestamp is deliberately excluded from version identity, so identical bytes map to the same dataset version.

### Direct-source provenance

| Season | Football-Data source | RAW SHA-256 |
|---|---|---|
| 2022/23 | `mmz4281/2223/E0.csv` | `8442792d3b614c94ea3cf381bd2736805889cc1713169035368fff19c3d02380` |
| 2023/24 | `mmz4281/2324/E0.csv` | `b2e057b0ed959f198b0f63d2391c01239f3608e6de5db68edab3f88e04d07ff3` |
| 2024/25 | `mmz4281/2425/E0.csv` | `d0c8ce4a96d886cf60cf101f570f4a3893844226f91c7bd769eb568c49edbfa4` |
| 2025/26 | `mmz4281/2526/E0.csv` | `3e3a8352f9ada6789c508d6ca184424421fed56a30400904a4a327c583407e62` |

---

## Coverage and core missingness

| Season | Rows | Completed | Teams | Date range | Source columns | Core invalid rows |
|---|---:|---:|---:|---|---:|---:|
| 2022/23 | 380 | 380 | 20 | 2022-08-05 → 2023-05-28 | 106 | 0 |
| 2023/24 | 380 | 380 | 20 | 2023-08-11 → 2024-05-19 | 106 | 0 |
| 2024/25 | 380 | 380 | 20 | 2024-08-16 → 2025-05-25 | 120 | 0 |
| 2025/26 | 380 | 380 | 20 | 2025-08-15 → 2026-05-24 | 132 | 0 |
| **Total** | **1,520** | **1,520** | — | — | — | **0** |

For all four seasons, the fields required for the canonical match record have zero missing values:

- Date
- HomeTeam
- AwayTeam
- FTHG
- FTAG
- FTR

There are also **zero duplicate canonical event IDs**.

### Schema drift finding

The source expands from 106 → 120 → 132 columns over the study window.

Decision:

- never bind the canonical model to the complete vendor schema;
- explicitly select contractual fields;
- preserve RAW unchanged;
- profile extra/missing columns per source version.

---

## Real 1X2 odds coverage

| Season | B365 pre | Avg pre | Max pre | Pinnacle pre | B365 close | Avg close | Max close | Pinnacle close |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2022/23 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2023/24 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2024/25 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2025/26 | 100% | 100% | 100% | **55.3%** | 100% | 100% | 100% | **55.3%** |

Aggregate coverage:

- B365 pre/close: **1,520 / 1,520**
- Avg pre/close: **1,520 / 1,520**
- Max pre/close: **1,520 / 1,520**
- Pinnacle pre/close: **1,350 / 1,520 = 88.8%**

The 2025/26 Pinnacle fields contain 170 missing match rows and therefore are not suitable as the universal CLV benchmark for this dataset version.

### Mean observed 1X2 overround

| Season | Avg pre | Avg close | Pinnacle pre | Pinnacle close |
|---|---:|---:|---:|---:|
| 2022/23 | 4.07% | 3.90% | 2.65% | 2.46% |
| 2023/24 | 4.14% | 3.97% | 3.46% | 2.93% |
| 2024/25 | 4.49% | 4.19% | 3.60% | 2.99% |
| 2025/26 | 5.81% | 5.67% | 3.54%* | 2.95%* |

\* Pinnacle 2025/26 values use only the 210 matches with complete Pinnacle triples.

Do not interpret the rise in average-bookmaker overround mechanically as a time trend in house margin: the composition of books represented by the aggregate can change.

### Important execution warning for `Max*`

`MaxH/MaxD/MaxA` and closing equivalents represent outcome-wise maxima across books. They are **not** a single bookmaker quote and must not be treated as automatically simultaneous or executable.

They may even imply very low or negative aggregate overround because they represent synthetic line shopping.

Any future use of `Max*` requires an explicit line-shopping / availability policy.

---

## Out-of-sample design

Training history:

- 2022/23
- 2023/24
- 2024/25

Training matches: **1,140**

Untouched evaluation season:

- **2025/26**

Test matches: **380**

Elo hyperparameters were fixed before evaluation:

- initial rating = 1500
- K = 20
- home advantage = 75 Elo points
- rating scale = 400
- draw prior = 0.25
- draw prior strength = 50

### Temporal policy

`temporal_update_policy = daily_batch`

All probabilities for a calendar date are computed before results from that date update ratings or the rolling draw rate.

This conservative rule prevents:

- simultaneous-match leakage;
- unknown kickoff-order leakage;
- same-day outcome leakage.

---

## Baseline results — 2025/26 OOS

| Model | Accuracy | Multiclass Brier ↓ | Log Loss ↓ |
|---|---:|---:|---:|
| Train-only constant prior | 42.63% | 0.6563 | 1.0845 |
| **Elo v0.1** | **48.68%** | **0.6156** | **1.0260** |
| De-vigged Avg closing market | **49.47%** | **0.6077** | **1.0118** |

Elo top-label ECE: **0.0424**

### Incremental value

Relative to the naive train-only prior:

- Elo reduces Brier by approximately **6.20%**.
- Elo reduces Log Loss by approximately **5.39%**.

Relative to Elo:

- the closing market has approximately **1.28% lower Brier**;
- the closing market has approximately **1.39% lower Log Loss**.

Interpretation:

> Elo learns meaningful signal, but the closing market remains the stronger probabilistic benchmark in this first experiment.

That is a successful baseline result. The research system is behaving skeptically rather than manufacturing profitability.

---

## Quality gates executed

GitHub Actions run 34861642251 completed successfully.

Automated tests cover:

1. Football-Data URL construction;
2. invalid season rejection;
3. stable SHA-256 hashing;
4. missingness and exact duplicate profiling;
5. dataset version stability across retrieval timestamps;
6. deterministic multi-source version identity;
7. pre-match Elo prediction ordering;
8. separation of market odds from Elo features;
9. same-day batch updates preventing outcome leakage.

The evidence bundle contained:

- canonical versioned CSV;
- dataset manifest;
- quality report;
- Elo baseline JSON;
- scientific Markdown report.

The external dataset itself is not committed to Git.

---

## Accepted decisions

### Dataset

**ACCEPT `fd_epl_v0.1_504af51e6c95` as the first verified research dataset identity.**

### Elo

**ACCEPT `elo_baseline_v0.1` as baseline challenger.**

It is a benchmark, not a production betting model.

### Market

Use de-vigged `AvgCH/AvgCD/AvgCA` as the current evaluation benchmark where complete.

Do not use closing odds as features for pre-close predictions.

### Pinnacle

Do not make Pinnacle the universal CLV reference in v0.1 because 2025/26 coverage is only 55.3% and the source registry already records the provider's recent-data warning.

### Money

**NO BET remains the only live-money decision.**

No real-money strategy has been approved.

---

## Next scientific gate

Phase 2 should now compare Elo against a goals-based baseline without expanding scope excessively:

1. independent Poisson;
2. derive 1X2 / O-U 2.5 / BTTS probabilities;
3. evaluate calibration and OOS metrics;
4. add Dixon-Coles only after independent Poisson is reproducible;
5. keep the closing market as benchmark, not a training leak.

The promotion criterion is not “higher accuracy”.

A new model must demonstrate reproducible improvement in probability quality, calibration and temporal robustness before any EV/backtesting claim is entertained.
