## 2026-10-01 — SWE/AI/DevOps sponsor + funding triage, sample run

- **Recipe:** `recipes/cases/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage.md` v0.1.0
- **Inputs:**
  `bash scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run.sh`
  (reads `data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`
  and `data/bls/compact/soc_occupation_compact.csv`; `--opt-end-date 2027-03-15`,
  default `--hiring-lag-days 45`)
- **Outputs:**
  `scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage/run/roles.json`,
  `.../run/role-scores.json`, `.../run/role-scores.md`
- **Result:** 30,369 CSV rows read → 386 roles emitted (19,100 wrong-industry,
  10,416 no-approvals, 0 no-titles, 467 no-title-match excluded). Scorer:
  Apply 55 · Consider 328 · Skip 3 (1% skip rate).
- **Open issues:** Skip rate (1%) is far below the "healthy run skips ≥50%"
  expectation — the scorer's own report flags this itself. Root cause: the
  sample-mode liveness placeholder (factor 0.5) multiplies the composite down
  but almost never crosses the scorer's `gate_zero` (0.05) threshold that
  forces an actual Skip, so it behaves as a soft discount, not a real gate, in
  this sample run. Only an already-past OPT date reliably forces Skip. Next
  improvement: do not let any role reach "Apply" on an unverified liveness
  value — see `TEST-REPORT.md` reflection for the concrete proposed fix.
