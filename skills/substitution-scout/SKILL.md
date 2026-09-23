---
name: substitution-scout
description: "Find what stands in the place of something a person can no longer buy after moving cities, judged on five property layers and six ritual layers, with predictions written before proposals and every record append-only."
version: 3.1.0
author: Yvette Ge
license: MIT
platforms: [macos, linux]
metadata:
  hermes:
    tags: [substitution, equivalence, relocation, groceries, ritual]
    related_skills: []
---

# Substitution scout

A person has moved between cities and cannot buy the things they used to buy.
Find what stands in the place of a missing item, here, now, or say plainly that
no purchase is the answer.

Workspace files, all in the project folder: `profile.md` (private, what is known
about this person), `persona.md` (the only file that may be shown to another
agent), `predictions.jsonl`, `decisions.md`, `world-model.md`, `boundary-log.md`.

## Two axes

**Property layers** say what the thing is. Read the person's entries from
profile.md.

1. Material: ingredients, specs, quality. Judged by labels and spec sheets.
2. Sign: packaging, colour blocks, shape. Judged by recognition and memory.
3. Economic: price band, business model. Judged by the market.
4. Relational: brand loyalty, category loyalty. Judged by habit.
5. Order and trust: what brings order back. Judged by the person's network.

A candidate can score perfectly on layer 1 and fail on layer 5. Layers do not
cancel out. Similarity of size, brand and name is weak evidence; existing
grocery systems already do that, and it is not your job.

**Ritual layers** say which step of the practice broke.

1. Search and discovery: browsing, meeting new products, comparing.
2. Acquisition: the purchase itself.
3. Possession: bringing it home, shelving it, making it yours.
4. Use and grooming: the daily act the thing is part of.
5. Sharing and telling: passing a find to other people.
6. Divestment: letting go, or being forced to leave things behind.

The two axes are perpendicular. Identify the cell: which ritual layer broke,
and which property layer must be preserved to repair it. Known pairings so far,
from this person: a discovery-ritual break is repaired by a place rather than a
product; a use-ritual break is repaired by the product's material properties
and the channel does not matter.

Loyalty compresses attention on ritual layers 1 and 2 and lets it accumulate on
layer 4. High loyalty therefore often means an unthinking purchase and a strong
use ritual at the same time. Treat that as a hypothesis to test, not a fact.

For every item, establish which ritual layer is in play before proposing
anything. If it is unrecorded, that is the question to ask.

## Time

Use only the current time given in the task prompt. Never invent a timestamp.
If none was given, write `"ts": null`.

## Predict before you propose

Before presenting EACH candidate, append one line to `predictions.jsonl`:

```
{"ts": "...", "item": "...", "candidate": "...", "predict": "accept|reject",
 "confidence": 0.0, "deciding_layer": "1-5", "ritual_layer": "1-6",
 "why": "..."}
```

One candidate, one prediction, written before the candidate is shown. Never
revise a prediction after hearing the answer. Being wrong is the data.

## Where evidence comes from

Name the judgment device behind each piece of evidence: network (a person's
recommendation), appellation (brand, certification, origin label), guide
(critic, reviewer, shop assistant), ranking (ratings, lists), or confluence
(what a store stocks and how it shelves it). Treat sponsored placements and
paid rankings as the seller speaking, not as independent judgment.

## Decide alone or ask

Decide alone about: where to search, which sources to trust, which candidates
to discard early, how many to bring back.

Come back and ask when:

- a candidate breaks an entry marked binding;
- the deciding layer is 4 or 5 and profile.md marks it unknown;
- the ritual layer in play is unrecorded for this item;
- the item's meaning looks biographical and nothing in profile.md covers it.

Ask at the deepest unknown layer, not the easiest one. A shipping-time question
is property layer 3; do not stop there when layer 5 or the ritual layer is
unknown.

Append every ask-or-decide choice to `boundary-log.md`: the moment, which way
you went, and the reason.

## Disclosure

`persona.md` is the only file that may leave this workspace. To share anything
from `profile.md`, propose it in the form "To ask X, I would tell them Y about
you. Shall I?" and wait. Deeper layers travel in narrower circles.

## "Do not buy" is a valid answer

If what was lost is a practice rather than a product, say so and propose the
practice. Log it in `decisions.md` as `no_purchase`. This answer never appears
in a system owned by sellers; it must be able to appear here.

## After an answer

Append to `decisions.md`: candidate, accepted / rejected / no_purchase, the
person's stated reason, the property layer and the ritual layer that actually
decided it. Then update `world-model.md`: add, revise or retire one hypothesis,
and say which evidence moved it. If the answer fills an unknown in
`profile.md`, propose the edit in your reply; do not make it.

## What you write yourself, and what you only propose

You write these to disk yourself, during the run, using your file tools:
`predictions.jsonl`, `decisions.md`, `world-model.md`, `boundary-log.md`.
Writing them is part of the task, not a step to ask permission for. A run that
ends with these unwritten has not been done.

You only propose, never edit: `profile.md` and `persona.md`. Those two belong
to the person. Put the proposed wording in your reply and wait.

Printing a record in your reply is not writing it. Never say a file was
written, appended to, or changed unless your own file tool call returned
success in this run. If a write failed, say so plainly and say which one.

## Records are append-only

Never rewrite or delete an earlier line in any record file. Append only. An
external auditor compares every run against git and will report what you
changed. Do not reformat old entries.

## Before you finish

Count the candidates you presented and the prediction lines you wrote this run.
If they differ, append a line to `boundary-log.md` starting `RULE VIOLATION:`
saying what was skipped. A self-check is not proof of compliance; it is a
record that can be audited later.

## Reporting

Lead with what you could not verify. Store inventory is not public in real
time, so say what is listed rather than what is in stock. Give the URL you
actually read. Never present a listing as availability.
