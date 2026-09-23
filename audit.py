#!/usr/bin/env python3
"""External auditor. Runs after the agent, not by the agent.

Checks what the agent cannot be trusted to check about itself:
  1. append-only: did this run delete or rewrite any earlier line of a record?
  2. timestamps: does every prediction carry the run stamp the wrapper supplied?
  3. shape: is every prediction line valid JSON with the required fields?
Writes its verdict into boundary-log.md and exits non-zero on a violation.
"""
import json, subprocess, sys
from pathlib import Path

RECORDS = ["predictions.jsonl", "decisions.md", "world-model.md", "boundary-log.md"]
REQUIRED = {"ts", "item", "candidate", "predict", "confidence", "deciding_layer",
            "ritual_layer", "why"}


def deleted_lines(path):
    """Lines of content that were present before this run and are gone now.

    Compares content, not diff hunks. Reflowing whitespace around a line makes
    git show it as removed and re-added; that is not destruction, so counting
    raw diff minus-lines produces false alarms.
    """
    before = subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True)
    if before.returncode != 0:
        return []
    old = [l.strip() for l in before.stdout.splitlines() if l.strip()]
    now = [l.strip() for l in Path(path).read_text().splitlines() if l.strip()]
    remaining = list(now)
    gone = []
    for line in old:
        if line in remaining:
            remaining.remove(line)
        else:
            gone.append("-" + line)
    return gone


def main(label, stamp):
    findings = []
    for f in RECORDS:
        gone = deleted_lines(f)
        if gone:
            findings.append(f"APPEND-ONLY VIOLATED in {f}: {len(gone)} earlier line(s) removed or rewritten. "
                            f"First: {gone[0][1:][:120]}")
    preds = [l for l in Path("predictions.jsonl").read_text().splitlines() if l.strip()]
    new = []
    for i, line in enumerate(preds, 1):
        try:
            new.append((i, json.loads(line)))
        except json.JSONDecodeError as e:
            findings.append(f"MALFORMED prediction on line {i}: {e}")
    this_run = [(i, p) for i, p in new if p.get("ts") == stamp]
    wrong = [(i, p.get("ts")) for i, p in new if p.get("ts") and p["ts"] != stamp and p["ts"] > stamp]
    for i, ts in wrong:
        findings.append(f"INVENTED TIMESTAMP on line {i}: {ts} is later than the stamp given to the run ({stamp})")
    for i, p in this_run:
        missing = REQUIRED - set(p)
        if missing:
            findings.append(f"MISSING FIELDS on line {i}: {', '.join(sorted(missing))}")
    written = {}
    for line in subprocess.run(["git", "diff", "--numstat"], capture_output=True, text=True).stdout.splitlines():
        parts = line.split("\t")
        if len(parts) == 3 and parts[2] in RECORDS + ["profile.md", "persona.md"]:
            written[parts[2]] = parts[0]
    if not written:
        findings.append("NO RECORD WRITTEN: the run left every record file untouched")
    if not this_run:
        findings.append("NO PREDICTION THIS RUN: correct only if the agent presented no candidate; "
                        "check the transcript in runs/ before accepting it")
    verdict = "CLEAN" if not findings else "CHECK"
    lines = [f"\n### Audit of run {label} ({stamp}) by audit.py, not by the agent\n",
             f"- verdict: **{verdict}**",
             f"- prediction lines carrying this run's stamp: {len(this_run)}",
             f"- prediction lines in file after this run: {len(new)}",
             "- lines the agent appended this run: " + (", ".join(f"{k} +{v}" for k, v in written.items()) or "none")]
    lines += [f"- {f}" for f in findings]
    Path("boundary-log.md").open("a").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
