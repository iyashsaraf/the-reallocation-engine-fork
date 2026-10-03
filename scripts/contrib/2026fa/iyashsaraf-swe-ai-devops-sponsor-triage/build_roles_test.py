#!/usr/bin/env python3
"""Offline test for build_roles.py. Fixture-based, no network calls, does not
read the real 30k-row CSV.

Run: python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles_test.py
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_roles  # noqa: E402

FIXTURE_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "mini-targets.csv")


class TestClassifyTitles(unittest.TestCase):
    def test_matches_software_engineer(self):
        matched, titles, soc = build_roles.classify_titles("['Senior Software Engineer']")
        self.assertTrue(matched)
        self.assertEqual(soc, "15-1252")

    def test_matches_devops(self):
        matched, titles, soc = build_roles.classify_titles("['Platform Engineer', 'DevOps Lead']")
        self.assertTrue(matched)
        self.assertEqual(soc, "15-1244")

    def test_matches_ai(self):
        matched, titles, soc = build_roles.classify_titles("['AI Research Engineer']")
        self.assertTrue(matched)
        self.assertEqual(soc, "15-1299")

    def test_no_false_positive_on_short_ai_substring(self):
        # "Maintenance Claims Coordinator" contains "ai" as a bare substring in
        # "Maintenance" and "Claims" but must NOT match the word-boundary "ai" pattern.
        matched, titles, soc = build_roles.classify_titles("['Maintenance Claims Coordinator']")
        self.assertFalse(matched)

    def test_empty_titles_field(self):
        matched, titles, soc = build_roles.classify_titles("")
        self.assertFalse(matched)
        matched, titles, soc = build_roles.classify_titles("[]")
        self.assertFalse(matched)


class TestTimelineFactor(unittest.TestCase):
    def test_future_date_gives_positive_factor(self):
        from datetime import date, timedelta
        today = date(2026, 10, 1)
        future = (today + timedelta(days=100)).isoformat()
        factor, days = build_roles.compute_timeline_factor(future, 45, today=today)
        self.assertGreater(factor, 0)
        self.assertEqual(days, 100)

    def test_past_date_zeroes_factor(self):
        from datetime import date
        today = date(2026, 10, 1)
        factor, days = build_roles.compute_timeline_factor("2020-01-01", 45, today=today)
        self.assertEqual(factor, 0.0)
        self.assertLess(days, 0)


class TestBuildRolesFixture(unittest.TestCase):
    def setUp(self):
        self.out_dir = tempfile.mkdtemp()

    def test_fixture_counts_and_exclusions(self):
        roles, counts = build_roles.build_roles(
            csv_path=FIXTURE_CSV,
            soc_csv_path="/nonexistent/no-soc-data.csv",  # role_quality intentionally unresolvable
            opt_end_date="2027-03-15",
            hiring_lag_days=45,
        )
        self.assertEqual(counts["rows_read"], 8)
        self.assertEqual(counts["skipped_wrong_industry"], 1)  # WRONGINDUSTRY INC
        self.assertEqual(counts["skipped_no_approvals"], 1)  # ZEROAPPROVALS INC
        self.assertEqual(counts["skipped_no_titles"], 1)  # NOTITLESDATA INC
        self.assertEqual(counts["skipped_no_title_match"], 1)  # MAINTENANCECORP INC
        self.assertEqual(counts["emitted"], 4)  # CLEARSWE, DEVOPSCO, AISPECIALCO, MLOPSFIRM

        companies = {r["company"] for r in roles}
        self.assertEqual(
            companies,
            {"CLEARSWE INC", "DEVOPSCO INC", "AISPECIALCO INC", "MLOPSFIRM INC"},
        )

        for role in roles:
            # liveness must never be silently omitted or defaulted to "live"
            self.assertIn("liveness", role)
            self.assertLess(role["liveness"]["factor"], 1.0)
            self.assertEqual(role["liveness"]["source"], "your-input")
            # unresolvable SOC must be flagged, not silently zeroed
            self.assertEqual(role.get("role_quality_status"), "no-soc-match")
            self.assertNotIn("role_quality", role)

    def test_past_opt_date_zeroes_every_role_timeline(self):
        roles, counts = build_roles.build_roles(
            csv_path=FIXTURE_CSV,
            soc_csv_path="/nonexistent/no-soc-data.csv",
            opt_end_date="2020-01-01",
            hiring_lag_days=45,
        )
        self.assertGreater(len(roles), 0)
        for role in roles:
            self.assertEqual(role["timeline"]["factor"], 0.0)

    def test_missing_csv_exits_nonzero(self):
        with self.assertRaises(SystemExit) as ctx:
            build_roles.build_roles(
                csv_path="/nonexistent/missing.csv",
                soc_csv_path="/nonexistent/no-soc-data.csv",
                opt_end_date="2027-03-15",
                hiring_lag_days=45,
            )
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
