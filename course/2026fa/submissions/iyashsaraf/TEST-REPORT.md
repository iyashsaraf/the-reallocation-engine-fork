# TEST-REPORT — swe-ai-devops-sponsor-triage

## Executive summary

This report records every check run against the prototype in
`scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/`: the
toolchain baseline before and after the change, the real sample run against the
full 30k-row dataset, both named failure cases exercised with real output, the
offline test suite, and a diff scoped to confirm nothing outside this
student's namespace was touched.

## Toolchain baseline

### Before (on `main`, before any of this student's files existed)

```
$ npm run doctor
ENVIRONMENT (required)
  ✓ node       v24.10.0
  ✓ python3    Python 3.13.5
...
SUMMARY
  environment: ✓ runnable
  recipes: 33/33 carry lifecycle frontmatter — all tracked
  next: continue

$ npm run verify
conformance: 158 files (85 md · 36 py · 30 js · 4 sh · 3 json)
✓ all conform (machine half of P4). Adequacy is still the human gate.
MANIFEST CHECK — The Reallocation Engine
==========================================
WARN (3):
  W1 ignore path not in .gitignore: archive/
  W2 private path not gitignored (PII/secret risk): private/
  W2 private path not gitignored (PII/secret risk): data/ats/
✓ manifest check passed (3 warnings)
```

Note: `manifest-check.mjs` calls system `python3 -c "import yaml..."` directly
and initially failed with `ModuleNotFoundError: No module named 'yaml'` — a
pre-existing environment gap (no PyYAML installed), unrelated to this
contribution. Homebrew's managed Python blocks a global `pip install` (PEP
668), so a throwaway venv (`python3 -m venv /tmp/verify-venv && .../pip install
pyyaml`) was prepended to `PATH` for local verification only — no repo files
were changed to work around this. The three `WARN` lines above
(`archive/`, `private/`, `data/ats/`) are pre-existing repo state, confirmed
present on `main` before this branch's changes (`git diff main -- <those
paths>` is empty).

### After (with this contribution's files added)

```
$ npm run verify
conformance: 167 files (89 md · 38 py · 30 js · 5 json · 5 sh)
✓ all conform (machine half of P4). Adequacy is still the human gate.
MANIFEST CHECK — The Reallocation Engine
==========================================
WARN (3):
  W1 ignore path not in .gitignore: archive/
  W2 private path not gitignored (PII/secret risk): private/
  W2 private path not gitignored (PII/secret risk): data/ats/
✓ manifest check passed (3 warnings)
```

Same 3 pre-existing warnings, no new ones. 9 new files picked up by
conformance (5 md, 2 py, 2 json, 1 sh — the `run/` output JSON files and this
recipe's md/card/readme/script/test/fixture).

```
$ node scripts/conformance.mjs scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/ \
    recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.md \
    recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.card.md \
    course/2026fa/submissions/iyashsaraf/
conformance: 10 files (5 md · 2 py · 2 json · 1 sh)
✓ all conform (machine half of P4). Adequacy is still the human gate.
```

```
$ node scripts/pii-scan.mjs
pii-scan: 1 finding(s) — see DATA_CONTRACT.md §Zero-Conditions
  [email] package-lock.json — <redacted here to avoid re-tripping the scanner on this report itself; it is the well-known npm maintainer "isaacs"'s public package-metadata address>
```

That finding is a dependency-metadata email in `package-lock.json`, unchanged
from `main` (`git diff main -- package-lock.json` is empty) — not introduced
by this contribution, and not personal data.

## Real sample run

```
$ bash scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run.sh
rows_read=30369
skipped_wrong_industry=19100
skipped_no_approvals=10416
skipped_no_titles=0
skipped_no_title_match=467
emitted=386
wrote scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run/roles.json

> the-reallocation-engine@1.0.0 score
> node scripts/score/role-scorer.mjs scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run/roles.json --out-dir scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run

✓ scored 386 roles → Apply 55 · Consider 328 · Skip 3 (skip 1%)
  scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run/role-scores.json  +  scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run/role-scores.md
