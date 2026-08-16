# Shared Mock Data

Canonical mock data reused across portfolio projects, starting with the **Sprint Confidence Gap Analyzer**. This exists so future projects don't each reinvent their own version of teams, cards, risks, and PRs from scratch.

## What's here

- `teams.json` — 3 teams, each with a product owner, a short engineer roster, and an active sprint ID
- `features.json` — 4 features, each grouping one or more cards, for feature-level risk rollup
- `cards.json` — sprints and cards, reusing the same card IDs originally created for the **Sprint Planning Automator**, extended with `linked_pr_id`, `linked_risk_ids`, and `feature_id`
- `risks.json` — RAID-style risk entries, reusing the same risk IDs originally created for the **RAID Log Automator**, extended with `linked_card_id`
- `prs.json` — pull request data linking to cards, with reviewers drawn from each team's engineer roster

## How this relates to the first two projects

`sprint-planning-automator` and `raid-log-automator` are **untouched and fully independent** — they keep their own separate mock data files, exactly as originally built, and don't reference this repo in any way.

This repo exists specifically because the third project (Confidence Gap Analyzer) needed to connect cards, risks, and PRs into one program-level view. Rather than duplicating that connected dataset inside that project's own repo, it lives here so any future project can reuse it too.

## How to use this in a project

This is **not** a live dependency — no submodule, no runtime network call. Copy the file(s) you need directly into your project folder before building:

```
cp teams.json features.json cards.json risks.json prs.json /path/to/your-project-folder/
```

If you only need part of it (e.g. just `cards.json` for a project that doesn't touch PRs or risks), copy only that file. Each file is self-contained and doesn't require the others to be present, except where `linked_*_id` fields reference IDs that live in another file — if you copy `cards.json` alone, the `linked_pr_id` and `linked_risk_ids` fields will simply point to IDs that don't resolve locally, which is fine as long as your project doesn't need to follow those links.

## If this data changes

Since this is copy-based, not live-linked: update the files here first, then manually re-copy into any project that needs the update. There's no automatic sync — that's a deliberate simplicity trade-off over using a git submodule.
