# Phase 0 — Data Source Decision Memo

**Date:** 2026-09-13  
**Status:** APPROVED FOR FREE-FIRST IMPLEMENTATION  
**Initial data budget:** USD 0

## Executive decision

Use a free-first stack for the first complete research pipeline.

Primary historical source:

1. **Football-Data.co.uk** for match results, match statistics and historical bookmaker odds.

Auxiliary sources:

2. **StatsBomb Open Data** for event-level data, lineups and selected 360 data.
3. **football-data.org** for fixtures/schedules/tables where useful.
4. **API-Football free tier** only when it adds recent auxiliary information not already available in the primary source.

Do **not** purchase historical intraday odds yet.

Paid escalation candidates remain blocked:

- The Odds API historical endpoint;
- Betfair Historical Data.

The first scientific gate is to demonstrate:

**Elo → Poisson → probabilities → calibration → odds → de-vig → EV → decision time → backtest → CLV → uncertainty**

with free data.

---

## Source matrix

| Source | Main variables | Historical role | Timestamp quality | Cost now | Decision |
|---|---|---|---|---:|---|
| Football-Data.co.uk | results, stats, bookmaker odds, early/closing price fields | primary historical backbone | medium | USD 0 | SELECT |
| StatsBomb Open Data | events, lineups, selected 360 | feature/research enrichment | event-level; availability-time must be modeled separately | USD 0 | SELECT AUXILIARY |
| football-data.org | fixtures, schedules, league tables | current/fixture auxiliary | API retrieval time | USD 0 free tier | SELECT AUXILIARY |
| API-Football | fixtures, lineups, injuries, odds, stats | auxiliary recent data | API retrieval time | USD 0 free tier | CANDIDATE |
| The Odds API Historical | point-in-time bookmaker snapshots | intraday historical odds | high | paid | BLOCK |
| Betfair Historical Data | exchange prices, market changes, settlement | exchange microstructure | high | paid | BLOCK |

---

## 1. Football-Data.co.uk

### Verified strengths

Official site states that its historical files are free and provides:

- results back to 1993/94;
- long-run match statistics;
- historical betting odds;
- early/pre-closing and closing odds fields for modern seasons;
- closing home/draw/away Pinnacle fields historically for part of the archive.

The provider states that since 2019/20 two sets of odds are collected: an earlier set and a closing set.

### Critical warning

The provider explicitly warns that, since **2025-07-23**, Pinnacle's public-API odds delivery has become unreliable/stale relative to other bookmakers.

Implication:

- retain these fields;
- flag them in source quality metadata;
- do not treat Pinnacle closing odds as automatic sharp-market ground truth for recent seasons;
- validate CLV benchmarks against another market proxy before drawing strong conclusions.

### Decision

**SELECT as Phase-0 primary source.**

Scientific limitation:

The files are not a complete intraday price tape. They are sufficient for the first reproducible backtesting pipeline but not for fine-grained T-24h/T-6h/T-1h historical execution studies.

Official references:

- https://www.football-data.co.uk/data
- https://www.football-data.co.uk/downloadm.php
- https://www.football-data.co.uk/matches.php

---

## 2. StatsBomb Open Data

### Verified strengths

Open repository contains:

- competitions/seasons;
- matches;
- events;
- lineups;
- StatsBomb 360 for selected matches.

The open-data terms request attribution when research/analysis/insights are published or shared.

### Limitation

Coverage is deliberately selected rather than universal.

Event timestamps describe events inside matches; they do not by themselves establish when all derived pre-match information became historically available to a bettor/model.

### Decision

**SELECT as auxiliary research source.**

Use it to learn richer football feature engineering without making the entire betting backtest dependent on its coverage.

Official reference:

- https://github.com/hudl/open-data

---

## 3. football-data.org

### Verified free tier

Current pricing documentation lists:

- EUR 0/month;
- 12 competitions;
- fixtures;
- delayed schedules;
- league tables;
- 10 calls/minute.

### Decision

