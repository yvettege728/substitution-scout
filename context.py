#!/usr/bin/env python3
"""Build the agent's view of its own past, from records it cannot write.

The agent never reads the record files directly. Each run the wrapper renders
this summary into the staging directory: the open queue, what was decided, the
live hypotheses, and the agent's own hit rate per layer. Everything here is
derived, so nothing the agent does during a run can change what it will be
told next run.

Usage: context.py <staging-dir>
"""
import json, sys
from collections import defaultdict
from pathlib import Path

LAYERS = {"1": "material", "2": "sign", "3": "economic", "4": "relational",
          "5": "order and trust"}


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


def tail(path, n, structured=True):
    """Last n record lines. Records written by the wrapper all carry '| run: ';
    earlier free-form prose from the versions where the agent wrote its own
    records is skipped, because it cannot be parsed and should not be quoted
    back as if it were a record."""
    p = Path(path)
    if not p.exists():
        return []
    lines = [l.strip() for l in p.read_text().splitlines() if l.strip()]
    if structured:
        lines = [l for l in lines if "| run: " in l]
    return lines[-n:]


def void_runs():
    """Run labels whose scores must not count. Operator-maintained."""
    p = Path("scores-void.txt")
    if not p.exists():
        return set()
    out = set()
    for line in p.read_text().splitlines():
        line = line.rstrip()
        if line and not line.startswith("#") and not line.startswith(" "):
            out.add(line.split()[0])
    return out


def hit_rates():
    """Per deciding-layer accuracy, from scored predictions only, skipping any
    run whose score was voided."""
    void = void_runs()
    scores = [s for s in jsonl("scores.jsonl")
              if str(s.get("prediction_id", "")).split("#")[0] not in void]
    by = defaultdict(lambda: [0, 0])
    for s in scores:
        layer = str(s.get("deciding_layer", "?"))
        by[layer][1] += 1
        if s.get("outcome") == "hit":
            by[layer][0] += 1
    return by


def main(stage):
    preds = jsonl("predictions.jsonl")
    scored = {s.get("prediction_id") for s in jsonl("scores.jsonl")}
    open_preds = [p for p in preds if p.get("id") and p["id"] not in scored]

    out = ["# What is already known", "",
           "Rendered by the wrapper from the record files. You cannot write this",
           "file or the files behind it. Work from it as given.", ""]

    q = Path("queue.md")
    if q.exists():
        body = [l for l in q.read_text().strip().splitlines() if not l.startswith("# ")]
        out += ["## Open queue", ""] + body
    else:
        out += ["## Open queue", "", "(queue.md missing)"]

    out += ["", "## Your accuracy so far", ""]
    rates = hit_rates()
    if not rates:
        out.append("No prediction has been scored yet. Treat your confidence as untested.")
    else:
        out.append("| deciding layer | correct | scored | rate |")
        out.append("|---|---|---|---|")
        for k in sorted(rates):
            hit, tot = rates[k]
            name = LAYERS.get(k, k)
            out.append(f"| {k} {name} | {hit} | {tot} | {hit/tot:.0%} |")
        weak = [k for k in rates if rates[k][1] >= 2 and rates[k][0] / rates[k][1] < 0.7]
        out.append("")
        if weak:
            worst = min(weak, key=lambda k: rates[k][0] / rates[k][1])
            out.append(f"You are worst on layer {worst} ({LAYERS.get(worst, worst)}). Lower your "
                       "confidence there, or ask instead of predicting.")
        else:
            out.append("No layer is below 70% yet. That is a small sample, not a licence to "
                       "raise your confidence.")

    out += ["", f"## Predictions still open ({len(open_preds)})", ""]
    for p in open_preds[-8:]:
        out.append(f"- {p.get('candidate')} for {p.get('item')}: predicted {p.get('predict')} "
                   f"at {p.get('confidence')}, deciding layer {p.get('deciding_layer')}")
    if not open_preds:
        out.append("(none)")

    out += ["", "## Last decisions", ""]
    out += [f"- {l}" for l in tail("decisions.md", 6)] or ["(none)"]

    out += ["", "## Live hypotheses", ""]
    out += [f"- {l}" for l in tail("world-model.md", 6)] or ["(none)"]

    Path(stage, "context.md").write_text("\n".join(out) + "\n")
    print(f"context.md rendered: {len(open_preds)} open predictions, {len(rates)} scored layers")


if __name__ == "__main__":
    main(sys.argv[1])
