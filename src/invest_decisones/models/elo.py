"""Leakage-safe pre-match Elo baseline and out-of-sample evaluation."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from itertools import groupby
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EloConfig:
    initial_rating: float = 1500.0
    k_factor: float = 20.0
    home_advantage_points: float = 75.0
    rating_scale: float = 400.0
    draw_prior: float = 0.25
    draw_prior_strength: float = 50.0


def _float(row: dict[str, str], field: str) -> float | None:
    value = (row.get(field) or "").strip()
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _prob_home_conditional(
    home_rating: float,
    away_rating: float,
    config: EloConfig,
) -> float:
    diff = home_rating + config.home_advantage_points - away_rating
    return 1.0 / (1.0 + 10.0 ** (-diff / config.rating_scale))


def _devig_decimal(
    odds: tuple[float, float, float],
) -> tuple[float, float, float]:
    implied = [1.0 / odd for odd in odds]
    total = sum(implied)
    return tuple(value / total for value in implied)  # type: ignore[return-value]


def _metrics(
    records: list[dict[str, Any]],
    prefix: str = "p_",
) -> dict[str, float | int | None]:
    if not records:
        return {
            "n": 0,
            "accuracy": None,
            "brier": None,
            "log_loss": None,
        }

    brier = 0.0
    log_loss = 0.0
    correct = 0
    labels = ("H", "D", "A")

    for record in records:
        probs = [float(record[f"{prefix}{label.lower()}"]) for label in labels]
        actual = record["result"]
        predicted = labels[max(range(3), key=lambda idx: probs[idx])]
        correct += int(predicted == actual)
        brier += sum(
            (prob - float(label == actual)) ** 2
            for prob, label in zip(probs, labels)
        )
        actual_prob = max(
            min(probs[labels.index(actual)], 1.0 - 1e-15),
            1e-15,
        )
        log_loss -= math.log(actual_prob)

    n = len(records)
    return {
        "n": n,
        "accuracy": correct / n,
        "brier": brier / n,
        "log_loss": log_loss / n,
    }


def _top_label_ece(
    records: list[dict[str, Any]],
    bins: int = 10,
) -> float | None:
    if not records:
        return None

    bucketed: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    labels = ("H", "D", "A")

    for record in records:
        probs = [float(record[f"p_{label.lower()}"]) for label in labels]
        idx = max(range(3), key=lambda i: probs[i])
        confidence = probs[idx]
        bucket = min(int(confidence * bins), bins - 1)
        bucketed[bucket].append(
            (confidence, int(labels[idx] == record["result"]))
        )

    total = len(records)
    ece = 0.0
    for bucket in bucketed:
        if not bucket:
            continue
        confidence = sum(item[0] for item in bucket) / len(bucket)
        accuracy = sum(item[1] for item in bucket) / len(bucket)
        ece += len(bucket) / total * abs(accuracy - confidence)

    return ece


def _market_probs(
    row: dict[str, str],
) -> tuple[tuple[float, float, float], str] | None:
    groups = (
        ("average_close", ("AvgCH", "AvgCD", "AvgCA")),
        ("average_pre", ("AvgH", "AvgD", "AvgA")),
    )

    for name, fields in groups:
        values = tuple(_float(row, field) for field in fields)
        if all(value is not None and value > 1.0 for value in values):
            return _devig_decimal(values), name  # type: ignore[arg-type]

    return None


def run_elo_baseline(
    matches: list[dict[str, str]],
    test_season: str,
    config: EloConfig | None = None,
) -> dict[str, Any]:
    """Run daily-batched chronological Elo with no same-day outcome leakage.

    All probabilities for a calendar date are computed from the state available
    before any result on that date is applied. This is deliberately conservative:
    it prevents simultaneous or unknown-kickoff-order matches from leaking outcomes.
    """
    config = config or EloConfig()

    ordered = sorted(
        matches,
        key=lambda row: (
            row["date"],
            row.get("time", ""),
            row["event_id"],
        ),
    )
    if not ordered:
        raise ValueError("No matches supplied")

    test_dates = [
        row["date"]
        for row in ordered
        if row["season"] == test_season
    ]
    if not test_dates:
        raise ValueError(f"No rows for test season {test_season}")

    first_test_date = min(test_dates)
    train_rows = [
        row
        for row in ordered
        if row["date"] < first_test_date
    ]
    if not train_rows:
        raise ValueError("Test season has no earlier training history")

    counts = {"H": 0, "D": 0, "A": 0}
    for row in train_rows:
        counts[row["result"]] += 1

    train_n = sum(counts.values())
    prior_probs = {
        label: counts[label] / train_n
        for label in counts
    }

    ratings: dict[str, float] = {}
    historical_matches = 0
    historical_draws = 0
    predictions: list[dict[str, Any]] = []
    market_records: list[dict[str, Any]] = []

    for match_date, date_rows_iter in groupby(
        ordered,
        key=lambda row: row["date"],
    ):
        date_rows = list(date_rows_iter)

        draw_prob = (
            historical_draws
            + config.draw_prior_strength * config.draw_prior
        ) / (
            historical_matches
            + config.draw_prior_strength
        )
        draw_prob = min(max(draw_prob, 0.10), 0.40)

        pending_updates: list[
            tuple[str, str, float, float, float, str]
        ] = []

        for row in date_rows:
            home = row["home_team"]
            away = row["away_team"]

            home_rating = ratings.get(
                home,
                config.initial_rating,
            )
            away_rating = ratings.get(
                away,
                config.initial_rating,
            )

            p_home_cond = _prob_home_conditional(
                home_rating,
                away_rating,
                config,
            )
            p_home = (1.0 - draw_prob) * p_home_cond
            p_away = (1.0 - draw_prob) * (1.0 - p_home_cond)

            if row["season"] == test_season:
                record: dict[str, Any] = {
                    "event_id": row["event_id"],
                    "date": match_date,
                    "home_team": home,
                    "away_team": away,
                    "result": row["result"],
                    "home_rating_pre": home_rating,
                    "away_rating_pre": away_rating,
                    "p_h": p_home,
                    "p_d": draw_prob,
                    "p_a": p_away,
                    "prior_h": prior_probs["H"],
                    "prior_d": prior_probs["D"],
                    "prior_a": prior_probs["A"],
                }
                predictions.append(record)

                market = _market_probs(row)
                if market is not None:
                    probs, market_group = market
                    market_records.append(
                        {
                            "event_id": row["event_id"],
                            "result": row["result"],
                            "m_h": probs[0],
                            "m_d": probs[1],
                            "m_a": probs[2],
                            "market_group": market_group,
                        }
                    )

            pending_updates.append(
                (
                    home,
                    away,
                    home_rating,
                    away_rating,
                    p_home_cond,
                    row["result"],
                )
            )

        # Apply the entire day's results only after all daily predictions exist.
        rating_deltas: dict[str, float] = {}
        day_draws = 0

        for (
            home,
            away,
            home_rating,
            away_rating,
            p_home_cond,
            result,
        ) in pending_updates:
            actual_score = {
                "H": 1.0,
                "D": 0.5,
                "A": 0.0,
            }[result]

            delta = config.k_factor * (
                actual_score - p_home_cond
            )

            rating_deltas[home] = (
                rating_deltas.get(home, 0.0) + delta
            )
            rating_deltas[away] = (
                rating_deltas.get(away, 0.0) - delta
            )
            day_draws += int(result == "D")

        # A team normally plays once per day; additive deltas also make this safe
        # for duplicated/special schedules without sequential within-day leakage.
        for team, delta in rating_deltas.items():
            ratings[team] = ratings.get(
                team,
                config.initial_rating,
            ) + delta

        historical_matches += len(date_rows)
        historical_draws += day_draws

    elo_metrics = _metrics(
        predictions,
        prefix="p_",
    )
    elo_metrics["ece_top_label"] = _top_label_ece(
        predictions
    )

    prior_records = [
        {
            "result": record["result"],
            "q_h": record["prior_h"],
            "q_d": record["prior_d"],
            "q_a": record["prior_a"],
        }
        for record in predictions
    ]
    prior_metrics = _metrics(
        prior_records,
        prefix="q_",
    )
    market_metrics = _metrics(
        market_records,
        prefix="m_",
    )

    market_groups: dict[str, int] = {}
    for record in market_records:
        market_groups[record["market_group"]] = (
            market_groups.get(
                record["market_group"],
                0,
            )
            + 1
        )

    return {
        "model": "elo_baseline_v0.1",
        "status": "baseline_challenger",
        "temporal_update_policy": "daily_batch",
        "test_season": test_season,
        "first_test_date": first_test_date,
        "train_matches": len(train_rows),
        "test_matches": len(predictions),
        "config": asdict(config),
        "elo": elo_metrics,
        "train_only_constant_prior": {
            "probabilities": prior_probs,
            "metrics": prior_metrics,
        },
        "market_benchmark": {
            "method": "proportional_devig",
            "preferred": "average_close",
            "fallback": "average_pre",
            "groups_used": market_groups,
            "metrics": market_metrics,
        },
        "final_ratings": dict(
            sorted(
                ratings.items(),
                key=lambda item: item[1],
                reverse=True,
            )
        ),
        "interpretation_guardrail": (
            "This is a fixed-parameter research baseline. "
            "It is not evidence of a profitable betting edge."
        ),
    }


def write_elo_result(
    result: dict[str, Any],
    path: str | Path,
) -> None:
    Path(path).write_text(
        json.dumps(result, indent=2) + "\n",
        encoding="utf-8",
    )
