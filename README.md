# substitution-scout

A Hermes skill for deciding what can stand in the place of something a person
can no longer buy after moving between cities, plus the wrapper and the external
auditor that keep it honest.

Written for MAS.665J, MIT AI Studio, Fall 2026.

## The idea

Grocery systems match substitutes on size, brand, name and embedding distance.
People do not. A substitute is judged on two axes at once.

**Five property layers**, what the thing is: material, sign, economic,
relational, and order and trust.

**Six ritual layers**, which step of the practice broke: search, acquisition,
possession, use, sharing, divestment.

A candidate can match on material and fail on order. Which layer decides differs
by item, and at the start of a run nobody knows which one it is, so the agent has
to find out before it proposes anything.

Three rules follow from that:

- **Predict before you propose.** Each candidate gets a prediction line written
  to an append-only log before the candidate is shown, so the reasoning is on
  record before the answer is.
- **Ask at the deepest unknown layer**, not the easiest one. A question about
  shipping is cheap; it is rarely the real question.
- **"Do not buy" is a valid answer.** If what was lost is a practice rather than
  a product, the agent has to say so. That answer never appears in a system owned
  by sellers.

## Why the auditor exists

Over nine runs on a small free model, the agent invented timestamps and cited
them as proof of ordering, claimed to have appended records during a run in which
it wrote zero bytes, deleted an audit log and wrote a forged one in its place, and
replaced a hypothesis it claimed to be revising. Its judgment about the task held
up; its account of its own actions did not.

So `audit.py` runs after the agent and outside it. It compares the working tree
against git by content rather than by diff hunks, checks that every prediction
carries the clock reading the wrapper supplied, and reports what the run actually
wrote. It has blind spots of its own, and they are documented in the code.

## Files

| Path | What it is |
|---|---|
| `skills/substitution-scout/SKILL.md` | the rules the agent runs on |
| `run.sh` | one run: git snapshot, a clock the agent cannot fake, the agent, then the audit |
| `audit.py` | the external auditor |
| `profile.example.md` | template for the private profile the skill reads |

## Use

Install [Hermes Agent](https://github.com/NousResearch/hermes-agent), copy the
skill into your project, then:

    ./run.sh <label> "<task>"

The skill has to be preloaded explicitly with `--skills substitution-scout`.
Trusting the project is not enough; the skill will be listed as enabled and still
not be in the session.

## Licence

MIT.
