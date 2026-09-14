"""Football-Data.co.uk ingestion with immutable RAW evidence.

This module intentionally uses only the Python standard library so Phase 0 can
run before the modeling environment is expanded.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/{league}.csv"
SOURCE_NAME = "football_data_co_uk"
SCHEMA_VERSION = 1

_SEASON_RE = re.compile(r"^\d{4}$")
_LEAGUE_RE = re.compile(r"^[A-Za-z0-9]+$")


@dataclass(frozen=True)
class RawArtifact:
    source: str
    source_url: str
    season: str
    league: str
    retrieved_at: str
    sha256: str
    byte_count: int
    raw_path: str
    metadata_path: str
    schema_version: int
    profile: dict[str, Any]


def build_url(season: str, league: str) -> str:
    """Build a Football-Data CSV URL from a season token such as 2526 and E0."""
    if not _SEASON_RE.fullmatch(season):
        raise ValueError("season must be a four-digit Football-Data token, e.g. '2526'")
    if not _LEAGUE_RE.fullmatch(league):
        raise ValueError("league must contain only letters and digits, e.g. 'E0'")
    return BASE_URL.format(season=season, league=league)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def profile_csv_bytes(payload: bytes) -> dict[str, Any]:
    """Return lightweight source-quality diagnostics without mutating the RAW."""
    text = payload.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = reader.fieldnames or []

    row_count = 0
    missing_by_column = {name: 0 for name in fieldnames}
    duplicate_rows = 0
    seen_rows: set[tuple[str, ...]] = set()

    for row in reader:
        row_count += 1
        values = tuple((row.get(name) or "").strip() for name in fieldnames)
        if values in seen_rows:
            duplicate_rows += 1
        else:
            seen_rows.add(values)

        for name, value in zip(fieldnames, values):
            if value == "":
                missing_by_column[name] += 1

    return {
        "row_count": row_count,
        "column_count": len(fieldnames),
        "columns": fieldnames,
        "missing_by_column": missing_by_column,
        "duplicate_exact_rows": duplicate_rows,
    }


def _download_bytes(url: str, timeout_seconds: int = 30) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "invest_decisones-research/0.1 (+https://github.com/dinatalediego/invest_decisones)"
        },
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return response.read()


def download_dataset(
    season: str,
    league: str,
    output_root: str | Path = "data/raw/football_data",
    timeout_seconds: int = 30,
) -> RawArtifact:
    """Download one CSV and persist immutable bytes plus provenance metadata."""
    url = build_url(season, league)
    payload = _download_bytes(url, timeout_seconds=timeout_seconds)

    digest = sha256_bytes(payload)
    retrieved = datetime.now(timezone.utc)
    retrieved_iso = retrieved.isoformat()
    timestamp_token = retrieved.strftime("%Y%m%dT%H%M%SZ")

    directory = Path(output_root) / season / league
    directory.mkdir(parents=True, exist_ok=True)

    stem = f"{timestamp_token}_{digest[:12]}"
    raw_path = directory / f"{stem}.csv"
    metadata_path = directory / f"{stem}.metadata.json"

    # Immutability contract: never overwrite a prior evidence artifact.
    if raw_path.exists() or metadata_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing RAW artifact: {stem}")

    profile = profile_csv_bytes(payload)

    raw_path.write_bytes(payload)

    metadata = {
        "source": SOURCE_NAME,
        "source_url": url,
        "season": season,
        "league": league,
        "retrieved_at": retrieved_iso,
        "retrieval_timestamp": retrieved_iso,
        "sha256": digest,
        "raw_hash": digest,
        "byte_count": len(payload),
        "raw_path": raw_path.as_posix(),
        "schema_version": SCHEMA_VERSION,
        "profile": profile,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return RawArtifact(
        source=SOURCE_NAME,
        source_url=url,
        season=season,
        league=league,
        retrieved_at=retrieved_iso,
        sha256=digest,
        byte_count=len(payload),
        raw_path=raw_path.as_posix(),
        metadata_path=metadata_path.as_posix(),
        schema_version=SCHEMA_VERSION,
        profile=profile,
    )


def artifact_as_dict(artifact: RawArtifact) -> dict[str, Any]:
    return asdict(artifact)
