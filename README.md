# usage-report - your monthly Claude Code growth report

Claude Code is a skill, and skills grow fastest with a mirror. This plugin gives each of us a personal, self-generated monthly report: what you built with Claude, how your prompting is leveling up, which habits are compounding, and one or two concrete things to try next month. Sharing it lets the team learn from each other's best patterns and lets us invest in the right training and tooling.

Two slash commands, installed as one plugin:

- `/usage-report` (monthly): your full growth report - wins, prompt-craft score with trends, category mix, and next-month suggestions. Written to `~/.claude/usage-reports/`, reviewed by YOU, then shared.
- `/usage-pulse` (weekly): 1-minute private pulse, just for you. Nothing shared.

Everything runs on your machine against your local Claude Code data (`~/.claude`). Nothing is uploaded by the tooling; you always see exactly what leaves your machine, and the only place work content can appear is one redacted "Examples" section that you review first.

## What it tracks, and how each signal helps you

| What you get | Signals in the report |
|---|---|
| See your prompt craft grow | Prompt Quality Score (5-dim rubric, fixed anchors so the trend is real), plus your strongest prompts called out as patterns worth repeating |
| Watch progress month over month | Deltas on everything; outcomes mix (fully/partially achieved, from Anthropic's own session facets); commits/pushes made in sessions |
| Discover features you're not using yet | Plan-mode and delegation adoption, slash-command breadth, cache-read ratio - each gap comes with a concrete "try this" |
| Turn friction into guardrails | Friction themes with `encoded` / `recurring` / `new` labels; `encoded` means you turned a lesson into a CLAUDE.md rule, skill, or hook - the strongest growth signal in the report |
| See your foundation compound | Per-project CLAUDE.md size/freshness, custom skills, commands, hooks, memory files - the assets that make every future session faster |
| Understand your rhythm | Active days, heavy/light days, peak hours, delegation %, machine-time vs your-time - useful for protecting focus and for spotting unsustainable stretches |
| Keep yourself and the team safe | A safety checklist (see below) that surfaces small things worth tidying before they become incidents |

### Ground rules (read this first, especially if you're reading as manager or HR)

- **This is a growth tool, not an evaluation tool.** Reports are for 1:1 coaching conversations and for sharing good patterns across the team - never for ranking people or performance scoring.
- These are proxies from tool logs. Real work quality lives in code review and shipped outcomes.
- High usage is NOT the goal; leverage is. Someone who ships more with fewer, better prompts should look *better* in this report, not worse - that is why prompt quality, outcomes, and delegation matter more than raw volume.
- Any metric that becomes a target gets gamed (Goodhart's law). Keep reports self-generated and self-reviewed, and change the rubric only deliberately (it invalidates trends).
- Per machine, CLI only: claude.ai web sessions and second machines are not counted.
- Transcript retention defaults to 30 days; the skill snapshots each month so your trends survive. Set `cleanupPeriodDays` to 45+ in `~/.claude/settings.json` (the report reminds you if needed).

## Security & privacy stance

As we all use AI tools more, we look out for each other: one pasted credential or one unvetted plugin can cost the whole team. The safety checklist in the report is a shared habit, like code review - items on it are things to tidy together, not marks against anyone.

- Everything here is open code: ~500 lines of stdlib Python plus two markdown skills. Audit it before installing; hold every other plugin/skill/MCP server we adopt to the same bar. The report's inventory tables exist so we all notice new tooling early.
- The "Help improve Claude" (training/retention) toggle lives in the claude.ai account, not on disk, so the report records a dated self-attestation instead of pretending to verify it. Org-managed accounts (Team/Enterprise) make this a non-issue: training is off by default and retention is admin-controlled.
- Hosting: a private repo requires every member to have read access (org membership or a team) before `/plugin marketplace add` works. Public is acceptable for THIS repo because it contains only generic tooling, but never commit reports, member names, or marketplace settings with internal URLs into a public repo.

## Steps

### One-time setup (5 minutes)

1. In any Claude Code session, add the marketplace:
   ```
   /plugin marketplace add artisansplatform/claude-code-usage
   ```
2. Install the plugin:
   ```
   /plugin install usage-report@artisans-tools
   ```
3. In `~/.claude/settings.json`, add `"cleanupPeriodDays": 60` (keeps a full month of history so your report is complete).
4. At claude.ai -> Settings -> Privacy, turn OFF "Help improve Claude".

### Every month, first week (~10 minutes)

1. Run `/insights` (takes a few minutes; enriches your report).
2. Run `/usage-report`.
3. Open `~/.claude/usage-reports/report-<month>.md` and read it - it's yours. Check the Examples section before sharing.
4. Send `report-<month>.md` and `report-<month>.json` to HR.

That's it. Optionally run `/usage-pulse` any week for a private 1-minute pulse (never shared; also feeds your "vs last week" line).

### For HR / admin

- Put everyone's `.json` for the month in one folder and run `python3 manager/aggregate.py <folder>` for the team snapshot. Use it per the ground rules above: spot shared training needs, celebrate wins.
- Optional: auto-prompt installation for everyone by adding to a shared repo's checked-in `.claude/settings.json`:
  ```json
  {
    "extraKnownMarketplaces": {
      "artisans-tools": { "source": { "source": "github", "repo": "artisansplatform/claude-code-usage" } }
    },
    "enabledPlugins": { "usage-report@artisans-tools": true }
  }
  ```
- Requirement on each machine: `python3` on PATH (stdlib only).

## Complementary org-level options (no member action needed)

- **Claude Code Analytics API** (Console/API orgs, Admin API key): per-user daily sessions, lines of code added/removed, commits, PRs, per-tool accept/reject, tokens and cost. Ground truth for volume; no behavioral depth.
- **OpenTelemetry** (`CLAUDE_CODE_ENABLE_TELEMETRY=1` + an OTLP collector): live dashboards for sessions, LoC, cost, active time, tool accept/reject.

This plugin covers what those cannot: prompt quality, categories, friction/learning, and the foundation-building signals.

## Maintenance

The collector (`bin/ccur-collect`) parses `~/.claude` files that Anthropic documents as internal and version-unstable. It skips anything it does not recognize, so it degrades rather than breaks; still, expect small updates after major Claude Code releases. Bump `collector_version` when definitions change, and note it in reports (trend breaks must be visible).

## License

MIT - see [LICENSE](LICENSE).
