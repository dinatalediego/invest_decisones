import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from invest_decisones.data.versioned_dataset import (
    SourceInput,
    build_versioned_dataset,
)


CSV = """Div,Date,Time,HomeTeam,AwayTeam,FTHG,FTAG,FTR,AvgH,AvgD,AvgA,AvgCH,AvgCD,AvgCA
E0,01/08/2024,15:00,Alpha,Beta,2,1,H,2.00,3.40,3.80,1.95,3.50,3.90
E0,02/08/2024,15:00,Gamma,Delta,1,1,D,2.20,3.20,3.10,2.25,3.25,3.15
"""


class VersionedDatasetTests(unittest.TestCase):
    def test_version_is_content_hash_stable_and_quality_is_measured(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = root / "E0.csv"
            raw.write_text(CSV, encoding="utf-8")
            digest = hashlib.sha256(raw.read_bytes()).hexdigest()

            source = SourceInput(
                season="2425",
                league="E0",
                source_url="https://example.test/E0.csv",
                sha256=digest,
                raw_path=raw.as_posix(),
                retrieved_at="2026-01-01T00:00:00+00:00",
            )

            first = build_versioned_dataset(
                [source],
                root / "one",
            )

            second_source = SourceInput(
                season="2425",
                league="E0",
                source_url="https://example.test/E0.csv",
                sha256=digest,
                raw_path=raw.as_posix(),
                retrieved_at="2026-02-01T00:00:00+00:00",
            )

            second = build_versioned_dataset(
                [second_source],
                root / "two",
            )

            self.assertEqual(
                first.dataset_version,
                second.dataset_version,
            )

            quality = json.loads(
                Path(
                    first.quality_report_path
                ).read_text()
            )

            self.assertEqual(
                quality["row_count"],
                2,
            )

            self.assertEqual(
                quality["sources"][0]["odds_groups"]["average_close"]["complete_rows"],
                2,
            )

            with Path(
                first.dataset_path
            ).open(
                newline="",
                encoding="utf-8",
            ) as handle:
                rows = list(
                    csv.DictReader(handle)
                )

            self.assertEqual(
                rows[0]["home_team"],
                "Alpha",
            )

            self.assertTrue(
                rows[0]["event_id"]
            )

    def test_version_supports_multiple_sources_and_is_order_invariant(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_raw = root / "first.csv"
            second_raw = root / "second.csv"
            first_raw.write_text(CSV, encoding="utf-8")
            second_raw.write_text(
                CSV.replace("Alpha", "Echo").replace("Beta", "Foxtrot"),
                encoding="utf-8",
            )

            first = SourceInput(
                season="2324",
                league="E0",
                source_url="https://example.test/2324.csv",
                sha256=hashlib.sha256(first_raw.read_bytes()).hexdigest(),
                raw_path=first_raw.as_posix(),
                retrieved_at="2026-01-01T00:00:00+00:00",
            )
            second = SourceInput(
                season="2425",
                league="E0",
                source_url="https://example.test/2425.csv",
                sha256=hashlib.sha256(second_raw.read_bytes()).hexdigest(),
                raw_path=second_raw.as_posix(),
                retrieved_at="2026-01-01T00:00:00+00:00",
            )

            forward = build_versioned_dataset(
                [first, second],
                root / "forward",
            )
            reverse = build_versioned_dataset(
                [second, first],
                root / "reverse",
            )

            self.assertEqual(
                forward.dataset_version,
                reverse.dataset_version,
            )


if __name__ == "__main__":
    unittest.main()
