# DATA SOURCE DECISION MEMO

## Decision metadata

- Date:
- Owner:
- Status: draft / approved / rejected
- Research question unlocked:
- Budget requested:
- Expected duration:

## 1. Missing information

Describe the exact datum or temporal property missing from the current free-first stack.

Do not use generic statements such as "better data".

Examples of acceptable gaps:

- no intraday odds at T-6h;
- no historically valid injury availability timestamp;
- insufficient xG coverage for a preregistered league/time period;
- no exchange liquidity data required to estimate executable edge.

## 2. Free alternatives evaluated

| Source | What it provides | Empirical test performed | Limitation |
|---|---|---|---|
| | | | |

## 3. Candidate source

- Provider:
- Product/API:
- URL:
- Data fields:
- Historical depth:
- Timestamp quality:
- Competitions/markets:
- Rate limits:
- Terms/license:
- Redistribution restrictions:

## 4. Cost

- One-off cost:
- Monthly cost:
- Minimum commitment:
- Expected total project cost:
- Currency:
- Cancellation method:

## 5. Scientific value

State which hypothesis, robustness check, execution assumption or validation becomes possible.

## 6. Incremental-value test

Define what will be compared before purchase:

```text
FREE STACK RESULT
vs
FREE STACK + CANDIDATE DATA
```

Specify the metric or validity improvement required to justify continued spend.

## 7. Exit criterion

The source must be cancelled/stopped when:

- the required historical window has been acquired; or
- the preregistered experiment is complete; or
- the incremental scientific value is not demonstrated; or
- a scientifically sufficient free replacement exists.

## 8. Decision

- [ ] APPROVE
- [ ] REJECT
- [ ] DEFER

Reason:

---

# DATA SOURCE DECISION MATRIX

Maintain the Phase-0 comparison using:

**SOURCE × VARIABLE × LEAGUE × SEASON × TIMESTAMP QUALITY × COST × LICENSE**

For every source selected, record empirical checks for:

- number of matches;
- minimum and maximum date;
- missingness;
- duplicates;
- identifier consistency;
- odds availability;
- timestamp availability;
- historical continuity;
- source-specific quality warnings.

## Required architecture outputs

1. **FREE-FIRST DATA STACK**
2. **PAID ESCALATION PATH**

The paid escalation path is documentation, not authorization to purchase.
