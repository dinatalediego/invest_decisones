#!/usr/bin/env python3
"""Download one Football-Data league/season into immutable RAW storage."""

from __future__ import annotations

import argparse
import json

from src.invest_decisones.data.football_data import artifact_as_dict, download_dataset


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--season", required=True, help="Football-Data season token, e.g. 2526")
    parser.add_argument("--league", required=True, help="League code, e.g. E0")
    parser.add_argument(
        "--output-root",
        default="data/raw/football_data",
        help="Local immutable RAW root",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = download_dataset(
        season=args.season,
        league=args.league,
        output_root=args.output_root,
    )
    print(json.dumps(artifact_as_dict(artifact), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
