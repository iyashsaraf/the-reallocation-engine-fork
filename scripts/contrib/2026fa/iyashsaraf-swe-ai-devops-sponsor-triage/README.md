# swe-ai-devops-sponsor-triage — prototype

Implements the sample-mode path of
`recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.md`.

## Run it (one command, from the repo root)

```bash
bash scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run.sh
```

This reads the real
`data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`,
filters to tech companies with a nonzero H-1B approval count and a
Software-Engineer/AI/DevOps title match in `top_job_titles_sponsored`, writes
`run/roles.json`, then hands that file to the repo's existing scorer
(`npm run score`) to produce `run/role-scores.json` and `run/role-scores.md`.
Nothing is written outside this folder's own `run/` subdirectory.

## Run the offline test

```bash
python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles_test.py -v
```

Fixture-based (`fixtures/mini-targets.csv`), no network calls, does not read
the real 30k-row CSV.

## What Apply / Consider / Skip means here

- **Apply** — strong sponsorship history + title match + funding signal, and
  the gates (liveness, timeline) are healthy. In sample mode, liveness is
  **never actually verified** (see below), so treat any Apply here as
  "Consider, pending a real liveness check," not a go-ahead.
- **Consider** — same evidence, but either a soft sponsorship tier or a gate
  close to its floor.
- **Skip** — a closed gate (timeline already past, or the scorer's gate
  threshold) zeroes the score regardless of how strong the other evidence is.
  A healthy run skips at least half of what it evaluates.

## Known limitation in this sample-mode run

`liveness.factor` is always an explicit placeholder (`0.5`, source
`your-input`, flagged "not verified") — this prototype makes no live network
calls in its tested path. A real run must replace this by executing
`npm run ats:liveness -- <job-url>` per shortlisted posting before trusting any
Apply recommendation.

## Options

```bash
python3 scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/build_roles.py \
  --csv <path>            # default: the real 80-Days CSV
  --soc-csv <path>         # default: the real BLS compact CSV
  --opt-end-date YYYY-MM-DD   # default: 2027-03-15 (your-input placeholder)
  --hiring-lag-days N      # default: 45 (your-input assumption)
  --out-dir <dir>          # required
  --limit N                # cap emitted roles, for a quick smoke run
```
