# Sprint Confidence Gap Analyzer

A CLI tool that replaces self-reported "I'm confident this card will be done" standup
updates with objective, PR-derived signals — rolled up into per-card, per-feature,
per-team, and program-wide status, with a plain-English reason for every flagged item.

## The problem

Engineers frequently report confidence that a card will be done 2-3 days before sprint
close, yet cards still roll over — driven by meetings, unexpected dependencies, and code
review delays that only surface in daily standups, after it's too late to react. This
project identifies the gap between reported engineering confidence and implementation
reality, using objective signals pulled from PR/code-review data (size, review status,
merge conflicts, quality gates) and linked RAID risks, instead of relying on how confident
an engineer *feels*.

It's built around a real on-the-job scenario: a Program Manager reviewing three teams'
active sprints wants to know, today, which cards are actually at risk and *why* — not
find out in the last standup before sprint close.

## What it does

For every card in each team's currently **Active** sprint, the tool:

1. Buckets the linked PR's size (Small/Medium/Large) from lines changed and files touched.
2. Tracks reviewer status, approvals-vs-required, and how long a review has sat Pending.
3. Buckets any post-review "round 2" rework the same way.
4. Pulls merge-conflict status directly from the PR's mergeable state.
5. Applies a mocked SonarQube quality gate — a failing gate forces the card Red,
   overriding every other signal.
6. Resolves the card's linked RAID-style risks — an active High-priority Risk/Issue
   flags the card Red even if its PR looks clean.
7. Combines all of the above into one Red/Amber/Green status per card, with a
   plain-English reasons list generated from the same rule-based flags (no LLM call,
   zero additional cost).
8. Rolls that up to team, program, and feature level, each following the same
   "worst status wins" logic and naming which team/card is driving it.

See [`sprint-confidence-gap-analyzer-PRD.md`](sprint-confidence-gap-analyzer-PRD.md) for
the full spec — data schema, all 15 user stories with acceptance criteria, and the edge
cases the tool is expected to handle without crashing.

## How the data connects

This is the third in a series of portfolio projects, and the first that deliberately ties
the earlier two together into one "program health" story:

- **Card IDs** (e.g. `ALPHA-202`) are the same ones used in the **Sprint Planning
  Automator**.
- **Risk IDs** (e.g. `R-001`) are the same ones used in the **RAID Log Automator**.

Rather than a live dependency between repos, the connected dataset
(`teams.json`, `features.json`, `cards.json`, `risks.json`, `prs.json`) lives in a
separate `pm-portfolio-mock-data` repo and is **copied** into this project's `data/`
folder before building — no git submodule, no runtime network call. If the shared data
changes, it's manually re-copied. See `shared-mock-data-README.md` for details on that
repo, and Section 4.5 of the PRD for the reasoning behind this trade-off.

## Running it

No API key, no paid dependency, no network call — everything runs against the local
mock data with the Python standard library.

```bash
python3 cli.py
```

Useful flags:

```bash
# Evaluate the report as of a specific date instead of today
python3 cli.py --as-of 2026-08-16

# Every threshold used in the status logic is configurable at runtime;
# see all of them (and their documented defaults) with:
python3 cli.py --help
```

### Running the tests

```bash
python3 -m pytest
```

74 tests cover every module, including full end-to-end runs against the real mock
dataset (not just synthetic fixtures) so the whole pipeline — data loading through
card/team/program/feature status — is verified against the actual scenario the mock
data was designed around.

## Dashboard

[`dashboard/confidence-gap-dashboard.html`](dashboard/confidence-gap-dashboard.html) is a
self-contained, single-file dashboard view of the same report the CLI prints — open it
directly in a browser, no server or build step required. It's evaluated 2 days before
sprint close (matching the PRD's own "2-3 days before sprint close" framing) and answers
the tool's core question visually: of the cards marked "In Progress" on the board, how
many actually carry a Red or Amber signal underneath?

It covers Program status, a per-team breakdown with each at-risk card's PR size and
specific reasons, and a full board-status-vs-signal comparison table for every card.

The page's data is a static snapshot, embedded at build time — not live. To refresh it
after a mock data change:

```bash
python3 dashboard/generate_data.py   # rewrites dashboard/dashboard_data.json
```

then paste the (minified) output into the `<script id="dashboard-data" type="application/json">`
block in `confidence-gap-dashboard.html`.

## Project structure

```
sprint-confidence-gap-analyzer/
├── data/                       # copied from pm-portfolio-mock-data (see above)
├── dashboard/
│   ├── confidence-gap-dashboard.html  # self-contained dashboard (see below)
│   ├── dashboard_data.json            # data snapshot embedded in the page above
│   └── generate_data.py               # rebuilds dashboard_data.json from the report pipeline
├── src/sprint_confidence/
│   ├── models.py                # Team, Sprint, Card, Feature, PR, Reviewer, Risk
│   ├── config.py                # all configurable thresholds, with documented defaults
│   ├── loader.py                # reads the 5 JSON files into the models above
│   ├── dates.py                 # shared ISO date parsing
│   ├── sprint_scope.py           # US-10: scope cards to each team's Active sprint
│   ├── sizing.py                 # US-1, US-4: PR / round-2 size buckets
│   ├── review_status.py          # US-2, US-3, US-12: reviewer & approval tracking
│   ├── pr_signals.py             # US-5, US-6, US-9: merge conflicts, quality gate, PR-split suggestion
│   ├── risk_linking.py           # US-11: linked RAID risk resolution
│   ├── card_status.py            # US-7, US-13: card-level Red/Amber/Green + reasoning
│   ├── rollup.py                 # US-8, US-14, US-15: team / program / feature rollups
│   └── report.py                 # wires everything together into the printable report
├── cli.py                        # entry point
└── tests/                        # one test module per source module above
```

## Related projects

- **Sprint Planning Automator** — original source of the card IDs reused here.
- **RAID Log Automator** — original source of the risk IDs reused here.
- **pm-portfolio-mock-data** — the shared, copy-based mock dataset this project's
  `data/` folder is copied from.
