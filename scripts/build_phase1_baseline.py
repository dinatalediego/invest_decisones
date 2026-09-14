#!/usr/bin/env python3
"""Build the first versioned Football-Data dataset and Elo baseline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from invest_decisones.data.football_data import download_dataset
from invest_decisones.data.versioned_dataset import (
    SourceInput,
    build_versioned_dataset,
    load_canonical_matches,
)
from invest_decisones.models.elo import (
    EloConfig,
    run_elo_baseline,
    write_elo_result,
)


def _season_spec(value: str) -> tuple[str, str]:
    try:
        season, league = value.split(":", 1)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "Use SEASON:LEAGUE, e.g. 2526:E0"
        ) from exc

    if len(season) != 4 or not season.isdigit() or not league:
        raise argparse.ArgumentTypeError(
            "Use SEASON:LEAGUE, e.g. 2526:E0"
        )

    return season, league


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--season",
        action="append",
        type=_season_spec,
        required=True,
        help="Repeatable SEASON:LEAGUE spec",
    )
    parser.add_argument(
        "--test-season",
        required=True,
        help="Out-of-sample season token",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/generated/phase1",
    )
    parser.add_argument(
        "--raw-dir",
        default="data/raw/football_data",
    )

    return parser.parse_args()


def _fmt(value: object, digits: int = 4) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def _write_markdown(
    output_dir: Path,
    quality: dict,
    elo: dict,
    version: str,
) -> None:
    rows = []

    for source in quality["sources"]:
        avg_close = source["odds_groups"]["average_close"]
        avg_pre = source["odds_groups"]["average_pre"]

        rows.append(
            "| {season} | {matches} | {teams} | {dmin} | {dmax} | {pre:.1%} | {close:.1%} |".format(
                season=source["season"],
                matches=source["completed_rows"],
                teams=source["team_count"],
                dmin=source["date_min"],
                dmax=source["date_max"],
                pre=avg_pre["coverage_completed"],
                close=avg_close["coverage_completed"],
            )
        )

    market = elo["market_benchmark"]["metrics"]

    report = f"""# Phase 1 — Versioned Dataset + Elo Baseline

## Dataset

- Version: {version}
- Canonical matches: **{quality['row_count']}**
- Duplicate event IDs dropped: **{quality['cross_source_duplicate_event_ids_dropped']}**
- Provider: Football-Data.co.uk

| Season | Matches | Teams | Min date | Max date | Avg pre odds | Avg closing odds |
|---|---:|---:|---|---|---:|---:|
{chr(10).join(rows)}

## Out-of-sample protocol

- Test season: **{elo['test_season']}**
- Training matches before test: **{elo['train_matches']}**
- Test matches: **{elo['test_matches']}**
- Hyperparameters: fixed before observing test outcomes
- Prediction order: rating/probability first, match-result update second

## Elo baseline

- Accuracy: **{_fmt(elo['elo']['accuracy'])}**
- Multiclass Brier: **{_fmt(elo['elo']['brier'])}**
- Log loss: **{_fmt(elo['elo']['log_loss'])}**
- Top-label ECE: **{_fmt(elo['elo']['ece_top_label'])}**

## Train-only constant-prior benchmark

- Brier: **{_fmt(elo['train_only_constant_prior']['metrics']['brier'])}**
- Log loss: **{_fmt(elo['train_only_constant_prior']['metrics']['log_loss'])}**

## Market benchmark

Uses proportional de-vig on AvgCH/AvgCD/AvgCA when present,
otherwise AvgH/AvgD/AvgA.

- Covered test matches: **{market['n']}**
- Brier: **{_fmt(market['brier'])}**
- Log loss: **{_fmt(market['log_loss'])}**
- Odds groups used: {json.dumps(elo['market_benchmark']['groups_used'], sort_keys=True)}

## Scientific interpretation

This run establishes the first reproducible baseline.
It does **not** claim a betting edge.

The next question is whether later models improve probability quality
and calibration out of sample, and eventually whether any improvement
survives market comparison and execution costs.
"""

    (
        output_dir / "PHASE1_BASELINE_REPORT.md"
    ).write_text(
        report,
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    source_inputs: list[SourceInput] = []

    for season, league in args.season:
        artifact = download_dataset(
            season=season,
            league=league,
            output_root=args.raw_dir,
        )

        source_inputs.append(
            SourceInput(
                season=season,
                league=league,
                source_url=artifact.source_url,
                sha256=artifact.sha256,
                raw_path=artifact.raw_path,
                retrieved_at=artifact.retrieved_at,
            )
        )

    dataset = build_versioned_dataset(
        source_inputs,
        output_dir=output_dir,
    )

    matches = load_canonical_matches(
        dataset.dataset_path
    )

    result = run_elo_baseline(
        matches,
        test_season=args.test_season,
        config=EloConfig(),
    )

    result["dataset_version"] = (
        dataset.dataset_version
    )

    elo_path = output_dir / "elo_baseline.json"

    write_elo_result(
        result,
        elo_path,
    )

    quality = json.loads(
        Path(
            dataset.quality_report_path
        ).read_text(
            encoding="utf-8"
        )
    )

    _write_markdown(
        output_dir,
        quality,
        result,
        dataset.dataset_version,
    )

    summary = {
        "dataset_version": dataset.dataset_version,
        "rows": dataset.row_count,
        "test_season": args.test_season,
        "elo": result["elo"],
        "market_benchmark": result[
            "market_benchmark"
        ],
        "artifacts": {
            "manifest": dataset.manifest_path,
            "quality": dataset.quality_report_path,
            "elo": elo_path.as_posix(),
            "report": (
                output_dir
                / "PHASE1_BASELINE_REPORT.md"
            ).as_posix(),
        },
    }

    print(
        "PHASE1_SUMMARY_JSON="
        + json.dumps(
            summary,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
