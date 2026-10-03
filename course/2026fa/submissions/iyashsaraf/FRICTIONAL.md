# FRICTIONAL — honest log

## Executive summary

This logs what I actually tried, what Claude (the AI agent) actually did, where
the two diverged, and what's still unresolved — written as the honesty rule
requires: distinguishing my work from the AI's, not blending them into one
voice.

## What I tried and what happened

I started by pasting the full assignment brief to Claude and asking what it
was and how to do it. Claude read it back to me in its own structured summary
before anything was built — I used that to confirm I understood the shape of
the deliverable correctly (recipe + card + prototype + tests + writeups + PR).

I had not yet forked the repo at that point. Claude asked directly whether I
had, and when I said no (I'd only cloned the main repo), it told me I needed a
real fork — not a copy — because the assignment requires pushing to my own
namespace and opening a PR from it, not pushing to the instructor's repo
directly. I forked it myself via github.com and renamed the local folder; I
confirmed the rename to Claude mid-task, which it picked up and re-verified
(checked `git remote -v` itself rather than taking my word for it).

I made the actual domain decision: MS Software Engineering student, SWE/AI/
DevOps roles, H-1B focus. When asked to narrow it further, I picked the
"sponsorship + funding filter" angle over "OPT countdown" or "cognitive-fit"
when given the choice — I wanted the recipe to use the engine's central
data join rather than a narrower slice. I also picked the placeholder OPT
date (2027-03-15) and the slug name.

## What I checked, changed, or learned in response

I didn't write any of the Python or Markdown myself in this session — Claude
did the file-level work (reading the CSV/scorer/recipe-style files, writing
`build_roles.py`, the fixture, the test, the recipe, the card, and the
reports). What I did do: approved the plan before any `recipes/`/`data/`
edits happened (the repo's own `CLAUDE.md` requires plan-mode for that, and
Claude followed it without being told to), asked what two shell commands did
before approving them rather than blindly accepting, and asked where the
`TEST-REPORT.md` would actually live when I lost track of it mid-session.

**Unresolved question I still have:** whether the 45-day hiring-lag assumption
in the timeline gate is realistic for H-1B-sponsoring tech employers
specifically, versus a generic number. I haven't independently verified this
against any outside source yet — it's disclosed as an assumption in the
recipe and prototype output, not presented as researched.

## Explicit human/AI contributions

- **Mine:** the domain, the recipe angle choice, the OPT-date placeholder and
  slug, approving the fork/branch setup, reading and confirming the plan
  before implementation, catching that I needed to ask what a bash command did
  before running it.
- **Claude's:** all repo exploration (recipe style conventions, data shapes,
  the scorer's actual gate-default behavior), all file authorship
  (`build_roles.py`, the test, the fixture, the recipe + card, run.sh,
  README, TEST-REPORT, worked run, this file), running every command and
  reporting real output, and surfacing the Skip-rate finding in the worked run
  unprompted — I didn't notice that discrepancy myself; Claude's own
  `TEST-REPORT.md` draft flagged it before I read the scored output closely
  enough to have caught it myself.
- **What I accepted as-is:** the recipe/card structure (I don't have a basis
  to second-guess SNICKERDOODLE-style recipe conventions I'd never seen
  before this assignment), the keyword list for SWE/AI/DevOps titles.
- **What I'd want to revisit before calling this VERIFIED (not just
  RUNNABLE-SAMPLE):** the liveness-placeholder behavior named in the worked
  run's "next improvement" — I agree with the proposed fix but haven't
  implemented or tested it myself.

## Traceability

- This session's conversation is the record of the back-and-forth described
  above.
- `course/2026fa/submissions/iyashsaraf/CHANGE-BRIEF.md` — predictions written
  before the build, with a dated Revisions section added after the real run
  (not edited into the original text).
- `logs/runs/2026fa-iyashsaraf-1.md` — the run-log entry for the real sample
  run.
- `course/2026fa/submissions/iyashsaraf/TEST-REPORT.md` and `WORKED-RUN.md` —
  every command run and its real output.
