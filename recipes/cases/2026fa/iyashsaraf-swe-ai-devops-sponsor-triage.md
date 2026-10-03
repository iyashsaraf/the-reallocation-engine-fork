---
status: RUNNABLE-SAMPLE
todos_open: 2
last_gate: null
attestation: null
recipe_version: 0.1.0
---

# swe-ai-devops-sponsor-triage — Company-level H-1B sponsorship × funding filter

## Executive summary

This recipe helps an international student targeting Software Engineer, AI, or
DevOps roles decide which companies are worth the research-and-apply hours in a
3-3-2 job-search day. It filters a 30,000+ company dataset down to tech employers
that (a) have an actual history of sponsoring H-1B visas and (b) have sponsored
roles whose titles look like the student's target roles, then hands that list to
the repo's existing scorer for an Apply/Consider/Skip recommendation per company.
It does **not** confirm that any specific open job posting is real or that this
year's hiring will happen in time — those remain gated, human-checked steps.

Two customers: this file is for the agent; `recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.card.md` is for the human.

**Handoff condition (done when):** a sample run is complete when the prototype
prints how many companies were read, how many were excluded (and why, by
reason), and how many roles were written to `roles.json`; the scorer then runs
on that file without errors and produces both `role-scores.json` and
`role-scores.md` with a stated Skip rate. "Looks right" is not the condition —
the counted-exclusion breakdown and the scorer's own audit trace are.

## Required reads

Read in this order before running:

1. `SNICKERDOODLE.md` — gates, provenance, TODO closure.
2. `DOMAIN.md` — layout; the 80-Days data lives under `data/80-days-to-stay/`.
3. `data/80-days-to-stay/80-days-csv/README.md` — what the CSV's columns mean and where they came from.
4. This recipe and `recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.card.md`.
5. `scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/README.md` — the prototype's one documented command.

Prefer those local files over external lookup.

## Source inventory

| Source | Path | What it supplies |
|---|---|---|
| Funding + sponsorship (company-level) | `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | `industry`, `total_funding`, `latest_funding_stage`, `latest_funding_date`, `Total Approvals`, `Total Denials`, `Approval_Rate`, `median_salary_offered`, `top_job_titles_sponsored` |
| Role quality (context only) | `data/bls/compact/soc_occupation_compact.csv` | `annual_median_wage`, `cognitive_pivot_score` for SOC 15-1252 / 15-1299 / 15-1244 |
| Scorer (reused, not reimplemented) | `scripts/score/role-scorer.mjs` (`npm run score`) | combines votes + gates into Apply/Consider/Skip with a full audit trace |
| This recipe's prototype | `scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles.py` | reads the CSV, classifies titles, writes `roles.json` |

## Proposed additions

- **SWE/AI/DevOps title classifier** over `top_job_titles_sponsored`
  [TODO: DEV — closed by `build_roles.py`, this recipe's own script; see Provenance].
  Justified because the CSV's sponsorship fields are company-level, not
  role-level — without a title match, "this company sponsors" cannot become
  "this company sponsors roles like mine."
- **Live liveness check wiring** (`npm run ats:liveness` against the student's
  actual shortlisted postings) [TODO: DATA SOURCE — the student must supply real
  job-posting URLs; none exist in sample mode]. Not built in this recipe; see
  Phase Gates and "What it can't verify."

## Phase gates

Each gate is a hard stop with a testable condition against paths that exist today.

| Gate | Type | Test | Pass | Fail |
|---|---|---|---|---|
| G1 — source exists | prerequisite | `test -f data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | proceed to filtering | stop: cannot run without the source CSV |
| G2 — sponsorship record present | vote input | row's `Total Approvals` is numeric and > 0 | company included as a sponsorship candidate | row excluded, counted as `skipped_no_approvals` |
| G3 — role-title match | vote input | `top_job_titles_sponsored` is non-empty and matches the SWE/AI/DevOps keyword list | role emitted with `fit` from the match | row excluded, counted as `skipped_no_titles` or `skipped_no_title_match` |
| **G4 — liveness (GATE, not a vote)** | hard stop | in sample mode: always fails open with an explicit unverified flag (see below); in a live run: `npm run ats:liveness -- <url>` must return a live result | role may reach Apply | role capped at Consider at best until a human runs real liveness |
| **G5 — visa timeline (GATE, not a vote)** | hard stop | `(opt_end_date − today) / hiring_lag_days`, clamped to `[0, 1]` | timeline factor > 0 | `opt_end_date` already past → factor = 0 → scorer forces Skip |

