import unittest

from invest_decisones.data.football_data import (
    build_url,
    profile_csv_bytes,
    sha256_bytes,
)


class FootballDataTests(unittest.TestCase):
    def test_build_url(self) -> None:
        self.assertEqual(
            build_url("2526", "E0"),
            "https://www.football-data.co.uk/mmz4281/2526/E0.csv",
        )

    def test_invalid_season_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            build_url("2025-26", "E0")

    def test_sha256_is_stable(self) -> None:
        self.assertEqual(
            sha256_bytes(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
        )

    def test_profile_counts_missing_and_duplicate_rows(self) -> None:
        payload = (
            b"Date,HomeTeam,AwayTeam,FTHG\n"
            b"01/01/2026,A,B,2\n"
            b"02/01/2026,C,D,\n"
            b"02/01/2026,C,D,\n"
        )
        profile = profile_csv_bytes(payload)
        self.assertEqual(profile["row_count"], 3)
        self.assertEqual(profile["column_count"], 4)
        self.assertEqual(profile["missing_by_column"]["FTHG"], 2)
        self.assertEqual(profile["duplicate_exact_rows"], 1)


if __name__ == "__main__":
    unittest.main()
