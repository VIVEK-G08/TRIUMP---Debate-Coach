import unittest

from triump_app.helpers import fact_counts, level_from_points, session_points


class HelperLogicTests(unittest.TestCase):
    def test_fact_counts(self):
        facts = [
            {"stance": "support"},
            {"stance": "support"},
            {"stance": "counter"},
            {"stance": "other"},
        ]
        self.assertEqual(fact_counts(facts), (2, 1))

    def test_level_from_points(self):
        level, progress, remaining = level_from_points(275)
        self.assertEqual(level, 2)
        self.assertAlmostEqual(progress, 0.1)
        self.assertEqual(remaining, 225)

    def test_session_points_rewards_balance(self):
        result = {"strength_score": 8, "fallacy_count": 1, "summary": "ok", "reframed_argument": "stronger"}
        points = session_points(result, 6, 6, [])
        self.assertGreaterEqual(points, 100)


if __name__ == "__main__":
    unittest.main()
