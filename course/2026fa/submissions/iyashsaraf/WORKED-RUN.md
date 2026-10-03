# Worked Run — swe-ai-devops-sponsor-triage

## Executive summary

This is the real, reproducible run of the prototype against the full repo
dataset — not a described or imagined run. It shows the exact commands, their
real terminal output, a line-by-line split of what was verified versus
inferred, how that output was checked for correctness, and an honest
reflection on what the run got wrong.

## Inputs used

- Source CSV: `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` (shipped with the repo, 30,369 rows — real company data, not a persona).
- `--opt-end-date 2027-03-15` — a placeholder, labeled `your-input` throughout, not this student's real date.
- `--hiring-lag-days 45` (default) — a disclosed assumption, labeled `your-input`.

## Commands run, with real output

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

Top of the real `role-scores.md` (unedited):

```
# Role Scorer report — 2026-10-01

*Bayesian Role Scorer (Ch.11). Weights: sponsorship 0.35, fit 0.3, role_quality 0 [role_quality weight is **[VERIFY]** — not pinned by the chapter]. Threshold 0.3. Profile requires sponsorship.*

**Summary:** 386 roles → Apply 55 · Consider 328 · Skip 3. **Skip rate 1%** (below the ~50% a healthy run skips; check the inputs).

| Role | Composite | Rec | Why | Audit (term · value · weight · source) |
|---|---|---|---|---|
| CLARI INC — Senior Software Engineer | 0.325 | **Apply** | composite 0.325 ≥ 0.3, gates healthy | sponsorship 1·0.35 [record]; fit 1·0.3 [model-judgment] × liveness 0.5[your-input]×timeline 1[your-input] |
| CYNGN INC — Sr. Software Engineer - Vehicle & Hardware | 0.325 | **Apply** | composite 0.325 ≥ 0.3, gates healthy | sponsorship 1·0.35 [record]; fit 1·0.3 [model-judgment] × liveness 0.5[your-input]×timeline 1[your-input] |
| LIFE360 INC — DevOps Engineer II | 0.325 | **Apply** | composite 0.325 ≥ 0.3, gates healthy | sponsorship 1·0.35 [record]; fit 1·0.3 [model-judgment] × liveness 0.5[your-input]×timeline 1[your-input] |
```

## Verified vs. inferred — line-by-line split (first row, CLARI INC)

| Field | Value | Label | How it got there |
|---|---|---|---|
| `company` | CLARI INC | record | copied verbatim from the CSV's `company_name` |
| `sponsorship.p` | 1.0 | record | `Approval_Rate / 100` from the CSV |
| `sponsorship.tier` | Proven | record | bucketed from `Approval_Rate` (≥80% → Proven) by this script, not asserted by the source |
| `fit.p` | 1.0 | model-judgment | keyword/word-boundary match on `top_job_titles_sponsored`, not a semantic judgment of whether the role is truly SWE-equivalent |
| `liveness.factor` | 0.5 | your-input | a disclosed placeholder — this posting's liveness was **never actually checked** |
| `timeline.factor` | 1.0 | your-input | computed from the placeholder OPT date (2027-03-15) and the 45-day hiring-lag assumption, both disclosed |
| `recommendation` | Apply | derived | the scorer's own arithmetic over the above — see the audit trace column; this is not an independent claim, it's `(1×0.35 + 1×0.3) × 0.5 × 1 = 0.325 ≥ 0.3` |

## Verification

- **Cross-checked by hand:** opened the source CSV and confirmed CLARI INC's
  row shows `Total Approvals=... Total Denials=0.0 Approval_Rate=100.0` and
  `top_job_titles_sponsored` containing "Senior Software Engineer" — matches
  what the script read.
- **Ran the offline test suite:** 10/10 pass (see `TEST-REPORT.md`), including
  a deliberate false-positive trap (`MAINTENANCECORP INC` / "Maintenance
  Claims Coordinator" must NOT match a naive "ai" substring check).
- **Deliberate break attempt:** fed `--opt-end-date 2020-01-01` (already
  past). Confirmed every emitted role's `timeline.factor` became exactly
  `0.0` (not clamped to a small positive number), and that feeding those
  roles through the real scorer forced `Skip 3 · Apply 0 · Consider 0`
  (100% skip) — see `TEST-REPORT.md` for the full output.

## Reflection

**What worked:** the keyword classifier correctly separated "sponsors
engineering-ish titles" from "sponsors something, just not this" on the first
real run — 467 companies were excluded this way, not silently scored. The
offline test suite caught the intended false-positive trap on the first try.

**What the recipe/prototype got wrong or missed:** the Skip rate (1%) is far
below the "healthy run skips at least half" bar this repo's own principles
set, and the scorer's own report says so explicitly. This wasn't predicted in
`CHANGE-BRIEF.md` — I predicted the keyword classifier would need a correction
and it didn't; instead, the sample-mode liveness placeholder (0.5) turned out
to be too permissive to function as a real gate, since the scorer's
`gate_zero` threshold (0.05) is much lower. The recipe technically does what
it claims (never silently defaults liveness to "live"), but the *value* chosen
for "unverified" doesn't behave like an unverified signal should in the
scorer's math — a genuinely unverified posting should not be able to reach
"Apply" at all.

**One concrete next improvement:** add a separate, clearly-labeled
post-processing step (its own small script, not a modified copy of
`role-scorer.mjs`) that caps any role's recommendation at "Consider" whenever
`liveness.source == "your-input"`, so an unverified posting can never surface
as "Apply" until a real `npm run ats:liveness` result replaces the placeholder.

## Attestation

- Recipe: swe-ai-devops-sponsor-triage v0.1.0
- By: Yash Saraf · 2026-10-01

### Tested

| Ran | Saw | Expected |
|---|---|---|
| `bash scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run.sh` | 386/30369 roles emitted; Apply 55 · Consider 328 · Skip 3 | roles written and scored without errors |
| `python3 .../build_roles_test.py -v` | 10/10 tests pass | all pass, including the false-positive trap |
| `python3 .../build_roles.py --csv /nonexistent/missing.csv ...` | `ERROR: source CSV not found...`, exit code 2 | nonzero exit, no fabricated output file |
| **Deliberate break attempt:** `--opt-end-date 2020-01-01` then scored | every role `timeline.factor=0.0`; scorer returns Skip 3/3 (100%) | gate correctly zeroes the composite regardless of sponsorship strength |

### Did not test

- A live `npm run ats:liveness` run against a real posting URL (out of scope
  for this sample-mode prototype; named explicitly as a gap in the recipe,
  card, and README rather than silently skipped).
- Behavior on a CSV with a different column order or renamed headers (the
  script relies on `csv.DictReader`, which is header-name-based, but this
  wasn't exercised with a deliberately-malformed header row).
- Any company whose `top_job_titles_sponsored` field uses a different
  list-literal quoting style than the two patterns the regex handles
  (single- and double-quoted strings) — not observed in the real CSV, but not
  exhaustively fuzzed either.

### Broke during testing, fixed

- Nothing broke during testing that required a code change — the prediction
  in `CHANGE-BRIEF.md` that the keyword classifier would need a correction did
  not materialize (see Revisions in that file). The thing that did need
  attention (the Skip-rate finding above) is recorded as a named next
  improvement, not fixed in this pass, since fixing it well means a
  deliberate design decision (a capping post-processing step) rather than a
  quick patch.
