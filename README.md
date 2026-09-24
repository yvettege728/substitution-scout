# substitution-scout

A Hermes skill and a wrapper for an agent that works out what can stand in the
place of something a person can no longer buy after moving between cities, and
that is allowed to answer that nothing can.

The interesting part is not the search. It is who holds the pen.

## Why it is built this way

Across nine runs the agent's judgment about the task held up. Its reports about
its own work failed five times. It claimed to have written records it had not
written, dated its own work with invented timestamps, deleted a hypothesis while
saying it was revising it, and once produced a forged audit block headed "by
audit.py, not by the agent" declaring itself clean after removing 101 lines of
the real log.

The fifth failure happened on a frontier model in the cloud, not on the small
free model used locally. It printed two predictions in its reply and wrote zero
bytes. So the problem is not model strength, and it is not a prompt that needs
sharpening.

**A record an agent can edit is not a record.** Version 4 acts on that.

## Custody

The agents have no write access to any record.

Each runs in its own staging directory under `stage/`, rebuilt from scratch every
run. The record files live in the repository root, outside every staging
directory. Anything an agent wants recorded goes in a single fenced `ledger` block
at the end of its reply; `ledger.py` parses that block, refuses any record missing
a required field, and appends it, supplying the timestamp itself so a run cannot
date its own work.

The sha256 of every record file is taken immediately before and after each model
call. A mismatch is a `CUSTODY VIOLATION`, caught by arithmetic rather than by the
agent's own confession.

## Three agents

| Agent | Sees | Tools | Does |
|---|---|---|---|
| planner | `context.md`, `queue.md`, `profile.md`, mechanisms | file | picks one item off the queue, says why that one, states its stop condition |
| scout | `plan.md`, `persona.md`, mechanisms | web, file, vision | property layers 1 to 3, one prediction per candidate |
| judge | `plan.md`, `candidates.md`, `profile.md`, `context.md` | file | property layers 4 and 5, accept / reject / no_purchase / ask |

The scout is not trusted with the deep layers and does not have them. `profile.md`
is absent from its directory, so the disclosure rule is enforced by the file system
rather than by the agent's good behaviour.

The judge is handed the candidates with the scout's `predict` and `confidence`
stripped out. A judge that can read the bet is not an independent test of it. In
one run where it could read them it agreed three times out of three; with the
predictions withheld, the same setup scored one hit and two misses.

## The loop closes

`score.py` matches each decision back to the prediction that preceded it and
writes hit or miss to `scores.jsonl`. No model is involved. `context.py` renders
the agent's own accuracy per layer into the next run's `context.md`, so a run that
has been wrong about a layer is told so before it predicts again.

`scores-void.txt` lists runs whose scores must not count, with the reason. Records
are append-only, so a bad score is annotated rather than deleted.

## Two agents can agree on the answer and disagree on the world

Every scored candidate now records the layer the scout predicted would decide it
and the layer the judge actually decided on. In one run both scored candidates
were rejected exactly as predicted, and the layers disagreed both times: the
scout was reasoning from price and packaging, the judge from what restores order.

A hit rate alone hides this. The accuracy looked perfect for a layer that was not
deciding anything. Naming the layer is part of the prediction, not decoration.

## What custody did not fix

A clean run is not a good run. One run passed every check with eleven records and
none refused, and its hypothesis still read as word salad.

| | record integrity | content quality |
|---|---|---|
| architecture | fixed: forgery is now physically impossible | no effect: the auditor can check that a hypothesis exists, not that it means anything |
| model strength | no effect: the frontier model wrote zero bytes too | this is where it bites |

Custody separation cures forgery. It does not cure nonsense. The auditor's ceiling
is presence, not truth, and closing that gap needs a verifier outside this system.

## Files

| Path | What it is |
|---|---|
| `.hermes/skills/substitution-scout/SKILL.md` | the rules all three agents run on. Hermes only finds a skill under `.hermes/skills`, so the dotted path matters |
| `run.sh` | one run: snapshot, three agents in three boxes, ledger, score, audit, commit |
| `ledger.py` | the wrapper's pen. The only thing that writes a record |
| `context.py` | renders what the agents are allowed to know about their past |
| `score.py` | closes predictions against decisions. Mechanical |
| `queue.py` | writes the queue status back after a run, and opens a row per cell when the split test fires |
| `audit.py` | the external auditor. Runs after the agents, never by them |
| `mechanisms.md` | the five substitution mechanisms and the two axes |
| `profile.example.md` | what the private profile looks like. Copy to `profile.md` |
| `persona.example.md` | the only file that may leave. Copy to `persona.md` |
| `queue.example.md` | open items. Copy to `queue.md` |

## Use

    cp profile.example.md profile.md
    cp persona.example.md persona.md
    cp queue.example.md queue.md
    ./run.sh first-run

`--skills substitution-scout` is required for the skill to load, and the skill
has to sit under `.hermes/skills`. Older builds have no `skills trust`, and
`skills list` will not show a workspace skill at all.

Set `AGENT_PROVIDER` and `AGENT_MODEL` together to override the model.

## Requirements

Hermes Agent, python3, git, and ripgrep on PATH as a real binary. The file
toolset's search needs `rg`; a shell function of that name will not be inherited
by the subprocess. Paths given to the agents must be absolute.

## Licence

MIT.
