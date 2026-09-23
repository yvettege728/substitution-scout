#!/bin/bash
# One run of the substitution scout, with a clock it cannot fake and an audit it cannot write.
# Usage: ./run.sh <label> "<task>"
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
LABEL="$1"; TASK="$2"
STAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
D="$PWD"
git add -A && git \
  commit -q -m "before run $LABEL" --allow-empty
printf '\n---\n## Run %s (%s)\n\n' "$LABEL" "$STAMP" >> boundary-log.md
hermes --in "$D" --skills substitution-scout -t web,file,skills,vision -z "Current time: $STAMP. Run label: $LABEL. Use the substitution-scout skill; it holds the rules. The workspace is $D and all its files are there. $TASK" \
  2>&1 | tee "runs/$LABEL.md"
python3 audit.py "$LABEL" "$STAMP" || echo "AUDIT FOUND VIOLATIONS (recorded, not fatal)"
git add -A && git \
  commit -q -m "run $LABEL"
echo "--- run $LABEL done, stamp $STAMP"
