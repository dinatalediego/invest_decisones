# Research Contract — Data, Point-in-Time Validity and Evidence

## 32. FREE-FIRST DATA POLICY

Initial data-acquisition budget: **USD 0**.

Prioritize sources that are free, reproducible, documented and legally usable.

A paid source may be introduced only when all are true:

1. a specific information gap has been identified;
2. free sources cannot resolve it with sufficient quality;
3. the missing data materially improves scientific validity;
4. the minimum-cost sufficient paid alternative has been identified;
5. the hypothesis or validation unlocked by the purchase is documented;
6. the subscription or purchase can be stopped when no longer needed.

Before any paid acquisition, create a **DATA PURCHASE DECISION MEMO** containing:

- missing datum;
- free source evaluated;
- limitation found;
- candidate paid source;
- cost;
- coverage;
- expected scientific value;
- required duration;
- cancellation criterion.

Optimization objective:

> **Maximum scientific quality per dollar spent.**

---

## 33. POINT-IN-TIME DATA CONTRACT

Temporal observations should distinguish, where applicable:

- `event_time`;
- `observed_at`;
- `available_at`;
- `ingested_at`;
- `source_updated_at`;
- `valid_from`;
- `valid_to`.

Primary feature rule:

> **available_at <= prediction_time**

No feature may use information that was not historically available at the decision time.

Preserve when possible:

- `source`;
- `source_record_id`;
- `retrieval_timestamp`;
- `source_version`;
- `raw_hash`;
- `schema_version`.

The RAW layer is immutable.

---

## 34. ODDS CONTRACT

Every odds observation should contain when available:

- `event_id`;
- `bookmaker`;
- `venue_type` = bookmaker/exchange;
- `market`;
- `selection`;
- `line`;
- `odds_decimal`;
- `observed_at`;
- `available_at`;
- `bookmaker_updated_at`;
- `opening_flag`;
- `closing_flag`;
- `source`;
- `commission`;
- `liquidity`.

Never retrospectively select the best price observed during an entire day.

Every strategy must preregister a **BET DECISION TIME**, such as:

- T-48h;
- T-24h;
- T-6h;
- T-1h;
- close.

The backtest may only use a price that would have been observable and plausibly executable at that time.

---

## 35. EXECUTION MODEL

The backtester must distinguish:

- **MODEL EDGE**
- **EXECUTABLE EDGE**

Execution assumptions should progressively consider:

- overround;
- commission;
- slippage;
- minimum stake;
- maximum stake;
- liquidity;
- stale prices;
- line changes;
- suspended markets;
- void bets;
- pushes;
- settlement rules;
- bookmaker availability;
- retrospective line-shopping risk.

A valid outcome is:

```text
MODEL EDGE > 0
EXECUTABLE EDGE <= 0
=> NO BET
```

---

## 36. DATA SOURCE GOVERNANCE

Maintain a machine-readable registry at `configs/data_sources.yml`.

For each source record:

- provider;
- URL;
- free/paid status;
- price;
- license/terms status;
- allowed use;
- redistribution permission;
- attribution requirement;
- API limits;
- historical depth;
- competitions;
- markets;
- update frequency;
- reliability;
- known biases;
- status.

Do not automatically commit third-party datasets.

If redistribution is prohibited or unclear, version only:

- downloader;
- metadata;
- schema;
- checksums;
- transformations;
- documentation.

Secrets and API keys must live only in environment variables or secret stores.

---

## 37. ENTITY RESOLUTION

Create internal canonical IDs for:

- `team_id`;
- `competition_id`;
- `season_id`;
- `event_id`;
- `player_id` when needed.

Maintain provider-to-canonical mappings.

Do not build permanent joins solely on entity names.

---

## 38. EXPERIMENT REGISTRY

Before running a strategy experiment, preregister:

- `experiment_id`;
- date;
- hypothesis;
- dataset version;
- features;
- model;
- hyperparameters;
- competition;
- market;
- period;
- EV threshold;
- staking;
- prediction time;
- bookmaker policy;
- primary metric.

Retain negative and failed experiments.

The registry exists to control:

- data snooping;
- multiple testing;
- p-hacking;
- cherry picking.

---

## 39. UNCERTAINTY AND EVIDENCE

Do not report point estimates alone when uncertainty can be estimated.

Quantify uncertainty where appropriate for:

- ROI;
- yield;
- CLV;
- Brier Score;
- Log Loss;
- Sharpe;
- drawdown;
- model differences.

Use bootstrap or other methods that preserve relevant temporal structure.

Distinguish explicitly:

1. positive estimate;
2. suggestive evidence;
3. statistically robust evidence.

Positive historical profitability does not by itself establish edge.

---

## 40. AGGREGATE RISK

In addition to individual position sizing, consider:

- maximum exposure per bet;
- maximum exposure per match;
- maximum exposure per competition;
- maximum daily exposure;
- correlated bets;
- market concentration;
- risk of ruin.

The system may reduce stake or return **NO BET** despite positive estimated EV.

---

## 41. SOURCE LADDER

### Tier 0 — Free and reproducible

Initial candidates:

- Football-Data.co.uk;
- StatsBomb Open Data;
- football-data.org;
- API-Football free tier;
- project-owned future odds snapshots where allowed.

### Tier 1 — Free but experimental

Additional sources can be tested when their stability, methodology or licensing is less certain, but they must not become critical dependencies until validated.

### Tier 2 — Minimum cost

Only after a documented gap, consider paid data for:

- historical point-in-time odds;
- broader xG coverage;
- historical injuries;
- exchange microstructure;
- market information that cannot be reconstructed reliably for free.

The architecture must not make paid data indispensable if a free source is scientifically sufficient.

---

## 42. DATA SOURCE DECISION MEMO — EXTENSION

Phase 0 must produce a comparison matrix:

**SOURCE × VARIABLE × LEAGUE × SEASON × TIMESTAMP QUALITY × COST × LICENSE**

Do not select a source solely because its documentation claims coverage.

Empirically validate:

- match count;
- min/max dates;
- missingness;
- duplicates;
- identifier consistency;
- odds availability;
- timestamps;
- historical quality.

The memo must end with:

1. **FREE-FIRST DATA STACK**
2. **PAID ESCALATION PATH**

The paid path remains inactive until experiments justify it.

---

## Initial modeling gate

Do not buy historical intraday odds yet.

First demonstrate a reproducible pipeline using free data:

**Elo → Poisson → probabilities → calibration → odds → de-vig → EV → decision time → backtest → CLV → uncertainty.**

Only after this pipeline works should point-in-time paid market data be evaluated.

## Strategic data asset

Start collecting project-owned future odds snapshots as early as practical.

Target observation horizons:

- T-48h;
- T-24h;
- T-6h;
- T-1h;
- close.

Every snapshot must preserve provenance and retrieval timestamps. The goal is to accumulate a clean point-in-time dataset whose historical availability is known rather than inferred.
