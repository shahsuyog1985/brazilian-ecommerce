import unittest
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]


class OutputTests(unittest.TestCase):
    def test_monthly_orders_with_purchase_timestamp_reconcile(self):
        monthly = pd.read_csv(ROOT / "reports" / "monthly_performance.csv")
        # One order has no purchase timestamp and is intentionally absent.
        self.assertEqual(int(monthly.orders.sum()), 99_440)

    def test_category_revenue_is_positive_and_sorted(self):
        category = pd.read_csv(ROOT / "reports" / "category_performance.csv")
        self.assertTrue((category.item_revenue > 0).all())
        self.assertTrue(category.item_revenue.is_monotonic_decreasing)

    def test_advanced_outputs_have_no_customer_ids(self):
        for path in (ROOT / "reports" / "advanced").glob("*.csv"):
            columns = pd.read_csv(path, nrows=1).columns
            self.assertNotIn("customer_id", columns)
            self.assertNotIn("customer_unique_id", columns)


if __name__ == "__main__":
    unittest.main()
