#!/usr/bin/env bash
# One documented command: build roles.json from the real 80-Days CSV, then
# score it with the repo's existing scorer (not reimplemented).
# Run from the repo root.
set -euo pipefail

HERE="scripts/contrib/2026fa/iyashsaraf-swe-ai-devops-sponsor-triage"
OUT_DIR="$HERE/run"

python3 "$HERE/build_roles.py" \
  --out-dir "$OUT_DIR" \
  --opt-end-date 2027-03-15

npm run score -- "$OUT_DIR/roles.json" --out-dir "$OUT_DIR"
