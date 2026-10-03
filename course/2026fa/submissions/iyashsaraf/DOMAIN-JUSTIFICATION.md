# Domain Justification — swe-ai-devops-sponsor-triage

## Who, in exactly what situation

An MS in Software Engineering student on F-1/OPT, targeting Software Engineer,
AI, and DevOps roles, with a limited OPT unemployment window (illustrated here
with a placeholder end date of 2027-03-15). Not "a tech job-seeker" generally —
specifically someone who needs to know, before spending an evening tailoring an
application, whether a company has a demonstrated history of sponsoring H-1B
visas for roles resembling theirs, and whether that company is currently
well-funded enough to be plausibly hiring.

## Information asymmetry addressed

Without this recipe, a student sees a job posting and a company name and has to
guess, from the outside, whether that company sponsors visas for engineering
roles specifically (not just "sponsors visas somewhere in the org") and whether
it's currently in a hiring-capable funding position. `top_job_titles_sponsored`
and `Approval_Rate` in the 80-Days CSV make the first fact visible; funding
stage/date make the second visible. Neither is discoverable by reading a job
posting or a careers page.

## Engine layers used

**80 Days to Stay** (`data/80-days-to-stay/80-days-csv/mapped_student_employment_targets_v3.csv`)
supplies both the funding and sponsorship evidence — this recipe reads one
already-joined CSV rather than performing a fresh join. **The Cognitive Pivot**
(`data/bls/compact/soc_occupation_compact.csv`) supplies role-quality context
(median wage, `cognitive_pivot_score`) — read and reported, but not scored,
since `role-scorer.mjs` currently gives role_quality zero weight.

## Where it fits the 3-3-2 day

This recipe automates company-level triage — a large share of the "2" research
hours, specifically the part spent manually cross-checking "does this company
even sponsor roles like mine" one tab at a time. Estimate (labeled as an
estimate, not a record): filtering 386 candidate companies down from 30,369 by
hand, at even 30 seconds per company to check funding + sponsorship + title
fit, would be roughly 3+ hours; this recipe does it in under a minute, leaving
the saved research time for actually reading the ~55 Apply-tier results in
depth. It feeds the credibility "3" only indirectly, by freeing time rather
than being the credibility artifact itself; the prototype and its tests are
what demonstrate judgment for that hour, per the assignment's own framing.

## Domain-specific failure modes

1. **Company-level sponsorship mistaken for role-level sponsorship.** A
   company can have a strong `Approval_Rate` driven entirely by, say, finance
   or sales roles, with zero history of sponsoring engineering titles. A
   student skimming only the Apply list — without reading the
   `skipped_no_title_match` count this recipe reports — would never notice
   this exclusion was even happening, and might independently (wrongly)
   assume "no match" means "no sponsorship," when it actually means "sponsors,
   just not this kind of role." The person hardest-placed to catch this is
   exactly the target user: someone new to reading H-1B/sponsorship data who
   doesn't yet know company-level and role-level evidence are different
   claims.
2. **An unverified-liveness Apply recommendation read as action-ready.** As
   found in this run (see `TEST-REPORT.md`), the sample-mode liveness
   placeholder doesn't act as a real gate, so 55 companies reach "Apply" on
   funding + sponsorship evidence alone, with posting reality never actually
   checked. A student under OPT time pressure, seeing "Apply," could
   reasonably skip the fine print and spend hours tailoring an application to
   a ghost posting. Hardest to catch: anyone reading only the top-line
   Apply/Consider/Skip counts rather than the per-role `liveness.source` field.
