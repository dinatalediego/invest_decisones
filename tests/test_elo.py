import unittest

from invest_decisones.models.elo import (
    EloConfig,
    run_elo_baseline,
)


def row(
    event_id,
    season,
    date,
    home,
    away,
    result,
    avg_close=None,
):
    values = {
        "event_id": event_id,
        "season": season,
        "league": "E0",
        "date": date,
        "time": "15:00",
        "home_team": home,
        "away_team": away,
        "result": result,
        "AvgCH": "",
        "AvgCD": "",
        "AvgCA": "",
        "AvgH": "",
        "AvgD": "",
        "AvgA": "",
    }

    if avg_close:
        (
            values["AvgCH"],
            values["AvgCD"],
            values["AvgCA"],
        ) = map(str, avg_close)

    return values


class EloTests(unittest.TestCase):
    def test_test_prediction_is_pre_match_and_market_is_evaluation_only(self) -> None:
        matches = [
            row(
                "1",
                "2324",
                "2024-01-01",
                "A",
                "B",
                "H",
            ),
            row(
                "2",
                "2324",
                "2024-01-02",
                "B",
                "A",
                "D",
            ),
            row(
                "3",
                "2425",
                "2025-01-01",
                "A",
                "B",
                "A",
                (2.0, 3.4, 3.8),
            ),
            row(
                "4",
                "2425",
                "2025-01-02",
                "B",
                "A",
                "H",
                (2.4, 3.2, 2.9),
            ),
        ]

        result = run_elo_baseline(
            matches,
            "2425",
            EloConfig(),
        )

        self.assertEqual(
            result["train_matches"],
            2,
        )

        self.assertEqual(
            result["test_matches"],
            2,
        )

        self.assertEqual(
            result["market_benchmark"]["metrics"]["n"],
            2,
        )

        self.assertEqual(
            result["status"],
            "baseline_challenger",
        )

    def test_requires_history_before_test(self) -> None:
        with self.assertRaises(ValueError):
            run_elo_baseline(
                [
                    row(
                        "1",
                        "2425",
                        "2025-01-01",
                        "A",
                        "B",
                        "H",
                    )
                ],
                "2425",
            )


if __name__ == "__main__":
    unittest.main()
