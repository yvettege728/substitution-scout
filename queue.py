#!/usr/bin/env python3
"""Keep the queue honest after a run.

Two jobs, both done by the wrapper and never by an agent:

  1. Write back status. A run that reached a decision changes what is open, and
     nothing else updates queue.md, so the planner kept choosing the same item
     twice in a row while believing it was choosing the deepest unknown.
  2. Open new cells. When the planner's split test says one item serves more
     than one occasion, each new cell becomes its own queue row, because the
     cell and not the item is the unit of substitution.

Usage: queue.py <label>
"""
import json, re, sys
from pathlib import Path

ACCEPTING = {"accept", "accepted"}
CLOSING = ACCEPTING | {"no_purchase"}


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def jsonl(path):
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def decisions_for(label):
    p = Path("decisions.md")
    if not p.exists():
        return []
    out = []
    for line in p.read_text().splitlines():
        if f"| run: {label} " not in line:
            continue
        parts = [x.strip() for x in line.split("|")]
        item = next((x[5:].strip() for x in parts if x.startswith("item:")), None)
        verdict = next((x.lower() for x in parts if x.lower() in CLOSING | {"reject", "rejected", "ask"}), None)
        if item and verdict:
            out.append((item, verdict))
    return out


def main(label):
    q = Path("queue.md")
    if not q.exists():
        print("QUEUE: queue.md missing, nothing to do")
        return 0
    lines = q.read_text().splitlines()
    plans = [p for p in jsonl("plans.jsonl") if p.get("run") == label]
    decs = decisions_for(label)
    changed = []

    # 1. status write-back for the item this run worked
    if plans and decs:
        item = plans[-1].get("item", "")
        verdicts = {v for i, v in decs if norm(i) == norm(item)} or {v for _, v in decs}
        if verdicts & ACCEPTING:
            new = "settled"
        elif "no_purchase" in verdicts:
            new = "settled"
        elif "ask" in verdicts:
            new = "parked"
        else:
            new = "open"
        for n, line in enumerate(lines):
            if not line.startswith("|") or norm(item) not in norm(line):
                continue
            cells = line.split("|")
            if len(cells) < 4 or norm(cells[2]) in ("status", ""):
                continue
            was = cells[2].strip()
            if was != new:
                cells[2] = f" {new} "
                lines[n] = "|".join(cells)
                changed.append(f"{item}: {was} -> {new}")
            break

    # 2. open a row per new cell when the split test fired
    for p in plans:
        for cell in p.get("split_cells", []) or []:
            label_text = str(cell).strip()
            if not label_text or any(norm(label_text) in norm(l) for l in lines):
                continue
            lines.append(f"| {label_text} | open | opened by the split test in run {label} |")
            changed.append(f"new cell: {label_text}")

    if changed:
        q.write_text("\n".join(lines) + "\n")
    for c in changed:
        print(f"QUEUE {c}")
    print(f"QUEUE: {len(changed)} change(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
