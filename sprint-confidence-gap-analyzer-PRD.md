# Sprint Confidence Gap Analyzer — Product Requirements Document

**Author:** Asha Veerpaneni — Program Manager / Scrum Master
**Status:** Draft v1
**Last updated:** August 16, 2026

## 1. Problem Statement
Engineers frequently report confidence that a card will be done 2-3 days before sprint close, yet cards still roll over — driven by meetings, unexpected dependencies, and code review delays that only surface in daily standups, after it's too late to react. This project identifies the gap between reported engineering confidence and implementation reality, using objective, PR-derived signals, rolled up into per-card and program-wide status — across all 3 teams' currently active sprints, with a plain-English reason for every flagged item.

## 2. Goals
1. **Learning goal:** Apply the same PRD-first, story-by-story build discipline used on the first two projects to a new domain — PR/code-review data — while learning to connect multiple mock datasets into one coherent program view.
2. **Career goal:** A third standalone portfolio project, directly solving a real problem experienced on the job, and the first that deliberately ties the first two projects' concepts together into a single "program health" story.
3. **Practical goal:** Give a PM objective, git-derived signals for sprint risk 2-3+ days before sprint close, with a clear explanation of *why* something is flagged, instead of relying on self-reported engineer confidence.

## 3. Users
- **Primary user:** Program Manager (you) — reviews per-card and program-level status and decides what to act on.
- **Secondary stakeholder:** Engineers/reviewers — indirectly benefit from earlier, evidence-based flagging instead of last-minute standup surprises; this tool is not intended to evaluate individual performance.

## 4. Design Decisions Carried From Planning

**4.1 — Mock data for v1, real GitHub API explicitly deferred.** No real PR-based workflow exists yet in the first two repos (they were built with direct commits, no feature-branch/PR history), and even if they did, two solo-built repos wouldn't provide the variety this tool needs. v1 uses a purpose-built mock dataset. Real GitHub API integration is deferred to v2.

**4.2 — No cost beyond the existing Claude Pro subscription.** No separate Anthropic API key, no autonomous paid API calls in v1. This explicitly includes the reasoning feature (US-13) — reasons are generated from rule-based flag logic already computed by the tool, not an LLM call, so this feature adds zero cost. If more polished prose is ever wanted, that can be done interactively via Claude Code (covered under Pro), but is not required for the feature to work.

**4.3 — Size is a risk signal, not a time estimate.** Lines-changed and files-touched bucket PR complexity as Small/Medium/Large, feeding status logic as one factor among several — not a predicted review duration.

**4.4 — PR splitting is a suggestion, not an automation.** The tool outputs a text suggestion when a Large PR is at risk; it never attempts to split code automatically.

**4.5 — Shared mock data lives in its own dedicated repo, not embedded in this project.** Unlike the first two projects — which intentionally stayed fully independent so they could be showcased as separate LinkedIn posts, and remain untouched by this decision — this project's data comes from a new, separate repo (`pm-portfolio-mock-data`) containing `teams.json`, `cards.json`, `risks.json`, and `prs.json`. These reuse the **same fictional card IDs** from the Sprint Planning Automator (e.g. `ALPHA-202`) and the **same fictional risk IDs** from the RAID Log Automator (e.g. `R-001`), so the "which card is at risk and why" story connects across all three projects. This is a **copy-based reuse strategy, not a live dependency**: no git submodule, no runtime network call. The relevant JSON files are copied directly into this project's folder before building, same as any other file. If the shared data changes later, it's manually re-copied — a deliberate simplicity trade-off, chosen over a submodule, given the current stage of the portfolio. Any future project can reuse the same shared repo the same way.

## 5. Data Schema

**Features** (new — sits above Cards, groups related work across one or more teams):
| Field | Notes |
|---|---|
| feature_id | e.g. FEAT-01 |
| feature_name, description | |
| owner | Typically a Product Owner |
| linked_team_ids | Teams contributing to this feature — supports features that span more than one team |
| linked_card_ids | Cards that make up this feature |

