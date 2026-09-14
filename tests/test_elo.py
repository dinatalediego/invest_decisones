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

    def test_same_day_results_do_not_change_other_same_day_predictions(self) -> None:
        base = [
            row(
                "train-1",
                "2324",
                "2024-01-01",
                "A",
                "B",
                "H",
            ),
            row(
                "train-2",
                "2324",
                "2024-01-02",
                "C",
                "D",
                "D",
            ),
        ]

        test_a = row(
            "a",
            "2425",
            "2025-01-01",
            "A",
            "C",
            "D",
            (2.0, 3.4, 3.8),
        )
        test_b = row(
            "b",
            "2425",
            "2025-01-01",
            "B",
            "D",
            "H",
            (2.2, 3.2, 3.3),
        )

        forward = run_elo_baseline(
            base + [test_a, test_b],
            "2425",
        )
        swapped_ids_a = dict(test_a, event_id="z")
        swapped_ids_b = dict(test_b, event_id="y")
        reversed_order = run_elo_baseline(
            base + [swapped_ids_b, swapped_ids_a],
            "2425",
        )

        self.assertEqual(
            forward["temporal_update_policy"],
            "daily_batch",
        )
        self.assertAlmostEqual(
            forward["elo"]["brier"],
            reversed_order["elo"]["brier"],
            places=12,
        )
        self.assertAlmostEqual(
            forward["elo"]["log_loss"],
            reversed_order["elo"]["log_loss"],
            places=12,
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
