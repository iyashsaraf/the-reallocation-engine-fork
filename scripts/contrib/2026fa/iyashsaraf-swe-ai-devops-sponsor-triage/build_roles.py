#!/usr/bin/env python3
"""build_roles.py — SWE/AI/DevOps H-1B sponsor + funding triage (recipe
swe-ai-devops-sponsor-triage). Reads the 80-Days-to-Stay CSV (company-level
funding + H-1B sponsorship history, already joined), filters to companies with
a real sponsorship record and a title match for Software Engineer / AI /
DevOps roles, and writes a roles.json shaped for the existing Bayesian role
scorer (scripts/score/role-scorer.mjs).

Every evidence value is labeled "record" (read verbatim from the CSV),
"model-judgment" (the title-keyword match), or "your-input" (the OPT end date
and the hiring-lag assumption). Liveness is never silently omitted: the scorer
defaults a missing liveness factor to 1 (fully live), so this script always
emits an explicit, flagged, unverified value instead.

Usage:
  python3 build_roles.py [--csv PATH] [--soc-csv PATH] [--opt-end-date YYYY-MM-DD]
                          [--hiring-lag-days N] [--out-dir DIR] [--limit N]
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import date, datetime

DEFAULT_CSV = "data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv"
DEFAULT_SOC_CSV = "data/bls/compact/soc_occupation_compact.csv"
TECH_INDUSTRIES = {"Other Technology", "Computers"}
DEFAULT_OPT_END_DATE = "2027-03-15"
DEFAULT_HIRING_LAG_DAYS = 45

# Target SOC codes for this student's situation (Software Developers; Computer
# Occupations All Other, which includes the "Artificial Intelligence
# Specialist" alternate title; Network and Computer Systems Administrators,
# DevOps-adjacent).
TARGET_SOC_CODES = ["15-1252", "15-1299", "15-1244"]

# Keyword -> SOC code this title most plausibly maps to, for the role_quality
# lookup (context only; role_quality carries zero weight in the scorer today).
# Matching is word-boundary-aware to avoid short-substring false positives
# (e.g. a naive "ai" match hitting "Maintenance" or "Claims").
KEYWORD_SOC = [
    (r"\bdevops\b", "15-1244"),
    (r"\bsite reliability\b", "15-1244"),
    (r"\bsre\b", "15-1244"),
    (r"\bsystems? admin", "15-1244"),
    (r"\bplatform engineer", "15-1244"),
    (r"\bmachine learning\b", "15-1299"),
    (r"\bml engineer\b", "15-1299"),
    (r"\bartificial intelligence\b", "15-1299"),
    (r"\bai engineer\b", "15-1299"),
    (r"\bai\b", "15-1299"),
    (r"\bmlops\b", "15-1299"),
    (r"\bsoftware engineer", "15-1252"),
    (r"\bsoftware developer", "15-1252"),
    (r"\bbackend engineer", "15-1252"),
    (r"\bfull.?stack engineer", "15-1252"),
    (r"\bmobile engineer", "15-1252"),
]
KEYWORD_SOC_COMPILED = [(re.compile(pat, re.IGNORECASE), soc) for pat, soc in KEYWORD_SOC]


def classify_titles(top_job_titles_sponsored):
    """Return (matched: bool, matched_titles: list[str], soc_code: str|None).
    Model-judgment: a keyword/word-boundary string match, not a semantic one.
    """
    if not top_job_titles_sponsored or not top_job_titles_sponsored.strip():
        return False, [], None
    # Field is stored as a Python-list-literal string, e.g. "['Senior Software Engineer']".
    titles = re.findall(r"'([^']*)'|\"([^\"]*)\"", top_job_titles_sponsored)
    titles = [a or b for a, b in titles]
    if not titles:
        titles = [top_job_titles_sponsored]
    matched_titles = []
    matched_soc = None
    for title in titles:
        for pattern, soc in KEYWORD_SOC_COMPILED:
            if pattern.search(title):
                matched_titles.append(title)
                if matched_soc is None:
                    matched_soc = soc
                break
    return (len(matched_titles) > 0), matched_titles, matched_soc


def sponsorship_tier(approval_rate):
    if approval_rate >= 80:
        return "Proven"
    if approval_rate >= 50:
        return "Likely"
    if approval_rate > 0:
        return "Possible"
    return "None"


def safe_float(x, default=None):
    try:
        if x is None or x == "":
            return default
        return float(x)
    except (ValueError, TypeError):
        return default


def load_soc_quality(soc_csv_path):
    """Map SOC code -> {annual_median_wage, cognitive_pivot_score} (record)."""
    quality = {}
    if not os.path.exists(soc_csv_path):
        return quality
    with open(soc_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            soc = row.get("bls_soc_code", "")
            if soc in TARGET_SOC_CODES and soc not in quality:
                quality[soc] = {
                    "annual_median_wage": safe_float(row.get("annual_median_wage")),
                    "cognitive_pivot_score": safe_float(row.get("cognitive_pivot_score")),
                }
    return quality


def compute_timeline_factor(opt_end_date_str, hiring_lag_days, today=None):
    """your-input: opt_end_date composed with a disclosed hiring-lag assumption.
    Returns (factor, days_remaining). factor=0 when opt_end_date is already past —
    never clamped up to a fake positive number.
    """
    today = today or date.today()
    opt_end = datetime.strptime(opt_end_date_str, "%Y-%m-%d").date()
    days_remaining = (opt_end - today).days
    if days_remaining <= 0:
        return 0.0, days_remaining
    factor = min(1.0, days_remaining / float(hiring_lag_days))
    return round(factor, 4), days_remaining


def build_roles(csv_path, soc_csv_path, opt_end_date, hiring_lag_days, limit=None):
    if not os.path.exists(csv_path):
        print(f"ERROR: source CSV not found: {csv_path}", file=sys.stderr)
        sys.exit(2)

    soc_quality = load_soc_quality(soc_csv_path)
    timeline_factor, days_remaining = compute_timeline_factor(opt_end_date, hiring_lag_days)

    roles = []
    counts = {
        "rows_read": 0,
        "skipped_wrong_industry": 0,
        "skipped_no_approvals": 0,
        "skipped_no_titles": 0,
        "skipped_no_title_match": 0,
        "emitted": 0,
    }

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            counts["rows_read"] += 1

            if row.get("industry") not in TECH_INDUSTRIES:
                counts["skipped_wrong_industry"] += 1
                continue

            approvals = safe_float(row.get("Total Approvals"), default=0.0) or 0.0
            if approvals <= 0:
                counts["skipped_no_approvals"] += 1
                continue

            titles_field = row.get("top_job_titles_sponsored", "")
            if not titles_field or not titles_field.strip():
                counts["skipped_no_titles"] += 1
                continue

            matched, matched_titles, matched_soc = classify_titles(titles_field)
            if not matched:
                counts["skipped_no_title_match"] += 1
                continue

            approval_rate = safe_float(row.get("Approval_Rate"), default=0.0) or 0.0
            tier = sponsorship_tier(approval_rate)
            fit_p = round(min(1.0, 0.5 + 0.15 * len(matched_titles)), 4)

            role = {
                "role_id": re.sub(r"[^a-z0-9]+", "-", row["company_name"].lower()).strip("-"),
                "company": row["company_name"],
                "title": matched_titles[0],
                "sponsorship": {
                    "p": round(approval_rate / 100.0, 4),
                    "tier": tier,
                    "source": "record",
                    "approvals": approvals,
                    "denials": safe_float(row.get("Total Denials"), default=0.0),
                },
                "fit": {
                    "p": fit_p,
                    "source": "model-judgment",
                    "matched_titles": matched_titles,
                },
                "liveness": {
                    "factor": 0.5,
                    "source": "your-input",
                    "note": "not verified — sample mode; run npm run ats:liveness against a real posting URL before trusting an Apply recommendation",
                },
                "timeline": {
                    "factor": timeline_factor,
                    "source": "your-input",
                    "opt_end_date": opt_end_date,
                    "hiring_lag_days_assumed": hiring_lag_days,
                    "days_remaining": days_remaining,
                },
                "funding": {
                    "latest_funding_stage": row.get("latest_funding_stage") or None,
                    "latest_funding_date": row.get("latest_funding_date") or None,
                    "total_funding": safe_float(row.get("total_funding")),
                    "source": "record",
                },
            }
            if matched_soc and matched_soc in soc_quality:
                role["role_quality"] = {
                    **soc_quality[matched_soc],
                    "soc_code": matched_soc,
                    "source": "record",
                    "note": "context only — role_quality carries zero weight in scripts/score/role-scorer.mjs today",
                }
            else:
                role["role_quality_status"] = "no-soc-match"

            roles.append(role)
            counts["emitted"] += 1

            if limit is not None and counts["emitted"] >= limit:
                break

    return roles, counts


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default=DEFAULT_CSV)
    ap.add_argument("--soc-csv", default=DEFAULT_SOC_CSV)
    ap.add_argument("--opt-end-date", default=DEFAULT_OPT_END_DATE)
    ap.add_argument("--hiring-lag-days", type=int, default=DEFAULT_HIRING_LAG_DAYS)
    ap.add_argument("--out-dir", required=True, help="never a tracked repo path")
    ap.add_argument("--limit", type=int, default=None, help="cap number of emitted roles")
    args = ap.parse_args()

    roles, counts = build_roles(
        args.csv, args.soc_csv, args.opt_end_date, args.hiring_lag_days, args.limit
    )

    os.makedirs(args.out_dir, exist_ok=True)
    out_path = os.path.join(args.out_dir, "roles.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(roles, f, indent=2)

    print(f"rows_read={counts['rows_read']}")
    print(f"skipped_wrong_industry={counts['skipped_wrong_industry']}")
    print(f"skipped_no_approvals={counts['skipped_no_approvals']}")
    print(f"skipped_no_titles={counts['skipped_no_titles']}")
    print(f"skipped_no_title_match={counts['skipped_no_title_match']}")
    print(f"emitted={counts['emitted']}")
    print(f"wrote {out_path}")
    if counts["emitted"] == 0:
        print("WARNING: zero roles emitted — check source CSV and keyword list", file=sys.stderr)


if __name__ == "__main__":
    main()
