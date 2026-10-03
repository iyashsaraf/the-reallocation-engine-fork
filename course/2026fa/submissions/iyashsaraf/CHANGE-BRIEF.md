# CHANGE-BRIEF — SWE/AI/DevOps H-1B Sponsor + Funding Triage

Written 2026-10-01, before any recipe or prototype code existed. This record is not
rewritten after the fact; later corrections are appended under "Revisions," not
edited into the predictions below.

## Executive summary

This is the pre-build prediction record for a new Reallocation Engine recipe. It
names the career situation, the exact data/scripts the recipe will reuse, the gates
it stops at, two predicted failure cases, and one prediction about what the first
prototype pass will get wrong — all written before writing the recipe or the code,
so the predictions can be checked against what actually happened.

## Career situation

MS in Software Engineering student on F-1, OPT end date **2027-03-15** (a placeholder
— `your-input`, not a real date, chosen to be realistic but not personal), targeting
Software Engineer / AI / DevOps roles. SOC codes in scope: **15-1252** (Software
Developers), **15-1299** (Computer Occupations, All Other — includes the
"Artificial Intelligence Specialist" alternate title), **15-1244** (Network and
Computer Systems Administrators — DevOps-adjacent).

Engine layers drawn on:
- **80 Days to Stay** (funding + sponsorship — both already joined in one CSV, see below)
- **The Cognitive Pivot** (BLS/O*NET role quality, for context only — see Fact 1 below)
- **Job-Ops** (liveness) is named but not executed live in this recipe's sample path
  (see predicted failure case 1).

## Existing data/scripts to reuse (exact paths)

- `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv` —
  30,369 rows, already joins company funding (`total_funding`,
  `latest_funding_amount`, `latest_funding_stage`, `latest_funding_date`) with H-1B
  sponsorship history (`Total Approvals`, `Total Denials`, `Approval_Rate`,
  `median_salary_offered`, `top_job_titles_sponsored`). This single file supplies
  both the funding vote and the sponsorship vote; the SEC Form D samples
  (`data/sec/form-d/processed/sample/*.sample.json`) are not joined in the core
  path of this recipe.
- `data/bls/compact/soc_occupation_compact.csv` — SOC-indexed BLS/O*NET data,
  including a precomputed `cognitive_pivot_score` column, for the role-quality
  signal.
- `scripts/score/role-scorer.mjs` (`npm run score`) — the existing Bayesian role
  scorer. The prototype writes a `roles.json` shaped like
  `data/examples/ch11-roles.json` and hands it to this script unmodified.

## Proposed addition the repo doesn't have yet

A keyword-based SWE/AI/DevOps title classifier over `top_job_titles_sponsored`
(e.g. matching "software engineer," "devops," "site reliability," "machine
learning," "artificial intelligence," "mlops," etc.). This doesn't exist anywhere
in the repo. It belongs here because the CSV's sponsorship data is company-level,
not role-level — without this classifier the recipe could only say "this company
sponsors," not "this company sponsors roles like mine." The match itself is a
**model-judgment** (a heuristic string match), not a verified fact, and will be
labeled as such everywhere it appears.

## Gates

1. **Liveness gate** — a posting must be a real, open requisition, not a ghost
   listing. A human needs to see: the actual job-board URL and a passing
   `npm run ats:liveness` result (or, in sample mode, an explicit "not verified"
   flag — see failure case 1) before clearing this gate.
2. **Visa-timeline gate** — the estimated time to hire must fit inside the
   remaining OPT window. A human needs to see: the OPT end date used, the
   hiring-lag assumption used, and the resulting timeline factor, before trusting
   an Apply recommendation gated on this.

## Predicted failure cases

1. **Liveness cannot be verified in sample mode.** The prototype runs on sample
   data only and makes no live network calls in its tested path (per the
   assignment's offline-test requirement). I predict that if the prototype simply
   omits the `liveness` field, the existing scorer will silently default it to
   `1` (fully live) — see `scripts/score/role-scorer.mjs`: `num(role.liveness?.factor) ?? 1`.
   That would misrepresent an unchecked posting as a verified-live one. Check: the
   prototype will always emit an explicit `liveness` object with a sub-1,
   clearly-labeled placeholder value and a note that it was not verified, so this
   silent default can never fire unnoticed.
2. **A sponsoring company has no role-specific title data.** Some rows in the CSV
   have `Total Approvals > 0` but an empty or null `top_job_titles_sponsored`
   field — the company has sponsored *something*, but not provably a role like
   this student's. Check: these rows are excluded from the output roles list
   (not scored as a weak match), and the script counts and reports how many were
   excluded this way, so the exclusion is visible rather than silent.

## One prediction about what the first pass will get wrong

I predict the keyword classifier for "AI" roles will have the most false
positives/negatives of anything in the pipeline, because `top_job_titles_sponsored`
titles are free text (e.g. "Senior Software Engineer," "Technical Lead") and a
plain substring match for "ai" will likely have to be scoped carefully (e.g.
require a word boundary) to avoid matching unrelated words that happen to contain
"ai" as a substring (e.g. "Email," "Maintenance," "Claims"). I expect this to need
at least one correction after the first real run against the full CSV, and the
worked-run reflection will record whatever that correction turns out to be.

## Revisions

**2026-10-01, after the first real run against the full CSV:**

- The predicted keyword-classifier correction (false positives on short "ai"
  substrings) did **not** need a post-build fix — the word-boundary regex was
  written correctly on the first pass and the offline test
  (`test_no_false_positive_on_short_ai_substring`) passed immediately. That
  prediction turned out wrong; recorded here rather than quietly dropped.
- An unpredicted issue surfaced instead: the real run's Skip rate was 1%
  (Apply 55 / Consider 328 / Skip 3 of 386), far below the "healthy run skips
  at least half" expectation the scorer's own report flags. Root cause: the
  sample-mode liveness placeholder (`factor: 0.5`) is a soft discount on the
  composite score, not a real gate — the scorer's `gate_zero` threshold is
  0.05, so 0.5 almost never forces an actual Skip the way a true "not verified"
  signal should. Only an already-past OPT date reliably forces Skip in this
  recipe today. See `TEST-REPORT.md` for the concrete next-improvement
  proposal (never let an unverified-liveness role reach "Apply").