**SELECT as auxiliary API**, not the historical source of truth.

Official reference:

- https://www.football-data.org/pricing

---

## 4. API-Football

### Verified free tier

Current official site lists:

- USD 0/month;
- 100 requests/day;
- access to endpoints including fixtures, lineups, injuries, pre-match odds and statistics;
- free plan limited in historical-season depth.

### Decision

**CANDIDATE AUXILIARY.**

Only activate if a concrete field is missing from the selected free backbone.

Its quota is sufficient for targeted validation but not for careless bulk collection.

Official reference:

- https://www.api-football.com/

---

## 5. The Odds API — historical

### Verified capability

Historical endpoint provides bookmaker snapshots at a requested historical timestamp.

Documentation states:

- featured-market history from 2020-06-06;
- 10-minute snapshots initially;
- 5-minute snapshots from September 2022;
- historical endpoint available only on paid plans.

### Decision

**BLOCK UNTIL DATA PURCHASE DECISION MEMO.**

Potential future value:

- reconstruct T-24h/T-6h/T-1h/close more rigorously;
- test whether an apparent edge survives realistic decision-time prices.

Do not purchase until the free pipeline is complete and a specific temporal-data gap is demonstrated.

Official references:

- https://the-odds-api.com/historical-odds-data/
- https://the-odds-api.com/liveapi/guides/v4/

---

## 6. Betfair Historical Data

### Verified capability

Betfair documentation describes timestamped Exchange historical market/price/settlement data for purchase and backtesting.

Official documentation places modern stream-format history around 2015 onward; product documentation should be rechecked for the exact first month relevant to a planned purchase.

### Decision

**BLOCK UNTIL MICROSTRUCTURE RESEARCH IS JUSTIFIED.**

Potential future role:

- traded-price / exchange microstructure;
- liquidity-aware execution research;
- settlement and market-state reconstruction.

It is not required for the MVP.

Official references:

- https://developer.betfair.com/
- https://historicdata.betfair.com/

---

# Free-First Data Stack

```text
Football-Data.co.uk
        │
        ├───────────────┐
        ▼               ▼
historical matches   historical odds
        │               │
        └───────┬───────┘
                ▼
         immutable RAW
                │
       entity resolution
                │
       point-in-time rules
                │
          feature layer
                │
   ┌────────────┴────────────┐
   ▼                         ▼
models                  market layer
   │                         │
   └────────────┬────────────┘
                ▼
          executable EV
                │
          backtest / NO BET
                │
      CLV + uncertainty
```

StatsBomb, football-data.org and API-Football are enrichments, not hard dependencies.

---

# Paid Escalation Path

A paid source can be activated only after:

1. the free pipeline is reproducible;
2. a specific failed/limited validation identifies a missing datum;
3. that datum materially affects inference;
4. the minimum sufficient paid option is identified;
5. a purchase memo documents cost and exit criterion.

Likely first paid use case, if ever needed:

> historical intraday odds with reliable timestamps.

Not:

> "more data because more data is better."

---

# Project-owned odds snapshots

The project should build its own forward point-in-time archive as soon as a free source is legally and technically validated.

Target horizons:

- T-48h
- T-24h
- T-6h
- T-1h
- close

Required properties:

- raw response retained or hashed;
- retrieval timestamp;
- source timestamp when available;
- bookmaker identity;
- market/selection/line;
- no retrospective best-price selection;
- no silent timestamp inference.

This archive is expected to become progressively more valuable because its availability chronology is observed directly rather than reconstructed later.

---

# Phase-0 exit criteria

Phase 0 is complete when:

- source registry exists;
- source terms/limits are recorded;
- primary source can be downloaded reproducibly;
- raw checksums and retrieval times are captured;
- empirical quality checks run on at least one league/season;
- canonical IDs can be generated;
- first historical odds fields are profiled;
- a dataset version can be frozen for the first Elo/Poisson experiment.

Next phase:

**build the reproducible Football-Data ingestion + source-quality validator.**
