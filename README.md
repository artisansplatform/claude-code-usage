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
| Discover features you're not using yet | Plan-mode and delegation adoption, slash-command breadth - each gap comes with a concrete "try this" |
| Spend tokens where they count | Context hygiene (below): how big your conversation was when you sent each prompt, prompts into 200K+ conversations, cold resumes, subagent vs main-thread tokens, and a price-weighted cost mix |
| Turn friction into guardrails | Friction themes with `encoded` / `recurring` / `new` labels; `encoded` means you turned a lesson into a CLAUDE.md rule, skill, or hook - the strongest growth signal in the report |
| See your foundation compound | Per-project CLAUDE.md size/freshness, custom skills, commands, hooks, memory files - the assets that make every future session faster |
| Understand your rhythm | Active days, heavy/light days, peak hours, delegation %, machine-time vs your-time - useful for protecting focus and for spotting unsustainable stretches |
| Keep yourself and the team safe | A safety checklist (see below) that surfaces small things worth tidying before they become incidents |

### Context hygiene: where the tokens go

Every step Claude takes re-sends the whole conversation, so conversation length, not the number of prompts, drives token use: on API price ratios about 70% of our token cost is re-reading cached conversation context, ~20% writing it to the cache and ~10% generated output (which is also why a cache-read share near 100% says nothing about efficiency: everyone has it). The report shows how big your conversation typically was when you sent a message (guideline: under 150K tokens), how many prompts went into a conversation already over 200K, and how many "cold resumes" re-opened a large session after an hour or more away, which re-processes the whole conversation because the cache has expired. The habit that fixes this is small: start a new session (`/clear` or `/new`) whenever you switch task, and `/resume` only to continue the same piece of work.

### Ground rules (read this first, especially if you're reading as manager or HR)

- **This is a growth tool, not an evaluation tool.** Reports are for 1:1 coaching conversations and for sharing good patterns across the team - never for ranking people or performance scoring.
- These are proxies from tool logs. Real work quality lives in code review and shipped outcomes.
- High usage is NOT the goal; leverage is. Someone who ships more with fewer, better prompts should look *better* in this report, not worse - that is why prompt quality, outcomes, and delegation matter more than raw volume.
- Any metric that becomes a target gets gamed (Goodhart's law). Keep reports self-generated and self-reviewed, and change the rubric only deliberately (it invalidates trends).
- Per machine, CLI only: claude.ai web sessions and second machines are not counted.
- Transcript retention defaults to 30 days; the skill snapshots each month so your trends survive. Set `cleanupPeriodDays` to 45+ in `~/.claude/settings.json` (the report reminds you if needed).

## Security & privacy stance

As we all use AI tools more, we look out for each other: one pasted credential or one unvetted plugin can cost the whole team. The safety checklist in the report is a shared habit, like code review - items on it are things to tidy together, not marks against anyone.

- Everything here is open code: ~1,600 lines of stdlib Python plus two markdown skills. Audit it before installing; hold every other plugin/skill/MCP server we adopt to the same bar. The report's inventory tables exist so we all notice new tooling early.
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
6. Optional: if your `git config user.name` is a handle (e.g. `jdoe42`), put your full name on the first line of `~/.claude/usage-reports/member.txt` so the report and zip carry it (see "Your name on the report" below).

### Every month, first week (~10 minutes)

1. Update the plugin so you're running the current collector - third-party marketplaces do not auto-update by default, so this one is on you. In your terminal:
   ```
   claude plugin update usage-report@artisans-tools
   ```
   Restart Claude Code afterwards to load it. Note there is no `/plugin update` slash command: in-session, `/plugin marketplace update artisans-tools` only refreshes the catalog listing, it does not update your installed copy. To make this automatic from next month on, run `/plugin` -> **Marketplaces** -> `artisans-tools` -> **Enable auto-update**.
2. Run `/insights` (a few minutes; enriches your report).
3. Run `/usage-report`. It asks ONE question right at the start (the privacy toggle), then runs on its own for about 8-10 minutes - you can walk away after answering. Use your normal default model (Opus or Sonnet class; skip Haiku for this one, the scoring quality matters). A full run costs roughly one medium coding session of quota (~35k output tokens), so any day you can code, you can run it.
4. Open `~/.claude/usage-reports/report-<month>.md` and read it - it's yours. Check the Examples section before sharing.
5. Send `<Member>-<Month>-<Year>.zip` to HR - a zip of just your `report-<month>.md` and `report-<month>.json`, written next to them in `~/.claude/usage-reports/`.

That's it. Optionally run `/usage-pulse` any week for a private 1-minute pulse (never shared; also feeds your "vs last week" line).

### Office holidays (`holidays.txt`)

`holidays.txt` in the plugin root lists office holidays, one `YYYY-MM-DD` per line (`#` comments and blank lines are fine). HR / the plugin owner maintains it in this repo; members receive it with the monthly plugin update (step 1 above), so nobody edits a local copy. A Mon-Fri holiday is left out of the workday count, so it never shows as an inactive day and never lowers usage %; working on one counts with weekend days. For a one-off run the collector also takes `--holidays <file>` instead.

### Your name on the report (`member.txt`)

The report and the zip name use, in order: the `CCUR_MEMBER` environment variable, the first non-empty line of `~/.claude/usage-reports/member.txt`, `git config --global user.name`, then your OS user name. The shared JSON records which one was used (`member_source`).

### For HR / admin

- Put everyone's zip for the month in one folder and run `python3 manager/aggregate.py <folder>` for the team snapshot - it reads the `.json` out of each zip (skipping copies under `snapshots/`), and still accepts loose `.json` files. One row per member and month; team totals and the number of old-schema rows are printed under the table. Use it per the ground rules above: spot shared training needs, celebrate wins.
- The shared `report-<month>.json` has a fixed schema (version 2.0): it is the collector's `shared.json`, in which the collector fills every number and the skill fills only the `llm` block (category mix, prompt score, learning themes, deltas) and the self-reported retention answer, without adding, renaming or removing keys. `aggregate.py` reads it by fixed paths. Reports made before 0.2.0 (free-form JSON) still load best-effort and are marked `old schema`; their token and context columns stay empty because those numbers are not comparable.
- `holidays.txt` is yours to maintain (see above): add the coming month's office holidays before members run their reports, and push it with a `version` bump in `.claude-plugin/plugin.json` so `claude plugin update` picks it up.
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

The collector (`bin/ccur-collect`) parses `~/.claude` files that Anthropic documents as internal and version-unstable. It skips anything it does not recognize, so it degrades rather than breaks; still, expect small updates after major Claude Code releases. Bump `collector_version` when definitions change, and note it in reports (trend breaks must be visible). Members pick those updates up via step 1 of the monthly routine above, so mention any change that shifts a number in the release notes.

### 0.2.0 trend break

Collector 0.2.0 changes what some numbers mean, so compare months across the 0.1.x -> 0.2.0 boundary with care (the report says so in its Trends section):

- Prompt, token and tool counts now include only records whose timestamp falls inside the month. 0.1.x counted every session that overlapped the month in full, so a session resumed across two months counted in both.
- Subagent tokens (`~/.claude/projects/<project>/<session>/subagents/`) are now read and counted separately from main-thread tokens; 0.1.x did not read them at all.
- Context metrics (conversation size per step and per prompt, long-context prompts, cold resumes, cost mix) are new, and the cache-read ratio is gone.
- Usage % excludes office holidays from the workday count, and the collector (not the skill) decides whether a month is partial.

## License

MIT - see [LICENSE](LICENSE).
