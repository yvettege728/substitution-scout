#!/usr/bin/env python3
"""The wrapper's pen.

The agent never writes a record. It emits a fenced ```ledger block of JSON
lines in its reply. This module parses that block and appends the records to
the real files, injecting the timestamp itself so a run cannot date its own
work.

Usage: ledger.py <transcript> <label> <stamp>
Prints one line per record appended, and the count, for the auditor to read.
"""
import json, re, sys
from pathlib import Path

BLOCK = re.compile(r"```ledger\s*\n(.*?)```", re.S)

VERDICTS = {"accept", "accepted", "reject", "rejected", "no_purchase", "ask"}

# Fields a record is refused without. The agent's own summary of what it did is
# not evidence; an incomplete record is worse than a missing one, because it
# looks like a record.
NEEDED = {
    "plan": ["item", "why_this_item", "ritual_hypothesis", "stop_when"],
    "prediction": ["item", "candidate", "predict", "confidence", "deciding_layer",
                   "ritual_layer", "why"],
    "decision": ["item", "candidate", "verdict", "reason", "deciding_layer", "ritual_layer"],
    "hypothesis": ["text", "status", "evidence"],
    "boundary": ["moment", "went", "reason"],
    "profile_proposal": ["section", "wording"],
    "action": ["item", "candidate", "where"],
}


def check(rec):
    kind = rec.get("record")
    missing = [f for f in NEEDED.get(kind, []) if not str(rec.get(f, "")).strip()]
    if missing:
        raise ValueError(f"{kind} record is missing {', '.join(missing)}")


def parse(text):
    """Every ledger block in the transcript, as (line_no, dict) or (line_no, error)."""
    out = []
    for block in BLOCK.findall(text):
        for n, raw in enumerate(block.splitlines(), 1):
            raw = raw.strip()
            if not raw or raw.startswith("//"):
                continue
            try:
                out.append((n, json.loads(raw)))
            except json.JSONDecodeError as e:
                out.append((n, {"record": "__malformed__", "error": str(e), "raw": raw[:160]}))
    return out


def append(path, line):
    with Path(path).open("a") as f:
        f.write(line.rstrip("\n") + "\n")


def next_pred_id(label):
    """Sequence number for this run's predictions, counted from the file itself."""
    p = Path("predictions.jsonl")
    if not p.exists():
        return 1
    n = 0
    for line in p.read_text().splitlines():
        if f'"{label}#' in line:
            n += 1
    return n + 1


def route(rec, label, stamp):
    """Write one record. Returns (file, description) or raises ValueError."""
    kind = rec.get("record")
    if kind not in NEEDED:
        raise ValueError(f"unknown record type {kind!r}")
    check(rec)
    g = lambda k, d="": str(rec.get(k, d)).replace("\n", " ").strip()

    if kind == "plan":
        rec["ts"], rec["run"] = stamp, label
        append("plans.jsonl", json.dumps(rec, ensure_ascii=False))
        return "plans.jsonl", f"plan for {g('item')}"

    if kind == "prediction":
        rec["ts"], rec["run"] = stamp, label
        rec["id"] = f"{label}#{next_pred_id(label)}"
        append("predictions.jsonl", json.dumps(rec, ensure_ascii=False))
        return "predictions.jsonl", f"prediction on {g('candidate')} as {rec['id']}"

    if kind == "decision":
        v = g("verdict").lower()
        if v not in VERDICTS:
            raise ValueError(f"verdict must be one of {sorted(VERDICTS)}, got {v!r}")
        append("decisions.md",
               f"{stamp} | run: {label} | item: {g('item')} | candidate: {g('candidate')} | "
               f"{v} | reason: {g('reason')} | property layer decided: {g('deciding_layer')} | "
               f"ritual layer decided: {g('ritual_layer')}")
        return "decisions.md", f"{v} on {g('candidate')}"

    if kind == "hypothesis":
        append("world-model.md",
               f"{stamp} | run: {label} | hypothesis: {g('text')} | status: {g('status')} | "
               f"evidence: {g('evidence')}")
        return "world-model.md", f"hypothesis {g('status')}"

    if kind == "boundary":
        append("boundary-log.md",
               f"- {stamp} | run: {label} | moment: {g('moment')} | went: {g('went')} | "
               f"reason: {g('reason')}")
        return "boundary-log.md", f"boundary {g('went')}"

    if kind == "profile_proposal":
        append("proposals.md",
               f"\n- {stamp} | run: {label} | section: {g('section')}\n  proposed: {g('wording')}\n"
               f"  status: NOT APPLIED. profile.md is the person's to edit.")
        return "proposals.md", "profile edit proposed"

    if kind == "action":
        append("shopping-list.md",
               f"- [ ] {g('item')}: {g('candidate')} | where: {g('where')} | price: {g('price')} | "
               f"url: {g('url')} | recheck: {g('recheck')} | added {stamp} run {label}")
        return "shopping-list.md", f"action for {g('candidate')}"

    raise ValueError(f"unknown record type {kind!r}")


def main(transcript, label, stamp):
    text = Path(transcript).read_text(errors="replace")
    recs = parse(text)
    if not recs:
        print("LEDGER: no ledger block in the reply. Nothing written.")
        return 0
    written, refused = [], []
    for n, rec in recs:
        if rec.get("record") == "__malformed__":
            refused.append(f"line {n}: not JSON ({rec['error']}): {rec['raw']}")
            continue
        try:
            f, what = route(rec, label, stamp)
            written.append(f"{f}: {what}")
        except ValueError as e:
            refused.append(f"line {n}: {e}")
    for w in written:
        print(f"LEDGER WROTE  {w}")
    for r in refused:
        print(f"LEDGER REFUSED {r}")
    print(f"LEDGER: {len(written)} written, {len(refused)} refused")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