```

## Named failure cases exercised

### 1. Company with no title match — handled without inventing a value

Already covered live: 467 of 30,369 rows were excluded as
`skipped_no_title_match` in the real run above (companies with a sponsorship
record but no SWE/AI/DevOps title in their history) — printed, not silent.
The offline test fixture additionally isolates this with
`MAINTENANCECORP INC` (titled "Maintenance Claims Coordinator" — a deliberate
short-substring trap for a naive "ai" match):

```
$ python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles_test.py -v
test_no_false_positive_on_short_ai_substring ... ok
```

### 2. OPT end date already past

```
$ python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles.py \
    --opt-end-date 2020-01-01 --out-dir /tmp/broken-timeline-test --limit 3
rows_read=366
skipped_wrong_industry=271
skipped_no_approvals=89
skipped_no_titles=0
skipped_no_title_match=3
emitted=3
wrote /tmp/broken-timeline-test/roles.json
```

Inspecting the emitted timeline field (no clamping to a fake positive number):

```json
{
  "factor": 0.0,
  "source": "your-input",
  "opt_end_date": "2020-01-01",
  "hiring_lag_days_assumed": 45,
  "days_remaining": -2465
}
```

A `factor: 0.0` is a closed gate in `role-scorer.mjs` (`gate_zero = 0.05`),
which forces the scorer's recommendation to `Skip` regardless of sponsorship
strength — verified by running these 3 roles through the scorer:

```
$ npm run score -- /tmp/broken-timeline-test/roles.json --out-dir /tmp/broken-timeline-test
✓ scored 3 roles → Apply 0 · Consider 0 · Skip 3 (skip 100%)
```

### Additional case: missing source CSV

```
$ python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles.py \
    --csv /nonexistent/missing.csv --out-dir /tmp/missing-csv-test2
ERROR: source CSV not found: /nonexistent/missing.csv
$ echo $?
2
```

Nonzero exit, no output file written, no fabricated empty `roles.json`.

## Offline test suite

```
$ python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles_test.py -v
test_fixture_counts_and_exclusions ... ok
test_missing_csv_exits_nonzero ... ok
test_past_opt_date_zeroes_every_role_timeline ... ok
test_empty_titles_field ... ok
test_matches_ai ... ok
test_matches_devops ... ok
test_matches_software_engineer ... ok
test_no_false_positive_on_short_ai_substring ... ok
test_future_date_gives_positive_factor ... ok
test_past_date_zeroes_factor ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.007s

OK
```

Fixture-based (`fixtures/mini-targets.csv`), no network calls, does not read
the real CSV.

## Scope check

```
$ git status --short
?? course/2026fa/
?? logs/runs/2026fa-iyashsaraf-1.md
?? recipes/cases/2026fa/
?? scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/
```

Only this student's namespaced paths — no other student's folder, no
`logs/RUN_LOG.md`.

## What the gates require a human to judge

- **Liveness gate (G4):** in sample mode, every role's liveness is an explicit,
  flagged, unverified placeholder (`factor: 0.5`, source `your-input`). A human
  must run `npm run ats:liveness -- <url>` against the actual shortlisted
  posting before treating any Apply recommendation here as action-ready.
- **Visa-timeline gate (G5):** the `--opt-end-date` and `--hiring-lag-days`
  are disclosed assumptions, not a researched per-company estimate. A human
  should replace the default with their real OPT date and sanity-check the
  45-day hiring-lag assumption against their own target companies before
  trusting the timeline factor.

## Finding and proposed next improvement (see also CHANGE-BRIEF Revisions)

The real run's Skip rate (1%) is far below the "healthy run skips at least
half" expectation the scorer's own `role-scores.md` flags
("below the ~50% a healthy run skips; check the inputs"). Mechanically: the
sample-mode liveness placeholder (`0.5`) is above the scorer's `gate_zero`
(0.05) threshold, so it only soft-discounts the composite instead of forcing a
Skip the way a genuinely-unverified posting should. Proposed next
improvement (not built in this pass, to avoid re-implementing or modifying
the shared scorer): a separate, clearly-labeled post-processing step in this
prototype's own folder that caps any role's recommendation at "Consider"
whenever `liveness.source == "your-input"` (i.e., never actually checked),
until a real `ats:liveness` result replaces it.