G4 and G5 are multipliers in the scorer (`scripts/score/role-scorer.mjs`), not
additive votes — a dead posting or an impossible timeline zeroes the composite
regardless of how strong the sponsorship/funding evidence is.

## Facts that bite, addressed

- **Role quality carries zero weight in the scorer.** This recipe reads
  `cognitive_pivot_score` from the BLS compact file for context in the human
  report, but does **not** claim it affects the Apply/Consider/Skip
  recommendation, because `role-scorer.mjs` hardcodes `role_quality: 0.0`
  weight today. No weight change is proposed here.
- **Only SEC Form D samples ship, and this recipe doesn't use them.** The
  funding signal here comes entirely from the 80-Days CSV's own
  `total_funding`/`latest_funding_stage`/`latest_funding_date` columns, which
  are already baked into that dataset — not from a fresh Form D join. This
  recipe does not claim Form D coverage beyond what's already reflected in the
  CSV it reads.
- **The `snickerdoodle` CLI does not run.** This recipe names only commands
  that exist today: `python3 scripts/contrib/.../build_roles.py`,
  `npm run score`, `node scripts/conformance.mjs`, `npm run verify`.

## What it can verify

- A company in `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`
  has a nonzero H-1B approval count and a computed `Approval_Rate` (record).
- That company's `top_job_titles_sponsored` field contains at least one title
  matching a disclosed SWE/AI/DevOps keyword list (model-judgment — a string
  match, not a semantic one).
- That company's most recent funding stage and date, as recorded in the CSV
  (record).
- The BLS `cognitive_pivot_score` and median wage for a resolved SOC code
  (record, context only — not scored).

## What it cannot verify

- Whether **this specific open requisition**, today, is real and accepting
  candidates — that requires a live `npm run ats:liveness` run against an
  actual posting URL, which this sample-mode prototype does not perform.
- Whether the company will still be sponsoring by the time this student
  applies — `Approval_Rate` is historical, not a guarantee.
- Whether the hiring process will actually complete before the stated OPT end
  date — the timeline factor is a disclosed assumption (a fixed hiring-lag
  constant), not a researched estimate for any specific company.
- Whether a free-text keyword match correctly captures role fit for an
  unusual job title.

## Output contract

### Agent output (machine)

File: `roles.json` (in the prototype's `--out-dir`), shaped per
`data/examples/ch11-roles.json`. Fields per role: `role_id`, `company`, `title`,
`sponsorship {p, tier, source}`, `fit {p, source}`, `liveness {factor, source,
note}`, `timeline {factor, source}`, optional `role_quality` (omitted, not
zeroed, when no SOC match exists).

### Human report (markdown)

File: `role-scores.md`, produced by `npm run score` from the agent output above.
Reader: the student, or a reviewer deciding whether to trust the run. Decision
enabled: which companies to prioritize for networking/research hours in the
student's 3-3-2 day, versus which to skip.

One file cannot serve both audiences (P5) — `roles.json` is for the scorer and
the agent; `role-scores.md` is for the person.

## Stop conditions and next action

- **Stop** if the source CSV is missing or unreadable — do not emit an empty or
  fabricated role list.
- **Stop (zero the row, don't guess)** if `opt_end_date` is already in the
  past — every role's timeline factor becomes `0`, which the scorer turns into
  an automatic Skip.
- **Next action on Apply:** tailor an application — but only after a human
  clears G4 with a real liveness check.
- **Next action on Consider:** manual verification of the specific posting and
  sponsorship recency before applying.
- **Next action on Skip:** this company may still be a target for a
  networking-hour informational interview (strong sponsorship history, just no
  live match right now) — not a dead end, a redirection to the "3" of 3-3-2.

## Run-log template

Use the shared template at `recipes/_shared.md` for entries in `logs/runs/`.
Record: date, recipe name + version, command run, `--opt-end-date` used,
companies read / excluded (by reason) / emitted, scorer's Apply/Consider/Skip
counts and Skip rate, and any gate decisions.

## Provenance

| Source | Verification command | Notes |
|---|---|---|
| `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | `test -f data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` | 30,369 rows; shipped with the repo. |
| `data/bls/compact/soc_occupation_compact.csv` | `grep -c "^15-1252\|^15-1299\|^15-1244" data/bls/compact/soc_occupation_compact.csv` | shipped compact BLS/O*NET extract. |
| `scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles.py` | `node scripts/conformance.mjs scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/` | this recipe's own script; closes the title-classifier TODO above. |
