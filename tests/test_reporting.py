import unittest

from reporting import build_auction_report, sample_auctions


class ReportingTests(unittest.TestCase):
    def test_sample_report_metrics(self):
        report = build_auction_report(sample_auctions(), top_n=2)

        self.assertEqual(report.total_auctions, 3)
        self.assertEqual(report.active_auctions, 2)
        self.assertEqual(report.upcoming_auctions, 1)
        self.assertEqual(report.ended_auctions, 0)
        self.assertEqual(report.total_bids, 8)
        self.assertEqual(report.peak_bid_hour, 9)
        self.assertEqual(report.hottest_auctions[0].auction_id, "AUCT-1001")
        self.assertEqual(report.top_categories[0].item_category, "accessories")


if __name__ == "__main__":
    unittest.main()
