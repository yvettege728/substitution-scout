#!/usr/bin/env python3
"""External auditor. Runs after the agents, not by them, and writes a verdict
they cannot edit.

Since v4 the agents have no write access to any record, so the interesting
question changed. It used to be "did it rewrite its own history". It is now
"did it try", plus "did the wrapper faithfully write what it was given".

Checks:
  1. custody: did any record file change while an agent was running?
  2. refusals: did the ledger reject anything the agent emitted?
  3. plan: did this run produce a plan before it produced candidates?
  4. coverage: did every candidate that reached a decision have a prediction?
  5. append-only: did anything earlier in a record file get removed?
  6. stamps: does every record from this run carry the wrapper's stamp?
  7. shape: are the prediction records complete?
  8. boundary: did the judge record where it chose to ask or decide?
"""
import json, subprocess, sys
from pathlib import Path

RECORDS = ["predictions.jsonl", "decisions.md", "world-model.md", "boundary-log.md",
           "plans.jsonl", "scores.jsonl", "proposals.md", "shopping-list.md"]
REQUIRED = {"ts", "item", "candidate", "predict", "confidence", "deciding_layer",
            "ritual_layer", "why"}


def read_jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for i, line in enumerate(p.read_text().splitlines(), 1):
        line = line.strip()
        if line:
            try:
                out.append((i, json.loads(line)))
            except json.JSONDecodeError as e:
                out.append((i, {"__bad__": str(e)}))
    return out


def deleted_lines(path):
    """Content present before this run and gone now. Compares multisets of
    lines, not diff hunks, so reflowed whitespace is not reported as loss."""
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
            gone.append(line)
    return gone


def main(label, stamp):
    findings, notes = [], []

    # 1. custody
    v = Path(f".custody/{label}.violations")
    if v.exists():
        for line in v.read_text().splitlines():
            if line.strip():
                findings.append(f"CUSTODY: {line.strip()}")
    else:
        notes.append("custody: no record file changed while an agent was running")

    # 2. ledger refusals
    led = Path(f"runs/{label}.ledger.txt")
    wrote = refused = 0
    if led.exists():
        for line in led.read_text().splitlines():
            if line.startswith("LEDGER REFUSED"):
                findings.append(line.replace("LEDGER REFUSED", "LEDGER REFUSED A RECORD:", 1))
                refused += 1
            elif line.startswith("LEDGER WROTE"):
                wrote += 1
    notes.append(f"ledger: {wrote} record(s) written by the wrapper, {refused} refused")

    # 3. plan
    plans = [p for _, p in read_jsonl("plans.jsonl") if p.get("run") == label]
    if not plans:
        findings.append("NO PLAN: this run produced no plan record, so nothing states what it "
                        "set out to do or when it meant to stop")
    else:
        item = plans[-1].get("item", "?")
        notes.append(f"plan: worked '{item}', stop condition "
                     f"{'stated' if plans[-1].get('stop_when') else 'MISSING'}")
        if not plans[-1].get("stop_when"):
            findings.append("PLAN WITHOUT A STOP CONDITION: the planner did not say when to "
                            "stop and ask, so the boundary was never its own to hold")

    # 4, 6, 7. predictions
    preds = read_jsonl("predictions.jsonl")
    bad = [i for i, p in preds if "__bad__" in p]
    for i in bad:
        findings.append(f"MALFORMED prediction on line {i}")
    mine = [(i, p) for i, p in preds if p.get("run") == label]
    for i, p in mine:
        if p.get("ts") != stamp:
            findings.append(f"STAMP MISMATCH on prediction line {i}: {p.get('ts')} is not the "
                            f"stamp given to this run ({stamp})")
        missing = REQUIRED - set(p)
        if missing:
            findings.append(f"MISSING FIELDS on prediction line {i}: {', '.join(sorted(missing))}")

    decided = [l for l in Path("decisions.md").read_text().splitlines() if f"run: {label} " in l]
    if len(decided) > len(mine):
        findings.append(f"COVERAGE: {len(decided)} candidate(s) reached a decision but only "
                        f"{len(mine)} prediction(s) were written this run. A candidate judged "
                        f"without a prior prediction cannot be scored.")
    notes.append(f"this run: {len(mine)} prediction(s), {len(decided)} decision(s)")

    # 5. append-only
    for f in RECORDS:
        if not Path(f).exists():
            continue
        gone = deleted_lines(f)
        if gone:
            findings.append(f"APPEND-ONLY VIOLATED in {f}: {len(gone)} earlier line(s) removed. "
                            f"First: {gone[0][:110]}")

    # 8. boundary
    if not any(f"run: {label} " in l for l in Path("boundary-log.md").read_text().splitlines()):
        findings.append("NO BOUNDARY RECORD: the judge never said where it chose to ask rather "
                        "than decide, which is the one thing it is supposed to own")

    # 9. the world model has to move, or the run learned nothing
    if decided and not any(f"run: {label} " in l
                           for l in Path("world-model.md").read_text().splitlines()):
        findings.append("WORLD MODEL UNCHANGED: the run reached decisions but added, revised or "
                        "retired no hypothesis. A run that decides without learning is a lookup.")

    # 10. an accepted candidate that produces no action is a decision nobody can act on
    accepted = [l for l in decided if "| accept |" in l or "| accepted |" in l]
    if accepted:
        acts = Path("shopping-list.md")
        have = acts.exists() and any(f"run {label}" in l for l in acts.read_text().splitlines())
        if not have:
            findings.append(f"NO ACTION: {len(accepted)} candidate(s) accepted but nothing was "
                            f"written to the shopping list, so the decision leads nowhere.")

    # 11. the scoring has to be independent of the bet
    cands = Path("stage/judge/candidates.md")
    leak = ("```ledger", '"predict"', '"confidence"')
    if cands.exists() and any(s in cands.read_text() for s in leak):
        findings.append("SCORE CONTAMINATED: the judge was shown the scout's predictions, so any "
                        "hit rate from this run measures agreement, not accuracy.")

    verdict = "CLEAN" if not findings else "CHECK"
    out = [f"\n### Audit of run {label} ({stamp}) by audit.py, not by any agent\n",
           f"- verdict: **{verdict}**"]
    out += [f"- {n}" for n in notes]
    out += [f"- {f}" for f in findings]
    Path("boundary-log.md").open("a").write("\n".join(out) + "\n")
    print("\n".join(out))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
