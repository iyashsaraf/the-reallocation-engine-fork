# SWE/AI/DevOps sponsor + funding triage — human card

**Audience:** an international student deciding which companies are worth
research-and-apply hours today.
**Agent twin:** `recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.md`
**Engine layers:** 80 Days to Stay (funding + sponsorship, both already in one
CSV). Role quality (BLS/O*NET) is read for context only — it does not affect
the recommendation.

## Purpose

Answer: of the companies with a real H-1B sponsorship history, which ones have
actually sponsored roles that look like Software Engineer / AI / DevOps work —
and of those, which are still worth applying to once liveness and your OPT
timeline are accounted for?

## What it can verify

- A company's nonzero H-1B approval count and computed approval rate, straight
  from `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`.
- That company's most recent funding stage/date, from the same CSV.
- Whether that company's previously-sponsored titles contain a SWE/AI/DevOps
  keyword match (a heuristic string match — labeled `model-judgment`, not a
  record).
- BLS median wage and `cognitive_pivot_score` for a resolved SOC code (context
  only, not scored — see "role quality carries zero weight" below).

## What it cannot verify

- Whether a specific job posting today is real and accepting applicants. That
  needs `npm run ats:liveness` against an actual URL — not run in sample mode.
- Whether this company will sponsor *you*, for *this* role, this year.
  Historical approval rate is not a promise.
- Whether hiring will actually finish before your OPT window closes — the
  timeline factor is a disclosed assumption (hiring-lag constant), not a
  per-company estimate.
- Whether a free-text title match is semantically right (e.g. "Platform
  Engineer" matching "devops" may or may not describe the same work at every
  company).

## Dependencies

- `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` (shipped with the repo)
- `data/bls/compact/soc_occupation_compact.csv` (shipped with the repo)
- `scripts/score/role-scorer.mjs` (existing scorer, reused as-is)
- Python 3 standard library only (`csv`, `json`, `argparse`, `datetime`) — no new dependencies

## Annotated commands

One documented command, from the repo root (see this prototype's own README for
the exact invocation):

```bash
bash scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run.sh
```

Expected: a count of companies read, a count excluded by reason
(`skipped_no_approvals`, `skipped_no_titles`, `skipped_no_title_match`), the
number of roles written to `roles.json`, then the scorer's own
Apply/Consider/Skip counts and Skip rate.

Deliberate break-test (expected: every role's timeline factor becomes `0`, all
Skip):

```bash
python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles.py \
  --opt-end-date 2020-01-01 --out-dir /tmp/broken-timeline-test
```

## What it produces

- `roles.json` — one row per company that cleared G2/G3, each evidence term
  labeled `record` or `model-judgment`, liveness always labeled `your-input`
  with an explicit "not verified" note in sample mode.
- `role-scores.json` / `role-scores.md` — the existing scorer's own audit-traced
  output, unmodified.

## Named failure modes

1. **False "fully live" assumption.** If liveness were simply omitted,
   `role-scorer.mjs` defaults it to `1` (fully live) —
   `num(role.liveness?.factor) ?? 1`. Mitigation: this prototype always emits
   an explicit sub-1 liveness value with a `your-input` / "not verified" note,
   so the scorer's permissive default can never silently stand in for a real
   check. A student or reviewer scanning `roles.json` would be the one to catch
   this if it were missing — it would look like every company passed a
   liveness check that never happened.
2. **Company-level sponsorship mistaken for role-level sponsorship.** A company
   can have `Total Approvals > 0` for, say, a finance role, with no SWE/AI/
   DevOps title in its sponsored-titles history. Mitigation: rows with no
   title match are excluded and counted (`skipped_no_titles` /
   `skipped_no_title_match`), not silently scored as a weak match. Hardest to
   catch: a student skimming only the Apply list would never see these
   exclusions unless the exclusion counts are reported — which this recipe
   requires.
3. **Keyword-match false positives on short substrings.** A naive substring
   match for "ai" would match unrelated words (e.g. "Maintenance," "Claims").
   Mitigation: the classifier uses word-boundary-aware matching, verified in
   the offline test fixture.
4. **Stale funding signal read as momentum.** `latest_funding_date` can be
   several years old; an old Series A is not the same signal as a Series A
   last quarter. Mitigation: the human report shows the raw funding date
   so this interpretation stays the reader's job, not a silently-aged score.
