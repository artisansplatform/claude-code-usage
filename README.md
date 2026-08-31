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

## Production safety baseline (recommended for everyone)

Team goal: the assistant must never be able to do something unrecoverable or production-affecting without a human in the loop. Auto mode is fine for day-to-day work as long as this fence is in place. Setup step 4 installs this for you; here is what it adds to `~/.claude/settings.json` (deny always wins over allow, whatever mode you are in):

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf:*)", "Bash(git push --force:*)", "Bash(git push -f:*)",
      "Bash(git reset --hard:*)", "Bash(git clean:*)", "Bash(sudo:*)",
      "Bash(terraform apply:*)", "Bash(terraform destroy:*)",
      "Bash(kubectl apply:*)", "Bash(kubectl delete:*)",
      "Bash(aws s3 rm:*)", "Bash(aws s3api delete:*)",
      "Bash(docker system prune:*)", "Bash(docker compose down -v:*)",
      "Read(./.env)", "Read(./.env.*)", "Read(**/*.pem)"
    ]
  }
}
```

The monthly report checks this: it lists any allow-rule that could push, delete, deploy, or mutate a database without asking, shows your deny-rules and PreToolUse guard hooks, and reports how many sessions ran in `auto` vs `bypassPermissions` mode.

Honest limit: deny-rules match command prefixes, so a script, a Makefile target, or `bash -c "..."` can still wrap a dangerous command. The durable protection is environmental: no production credentials on dev machines, and production deploys only through CI with a human approval step. For org-wide enforcement that members cannot override, the same `permissions.deny` block goes in managed settings (`/etc/claude-code/managed-settings.json` on Linux).

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
   When the dialog asks for a scope, pick **"Install for you (user scope)"** so the commands work in all your repos, not just the current one.
3. Run this in your terminal (keeps six months of session history so your reports and trends stay complete; it only raises the value, never lowers it):
   ```
   python3 -c "import json,pathlib;p=pathlib.Path.home()/'.claude/settings.json';d=json.loads(p.read_text() or '{}') if p.exists() else {};d['cleanupPeriodDays']=max(180,int(d.get('cleanupPeriodDays') or 0));p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2));print('cleanupPeriodDays =',d['cleanupPeriodDays'])"
   ```
4. Install the production-safety baseline (adds the deny-rules listed above; keeps everything else in your settings as is; safe to re-run):
   ```
   python3 -c "import json,pathlib;p=pathlib.Path.home()/\".claude/settings.json\";d=json.loads(p.read_text() or \"{}\") if p.exists() else {};perm=d.setdefault(\"permissions\",{});deny=perm.setdefault(\"deny\",[]);base=[\"Bash(rm -rf:*)\",\"Bash(git push --force:*)\",\"Bash(git push -f:*)\",\"Bash(git reset --hard:*)\",\"Bash(git clean:*)\",\"Bash(sudo:*)\",\"Bash(terraform apply:*)\",\"Bash(terraform destroy:*)\",\"Bash(kubectl apply:*)\",\"Bash(kubectl delete:*)\",\"Bash(aws s3 rm:*)\",\"Bash(aws s3api delete:*)\",\"Bash(docker system prune:*)\",\"Bash(docker compose down -v:*)\",\"Read(./.env)\",\"Read(./.env.*)\",\"Read(**/*.pem)\"];added=[r for r in base if r not in deny];deny.extend(added);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2));print(\"deny rules added:\",len(added),\"| total deny:\",len(deny))"
   ```
5. At claude.ai -> Settings -> Privacy, turn OFF "Help improve Claude".

### Every month, first week (~10 minutes)

1. Run `/insights` (a few minutes; enriches your report).
2. Run `/usage-report`. It asks ONE question right at the start (the privacy toggle), then runs on its own for about 8-10 minutes - you can walk away after answering. Use your normal default model (Opus or Sonnet class; skip Haiku for this one, the scoring quality matters). A full run costs roughly one medium coding session of quota (~35k output tokens), so any day you can code, you can run it.
3. Open `~/.claude/usage-reports/report-<month>.md` and read it - it's yours. Check the Examples section before sharing.
4. Send `<Member>-<Month>-<Year>.zip` to HR - a zip of just your `report-<month>.md` and `report-<month>.json`, written next to them in `~/.claude/usage-reports/`.

That's it. Optionally run `/usage-pulse` any week for a private 1-minute pulse (never shared; also feeds your "vs last week" line).

### For HR / admin

- Put everyone's zip for the month in one folder and run `python3 manager/aggregate.py <folder>` for the team snapshot - it reads the `.json` out of each zip, and still accepts loose `.json` files. Use it per the ground rules above: spot shared training needs, celebrate wins.
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
