"""Versioned Football-Data dataset construction and quality profiling."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

CANONICAL_SCHEMA_VERSION = 1

ODDS_GROUPS: dict[str, tuple[str, str, str]] = {
    "b365_pre": ("B365H", "B365D", "B365A"),
    "average_pre": ("AvgH", "AvgD", "AvgA"),
    "maximum_pre": ("MaxH", "MaxD", "MaxA"),
    "pinnacle_pre": ("PSH", "PSD", "PSA"),
    "b365_close": ("B365CH", "B365CD", "B365CA"),
    "average_close": ("AvgCH", "AvgCD", "AvgCA"),
    "maximum_close": ("MaxCH", "MaxCD", "MaxCA"),
    "pinnacle_close": ("PSCH", "PSCD", "PSCA"),
}

CANONICAL_FIELDS = (
    "event_id",
    "season",
    "league",
    "date",
    "time",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    *[field for fields in ODDS_GROUPS.values() for field in fields],
)


@dataclass(frozen=True)
class SourceInput:
    season: str
    league: str
    source_url: str
    sha256: str
    raw_path: str
    retrieved_at: str


@dataclass(frozen=True)
class VersionedDataset:
    dataset_version: str
    dataset_path: str
    manifest_path: str
    quality_report_path: str
    row_count: int
    source_count: int


def _parse_date(value: str) -> datetime:
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            pass
    raise ValueError(f"Unsupported Football-Data date: {value!r}")


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _safe_int(value: str | None) -> int | None:
    number = _safe_float(value)
    if number is None or not float(number).is_integer():
        return None
    return int(number)


def _event_id(league: str, match_date: str, home: str, away: str) -> str:
    key = "|".join((league.strip().upper(), match_date, home.strip(), away.strip()))
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]


def _odds_triple(
    row: dict[str, str], fields: tuple[str, str, str]
) -> tuple[float, float, float] | None:
    values = tuple(_safe_float(row.get(field)) for field in fields)
    if any(value is None or value <= 1.0 for value in values):
        return None
    return values  # type: ignore[return-value]


def _mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def _dataset_version(sources: Iterable[SourceInput]) -> str:
    identity = {
        "schema_version": CANONICAL_SCHEMA_VERSION,
        "sources": sorted(
            {
                "season": source.season,
                "league": source.league,
                "sha256": source.sha256,
            }
            for source in sources
        ),
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return f"fd_epl_v0.1_{digest[:12]}"


def build_versioned_dataset(
    sources: list[SourceInput],
    output_dir: str | Path,
) -> VersionedDataset:
    """Canonicalize completed matches, create a stable version and quality report."""
    if not sources:
        raise ValueError("At least one source is required")

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)

    dataset_version = _dataset_version(sources)
    canonical_rows: list[dict[str, Any]] = []
    per_source: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()
    cross_source_duplicates = 0

    for source in sorted(sources, key=lambda item: (item.season, item.league)):
        raw_path = Path(source.raw_path)
        with raw_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = reader.fieldnames or []
            raw_rows = 0
            completed_rows = 0
            invalid_core_rows = 0
            source_dates: list[datetime] = []
            teams: set[str] = set()
            missing_by_column = {column: 0 for column in columns}
            odds_complete = {name: 0 for name in ODDS_GROUPS}
            overrounds: dict[str, list[float]] = {name: [] for name in ODDS_GROUPS}

            for row in reader:
                raw_rows += 1
                for column in columns:
                    if not (row.get(column) or "").strip():
                        missing_by_column[column] += 1

                date_raw = (row.get("Date") or "").strip()
                home = (row.get("HomeTeam") or "").strip()
                away = (row.get("AwayTeam") or "").strip()
                home_goals = _safe_int(row.get("FTHG"))
                away_goals = _safe_int(row.get("FTAG"))
                result = (row.get("FTR") or "").strip().upper()

                if not date_raw or not home or not away:
                    invalid_core_rows += 1
                    continue

                try:
                    match_dt = _parse_date(date_raw)
                except ValueError:
                    invalid_core_rows += 1
                    continue

                source_dates.append(match_dt)
                teams.update((home, away))

                if home_goals is None or away_goals is None or result not in {"H", "D", "A"}:
                    continue

                completed_rows += 1
                iso_date = match_dt.date().isoformat()
                event_id = _event_id(source.league, iso_date, home, away)
                if event_id in seen_event_ids:
                    cross_source_duplicates += 1
                    continue
                seen_event_ids.add(event_id)

                canonical: dict[str, Any] = {
                    "event_id": event_id,
                    "season": source.season,
                    "league": source.league,
                    "date": iso_date,
                    "time": (row.get("Time") or "").strip(),
                    "home_team": home,
                    "away_team": away,
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "result": result,
                }

                for group_name, fields in ODDS_GROUPS.items():
                    triple = _odds_triple(row, fields)
                    if triple is not None:
                        odds_complete[group_name] += 1
                        overrounds[group_name].append(
                            sum(1.0 / value for value in triple) - 1.0
                        )
                    for field in fields:
                        canonical[field] = _safe_float(row.get(field))

                canonical_rows.append(canonical)

            per_source.append(
                {
                    "season": source.season,
                    "league": source.league,
                    "source_url": source.source_url,
                    "raw_sha256": source.sha256,
                    "raw_rows": raw_rows,
                    "completed_rows": completed_rows,
                    "invalid_core_rows": invalid_core_rows,
                    "team_count": len(teams),
                    "date_min": min(source_dates).date().isoformat()
                    if source_dates
                    else None,
                    "date_max": max(source_dates).date().isoformat()
                    if source_dates
                    else None,
                    "column_count": len(columns),
                    "missing_by_column": missing_by_column,
                    "odds_groups": {
                        name: {
                            "complete_rows": odds_complete[name],
                            "coverage_completed": (
                                odds_complete[name] / completed_rows
                                if completed_rows
                                else 0.0
                            ),
                            "mean_overround": _mean(overrounds[name]),
                        }
                        for name in ODDS_GROUPS
                    },
                }
            )

    canonical_rows.sort(key=lambda row: (row["date"], row["time"], row["event_id"]))
    dataset_path = output_root / f"{dataset_version}.csv"
    with dataset_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(CANONICAL_FIELDS))
        writer.writeheader()
        writer.writerows(canonical_rows)

    created_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "dataset_version": dataset_version,
        "canonical_schema_version": CANONICAL_SCHEMA_VERSION,
        "created_at": created_at,
        "provider": "Football-Data.co.uk",
        "competition": "English Premier League",
        "row_count": len(canonical_rows),
        "source_count": len(sources),
        "source_content_hashes": sorted(source.sha256 for source in sources),
        "sources": [
            asdict(source)
            for source in sorted(sources, key=lambda x: (x.season, x.league))
        ],
        "dataset_path": dataset_path.as_posix(),
        "version_identity_excludes_retrieval_timestamp": True,
    }
    manifest_path = output_root / "dataset_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    quality = {
        "dataset_version": dataset_version,
        "row_count": len(canonical_rows),
        "cross_source_duplicate_event_ids_dropped": cross_source_duplicates,
        "sources": per_source,
        "aggregate_odds_coverage": {
            group: {
                "complete_rows": sum(
                    source["odds_groups"][group]["complete_rows"]
                    for source in per_source
                ),
                "coverage": (
                    sum(
                        source["odds_groups"][group]["complete_rows"]
                        for source in per_source
                    )
                    / len(canonical_rows)
                    if canonical_rows
                    else 0.0
                ),
            }
            for group in ODDS_GROUPS
        },
    }
    quality_report_path = output_root / "quality_report.json"
    quality_report_path.write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )

    return VersionedDataset(
        dataset_version=dataset_version,
        dataset_path=dataset_path.as_posix(),
        manifest_path=manifest_path.as_posix(),
        quality_report_path=quality_report_path.as_posix(),
        row_count=len(canonical_rows),
        source_count=len(sources),
    )


def load_canonical_matches(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