**Teams** (extends the Sprint Planning Automator's team model, with a new field):
| Field | Notes |
|---|---|
| team_id, team_name | Same as Sprint Planning Automator |
| active_sprint_id | Used to scope the report to Active sprints only (US-10) |
| product_owner | Same as Sprint Planning Automator |
| **engineers** | **New** — a short roster of 2 fictional engineer names per team, added specifically for this project since the original mock data only tracked team-level info, not individual contributors. Used as PR reviewers (US-12). |

**Cards** (extends the Sprint Planning Automator's card schema):
| Field | Notes |
|---|---|
| card_id, team_id, sprint_id, title, priority, story_points, status | Same as Sprint Planning Automator, reusing the same card IDs |
| feature_id | **New** — links this card to the feature it belongs to |
| linked_pr_id | **New** — links this card to a PR entry |
| linked_risk_ids | **New** — list of RAID-style risk IDs (reusing entries from the RAID Log Automator) relevant to this specific card |

**PRs:**
| Field | Notes |
|---|---|
| pr_id, linked_card_id | |
| state | Draft / Open / Closed / Merged |
| created_date, last_updated_date, merged_date | |
| lines_added, lines_deleted, files_changed | Feeds size bucket |
| size_bucket | Calculated — Small/Medium/Large, configurable thresholds |
| reviewers | List of `{reviewer_name, review_status, last_action_date}` — reviewer_name drawn from the linked card's team engineer roster |
| required_approvals | Configurable |
| round2_diff, round2_size_bucket | Same bucket logic applied to post-review rework |
| mergeable, mergeable_state | Conflict detection |
| ci_checks_status | pass / fail / pending |
| sonarqube_coverage_pct, sonarqube_quality_gate | Mocked; failing gate is a hard override to Red |

**Linked Risks** (reused/extended from RAID Log Automator entries):
| Field | Notes |
|---|---|
| risk_id, category, description | Same as RAID Log Automator, reusing relevant entries (e.g. `R-001`) |
| priority (calculated bucket) | Same Probability x Impact logic as the RAID project |
| owner, status | |

## 6. Scope

### In scope (v1)
- Consolidated mock dataset covering Teams (with engineer rosters), Cards, PRs, and Linked Risks, connecting all three per Section 4.5 and 5
- **Scoped to Active sprints only, across all 3 teams** — cards in closed/future sprints are excluded from the report (US-10)
- Calculate PR size bucket (Small/Medium/Large), configurable thresholds (US-1)
- Track per-reviewer review status and approvals received vs. required, reviewers drawn from each team's engineer roster (US-2, US-12)
- Flag reviews sitting "Pending" past a configurable duration (US-3)
- Calculate a Round 2 size bucket from post-review rework (US-4)
- Pull merge-conflict status from mergeable state (US-5)
- Mock SonarQube coverage/quality gate; failing gate forces Red regardless of other signals (US-6)
- Combine PR signals **and any linked RAID risk items** into one documented, rules-based status per card (US-7, US-11)
- **Plain-English reasoning for every Amber/Red card**, generated from the same rule flags already computed — zero additional cost (US-13)
- Team-level and **Program-level rollup across all 3 teams' active sprints**, with reasoning for the overall Program status (US-8, US-14)
- **Feature-level rollup**, so risk is visible at the "what are we shipping" level, not just per-card or per-team (US-15)
- Text-only suggestion to consider splitting a PR when Large and at risk — never automated (US-9)
- Manually triggered by the PM, runs from the terminal (CLI), no GUI required for v1

### Out of scope (v1)
- Real GitHub/GitLab/Bitbucket API integration (see 4.1)
- Real SonarQube API integration (mocked only)
- Automated PR splitting (see 4.4)
- Predicting exact review completion time in hours (see 4.3)
- Any runtime file dependency on the Sprint Planning Automator or RAID Log Automator repos (see 4.5) — this project carries its own copies of relevant entries instead

### Possible v2
- Real GitHub API integration via a free Personal Access Token
- Real SonarQube API integration
- Historical calibration once real cycle-time data exists

## 7. User Stories & Acceptance Criteria

**US-1:** As a PM, I want each PR's lines changed and files touched converted into a configurable size bucket, so I have an objective complexity signal.
- *Acceptance:* Thresholds supplied at runtime; every PR receives a bucket; defaults documented if none supplied.

**US-2:** As a PM, I want each reviewer's status and approvals-received-vs-required tracked per PR, so I know exactly where review stands.
- *Acceptance:* Per-PR output lists each reviewer's status; flags PRs below required approval count.

**US-3:** As a PM, I want reviews sitting "Pending" too long flagged separately from rework delays.
- *Acceptance:* Pending duration calculated from request date to current date; flagged past a configurable threshold.

**US-4:** As a PM, I want post-review rework bucketed with the same size logic as PR size.
- *Acceptance:* Round 2 diff bucketed Small/Medium/Large; a Large bucket flagged as elevated risk.

**US-5:** As a PM, I want merge-conflict status pulled directly from mergeable state.
- *Acceptance:* "Dirty" or "blocked" mergeable state flagged as a hard risk factor.

**US-6:** As a PM, I want mock SonarQube data with a failing quality gate forcing Red regardless of other signals.
- *Acceptance:* Any PR with a failing quality gate is automatically Red, overriding all other signals.

**US-7:** As a PM, I want each card's overall status calculated from combined PR **and linked risk** signals, so I get one clear status per card.
- *Acceptance:* Status logic is documented explicitly: any hard-fail signal (failing quality gate, merge conflict, an associated High-priority open Risk/Issue) = Red; multiple soft-risk signals = Amber; clean across all signals = Green.

**US-8:** As a PM, I want a sprint-level rollup per team showing status counts and a list of at-risk cards with reasons.
- *Acceptance:* Output includes counts per status category per team, and named at-risk cards with reasons.

**US-9:** As a PM, I want a text suggestion — never an automated action — when a Large PR is at risk close to sprint end.
- *Acceptance:* Suggestion generated for qualifying PRs; no automated splitting action is ever taken.

**US-10:** As a PM, I want the report scoped only to cards within each team's currently Active sprint, so status reflects what's happening right now.
- *Acceptance:* Cards in non-Active sprints are excluded from all status and rollup calculations; the tool confirms which sprint (by ID) was treated as Active per team.

**US-11:** As a PM, I want each card linked to its PR and any relevant RAID risk items, so I see the full picture of what's putting a card at risk, not PR data alone.
- *Acceptance:* A card with a linked open High-priority Risk or Issue is flagged even if its own PR signals look clean; the link is shown explicitly in output.

**US-12:** As a PM, I want reviewers assigned from each team's own engineer roster, so review status maps back to realistic team ownership.
- *Acceptance:* Every PR's reviewers are drawn from the linked card's team's engineer list, not an arbitrary name.

**US-13:** As a PM, I want a plain-English reasoning list for every Amber/Red card and for the overall Program status, generated at no additional cost.
- *Acceptance:* Every Amber/Red card lists the specific flags that caused its status (e.g. "Quality gate failed: 82% coverage, threshold 90%"; "No reviewer response in 3 days"). Reasoning is produced via rule-based text generation from already-computed flags — verified to require no Anthropic API key to run (see 4.2).

**US-14:** As a PM, I want a Program-level status calculated across all 3 teams' active sprints, so I can report overall program health, not just per-team.
- *Acceptance:* Program status = Red if any team has 1+ Red cards; Amber if any team has Amber cards but no Red; Green only if all teams are clean. Reasoning for the Program status names which team(s) and card(s) are driving it.

**US-15:** As a PM, I want each feature's status calculated from the status of its linked cards, so I can see which features are at risk, not just which individual cards.
- *Acceptance:* A feature's status follows the same "worst card wins" logic as Program status (Red if any linked card is Red, Amber if any is Amber with no Red, Green only if all linked cards are Green). Reasoning names which card(s) are driving an at-risk feature's status. A feature with only one linked card (e.g. FEAT-02) simply inherits that card's status and reasoning directly.

## 8. Non-Functional Requirements
- **Performance:** Process the full mock dataset (~20-50 cards/PRs across 3 teams) in under 5 seconds.
- **Cost:** Zero dependency on a paid Anthropic API key or autonomous API calls, including the reasoning feature — see Section 4.2.
- **Data connection:** Reuses card/risk IDs from the first two projects for narrative consistency, without a runtime file dependency on either repo — see Section 4.5.
- **Usability:** Status and reasoning must be understandable by a non-technical stakeholder without reading code.
- **Reliability:** Must handle the edge cases in Section 9 without crashing.

## 9. Risks & Edge Cases
- PR has no reviewers assigned yet → flagged as "review not requested," not an error.
- A PR is Approved, then new commits pushed afterward → flagged as needing re-review.
- Mixed reviewer statuses → "Changes Requested" takes precedence; PR treated as blocked.
- Missing SonarQube data → flagged "quality gate unknown," never assumed to pass.
- Card has no linked PR yet (work not started) → flagged distinctly from "PR exists but at risk."
- Card has a linked risk that's since been Closed in the RAID data → excluded from active risk flagging.
- A team has no Active sprint in the mock data → that team excluded from the Program rollup, flagged explicitly rather than silently ignored.

## 10. Success Metrics
- 100% of PRs with a failing quality gate correctly forced to Red.
- 100% of cards with a linked open High-priority Risk/Issue correctly flagged, even with clean PR signals.
- Status classification matches expected outcome for every designed test scenario in the mock data.
- Program-level rollup correctly reflects the worst-status team in 100% of test scenarios.
- Feature-level rollup correctly reflects the worst-status linked card in 100% of test scenarios.
- Reasoning output present for 100% of Amber/Red cards and the Program status.
- Zero paid API calls required to run the core script.

## 11. Technical Approach (initial)
- Mock data copied from the separate `pm-portfolio-mock-data` repo (`teams.json`, `cards.json`, `risks.json`, `prs.json`) into this project's folder — see Section 4.5. Not a live dependency; a one-time copy per build.
- Core logic built and tested as a terminal/CLI Python script, run through Claude Code under the existing Pro subscription.
- Manually triggered by the PM, no scheduled/background execution in v1.
- Git used from the first commit, pushed to its own public GitHub repo (e.g. `sprint-confidence-gap-analyzer`), cross-linked in READMEs to the other two projects and to `pm-portfolio-mock-data`.
- No external network calls required to run the core script in v1.

## 12. Definition of Done (v1)
- Script runs end-to-end against the mock dataset, scoped to Active sprints across all 3 teams, producing card-level, feature-level, team-level, and Program-level status with reasoning.
- All 15 user stories pass their acceptance criteria.
- README documents the problem, the real on-the-job scenario that motivated it, the data-connection design decision (Section 4.5), and how to run it with no API key required.
- Code is committed incrementally to its own public GitHub repo with a clear history.
