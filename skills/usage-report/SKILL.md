---
name: usage-report
description: Generate the user's personal monthly Claude Code growth report (wins, prompt-craft score, trends, and next-month suggestions), write it to ~/.claude/usage-reports/, and have them review the Examples section before sharing.
---

# Monthly growth report

You produce the user's personal growth report from their LOCAL Claude Code data. Nothing is uploaded; the user reviews the finished file and shares it themselves.

**Tone rules (apply to every sentence of the report):** write in second person ("you"), lead every section with what is going well, and frame every gap as a specific, small opportunity ("try adding a done-when line to your next brief") rather than a criticism. Never use scolding words (weak, poor, failure, violation, bad habit) in the report body; never compare the user to other people; celebrate month-over-month improvement explicitly wherever a delta is positive. The numbers themselves stay honest and unrounded - warmth in the words, accuracy in the figures.

**Month selection**: if the user passed an argument like `2026-08`, use that calendar month. Otherwise: today is day 1-7 of a month -> report the previous full month; else report the current month to date. Always pass the full calendar month (`--from <YYYY-MM-01> --to <last-day>`); the collector decides whether the window is partial (`window.partial`), so never label a report partial on your own.

## Step 1 - Ask the one question, then collect

FIRST, ask the data-retention question from Step 6c (one AskUserQuestion call). It is the run's only interaction; asking it up front means everything after runs unattended instead of blocking mid-run while the user is away.

Then run the bundled collector at `${CLAUDE_PLUGIN_ROOT}/bin/ccur-collect` (do not assume it is on PATH; on Windows prefix it with `py -3` or `python`):

```
${CLAUDE_PLUGIN_ROOT}/bin/ccur-collect --from <YYYY-MM-01> --to <last-day> --out <scratchpad>/ccur
```

Read `metrics.json` and `shared.json` fully (both in the `--out` folder). `shared.json` is the fixed-schema shared document: every deterministic number is already in it, and Step 9 ships it with only the `llm` fields and the attestation filled in. Read `sessions.jsonl` and `prompt_sample.jsonl` only as instructed below. NEVER read raw transcripts under `~/.claude/projects/` yourself; the collector already parsed them, and reading them would blow up cost.

If `rhythm.source` is `transcripts`, history.jsonl was empty or truncated (it held `rhythm.history_coverage_pct`% of the prompts the transcripts show), so the collector built the rhythm and the prompt sample from transcripts instead; say so in one line of the report header. If `sessions.count` is much lower than the rhythm implies (transcripts already cleaned up), say so too: token and context numbers then cover only the transcripts still on disk. If facet coverage is low (< 40%), note that running `/insights` first enriches category/outcome data, then continue with what exists.

## Step 2 - Deterministic sections

Use the numbers exactly as computed; the definitions live in `metrics.json.definitions` and must not be reinterpreted between months. Headline block (keep this exact shape; it is what managers compare across people and months). All fields are in `shared.json`; `N` is the length of `window.holidays_in_window`:

```
Monthly Usage: <headline.usage_pct>% (<headline.active_workdays>/<window.workdays_excl_holidays> workdays Mon-Fri, <N> holidays excluded)
Avg Daily Usage: <headline.avg_active_minutes_per_active_day, as hours and minutes>
Peak Day: <headline.peak_weekday> | Peak Hour: <headline.peak_hour_local, local>
Heavy / Light / Inactive days: <headline.heavy_days> / <headline.light_days> / <headline.inactive_workdays>
Weekend or holiday days worked: <headline.active_weekend_or_holiday_days>
Sessions: <headline.sessions> | Prompts: <headline.prompts_total> | Projects: <headline.distinct_projects>
```

Title the report "<Month> <Year>", plus "(partial month, data through <window.data_through>)" only when `window.partial` is true. When `headline.rhythm_source` is `transcripts`, add under the block: "Rhythm from transcripts (history.jsonl held <headline.history_coverage_pct>% of your prompts)."

## Step 3 - Category mix

Prefer facet `goal_categories` (Anthropic's own classifier). Map facet keys to the team taxonomy; put unmapped keys under the closest bucket or `other`:

| Team category | Facet keys (examples) |
|---|---|
| Coding | feature_implementation, bug_fixing, refactoring, testing, debugging |
| Code Review | code_review, pr_review |
| Documentation | documentation, writing |
| Research | research, learning, exploration, question_answering |
| Architecture | architecture, design, planning |
| SQL / Data | sql, data_analysis |
| DevOps | devops, ci_cd, tooling_setup, deployment, infrastructure |
| Other | anything else |

For sessions without facets, classify from `sessions.jsonl` (`first_prompt` + `top_tools` + project name), max 200 rows, in one pass. Report the mix as % of sessions, plus a Coding sub-mix (feature / bug fix / testing / refactor / optimization) from the same data. For Step 9 these become `llm.category_mix_pct` with exactly the keys `coding`, `code_review`, `documentation`, `research`, `architecture`, `sql_data`, `devops`, `other`, and `llm.coding_submix_pct` with exactly `feature`, `bug_fix`, `testing`, `refactor`, `optimization` (numbers, one decimal).

## Step 4 - Prompt Quality Score

Score TASK BRIEFS only: prompts marked `"brief": true` in `prompt_sample.jsonl` plus session `first_prompt`s from `sessions.jsonl` (skip empty and `<task-notification>` ones), up to 40 total spread across the month. Short mid-session follow-ups ("yes", "stage your changes") are NOT scored on this rubric; report their share of all prompts separately as conversational steering (a high share with low interruptions is a good sign, not a bad one). If fewer than 10 briefs exist, skip the score and write "insufficient sample".

Each brief gets 0-4 on five dimensions; the score is the mean over all briefs and dimensions, as a percentage of 4. Use these anchors EXACTLY (they must stay stable across months or the trend is meaningless):

| Dimension | 0 | 2 | 4 |
|---|---|---|---|
| Intent clarity | goal unguessable | goal stated, "done" fuzzy | goal + explicit done-state |
| Context given | none | some (file OR error OR constraint) | names files/errors/constraints precisely |
| Scope shaping | boil-the-ocean or one-word ask | roughly right-sized | right-sized, decomposed, or explicitly asks for a plan first |
| Leverage | ignores available machinery | some reuse of commands/skills | uses commands, skills, plan mode, images, or prior context aptly |
| Verifiability | no way to check | implies a check | asks for tests/evidence/verification |

Rules: judge the prompt as written, not the outcome. Score in one batch. Report overall %, per-dimension means, n, and note the dimension with the most headroom (call it "your biggest opportunity", with the expected payoff, e.g. fewer re-explains). For Step 9 this becomes `llm.prompt_quality` = `{"overall_pct", "n", "dimensions_pct": {"intent_clarity", "context_given", "scope_shaping", "leverage", "verifiability"}, "biggest_opportunity" (the dimension key), "steering_share_pct"}`; when the score is skipped, set `overall_pct` and `dimensions_pct` to null and keep `n`.

Hygiene: `metrics.json.hygiene` counts sampled prompts where credential-shaped strings were auto-masked. If > 0, add a safety-checklist item in Step 6b (count only; NEVER quote or describe the credential itself) suggesting env vars / `!` commands reading from files as the easy alternative to pasting secrets.

## Step 5 - Working style, leverage and context hygiene

From `shared.json`: `working_style` (interruptions per 100 prompts, tool error share, plan-mode session %, delegation session %, slash commands top 10, median response time if present), the model mix from `tokens.model_output_share_pct`, and token totals from `tokens.main` and `tokens.subagents` (label them "estimate"). One short paragraph naming the user's working style and the single habit that would raise their leverage most next month.

Then a required **Context hygiene** paragraph from `context_hygiene` and `tokens`, in this shape (field names below are under `context_hygiene` unless they start with `tokens.`; write token totals as millions with one decimal, e.g. 11.8M):

> Every step Claude takes re-sends the whole conversation. This month your conversation was typically {median_context_at_prompt/1000:.0f}K tokens long when you sent a message (guideline: under 150K). {long_context_prompts.pct_of_prompts}% of your prompts went into a conversation already over 200K tokens, and {cold_resume_prompts.count} re-opened a large session after an hour or more away, which re-processes the whole conversation. A short follow-up (under 40 characters) cost about {by_prompt_length.short_lt40.context_reread_per_prompt/1e6:.1f}M tokens of re-read context on average. Subagents added {tokens.subagents.output} output tokens on top of {tokens.main.output}. The habit that fixes this is small: start a new session (`/clear` or `/new`) whenever you switch task, and `/resume` only to continue the same piece of work.

Follow it with the cost-mix line: "About {tokens.cost_mix_pct.context_reread}% of your token cost was re-reading context, {tokens.cost_mix_pct.context_write}% writing it, {tokens.cost_mix_pct.output}% output (a price-weighted mix, not money)." The tone rules still apply: when the median is under the guideline, or fewer prompts went into 200K+ conversations than last month, open the paragraph with that win; keep the figures exact either way. Drop a sentence only when its number is null (e.g. no short follow-ups this month). The `/clear`, `/new`, `/resume` and `/compact` counts in `working_style.slash_commands_top` show whether the habit is already there; celebrate it when it is.

Never describe a high cache-read share or a long session as efficient. Cache reads are cheap per token, but they are re-reads of a conversation that keeps growing, and their share is close to 100% for everyone, so it says nothing about the member. The cost driver is conversation length per step.

## Step 6 - Learning signals

- Frictions: report facet `frictions` counts and `outcomes` mix (fully/partially achieved).
- Cluster the friction types plus interrupted sessions into at most 3 recurring themes.
- For each theme, check `foundation` in metrics.json: did a plausible guardrail appear (CLAUDE.md grown, new skill/command/hook, new memory files)? Label each theme `encoded` (guardrail exists), `recurring` (seen last month too, no guardrail), or `new`. For Step 9 these become `llm.learning_themes` = a list of `{"theme": <short generic label, e.g. "flaky test setup", never a client/product name or path>, "status": "encoded" | "recurring" | "new"}`.
- Foundation table: per active project, CLAUDE.md lines, skills, commands, hooks; plus global skills/hooks/plugins/memory counts.

## Step 6b - Safety checklist

From `metrics.json.security`, build a "Safety checklist" section. The collector already decided which checks need tidying: `security.flags` (names) and `security.flags_total` (count) are deterministic, so use them as they are and never recount. Frame it as the team looking out for each other: items are things worth tidying, never accusations. Table rows (names/counts only; NEVER quote a credential, URL parameter, or command):

| Check | Value | Worth tidying when |
|---|---|---|
| Permission modes used | session counts per mode (`auto` = classifier auto-approves routine actions) | any `bypassPermissions` session; note `auto` share as information, it is fine when the rows below are clean |
| Default permission mode in settings | `permission_rules.default_modes` | `bypassPermissions` anywhere |
| Allow-rules that could hurt production | `permission_rules.dangerous_allow_rules` (rule + layer + reason) | any - these let the assistant push, delete, deploy, or mutate a database without asking |
| Allow-rules worth a glance | `permission_rules.review_allow_rules` | list count only; read-only infra commands and anything mentioning prod - no flag, just a look |
| Deny-rules and guard hooks | `permission_rules.deny_rules` + `pretooluse_guard_hooks` | none present - point to the baseline deny-list in the README; when present, celebrate it: this is the fence that keeps AI away from anything unrecoverable |
| Sandbox-disabled Bash calls | count | > 0 |
| Credential-shaped strings in prompts | `hygiene` count | > 0 |
| Credential-shaped strings in Bash commands | count | > 0 |
| Plugin marketplaces | names + sources | `marketplaces_outside_approved` is not empty (approved: `artisans-tools` + `claude-plugins-official`) |
| MCP servers | name + type:binary/host | any server without an obvious reason - worth a quick team mention |
| Skills installed | names | any skill not from the team repo or written by the user - worth a quick team mention |
| Claude Code versions in window | newest + count | a single version across 20+ workdays (auto-update likely off, so security fixes are not arriving) |
| cleanupPeriodDays | value | unset or < 45 |

When N = `security.flags_total` items need tidying, the TL;DR gets one line: "Safety checklist: N small things to tidy (details inside)". The MCP-server and skills rows are conversation-starters only; they are not part of N. The team goal behind this table, state it once in the section intro: the assistant should never be able to do something unrecoverable or production-affecting without a human in the loop. When zero, say "Safety checklist: all clear" - a clean checklist deserves the mention. Every item pairs with its one-line fix. These are conversation-starters, not verdicts: an unlisted MCP server is usually perfectly legitimate.

## Step 6c - Data-retention attestation

Asked at the START of the run (see Step 1); this section is where the answer lands in the report. The consumer "Help improve Claude" toggle is an account-side setting, not readable from the machine. The question (options Yes / No / Unsure): "Is 'Help improve Claude' turned OFF at claude.ai Settings -> Privacy?" Record the answer verbatim with today's date in the report and, in Step 9, as `security.data_retention_attestation` = `{"question", "answer" ("Yes" / "No" / "Unsure"), "date" (YYYY-MM-DD), "self_reported": true}`. If No or Unsure, add a next-month opportunity line with the exact settings path so it takes one minute to fix. Do not present the attestation as verified fact; label it "self-reported".

## Step 7 - Trends

Read all `~/.claude/usage-reports/snapshots/*.json`. If a previous month exists, add a delta table for: usage %, prompts, active days, category mix top-3, prompt quality (overall + dims), interruptions/100, plan-mode %, delegation %, fully-achieved %, foundation counts, and the context metrics: median context at prompt (`context_hygiene.median_context_at_prompt`), long-context prompt % (`context_hygiene.long_context_prompts.pct_of_prompts`), cold resumes (`context_hygiene.cold_resume_prompts.count`), output per prompt (`context_hygiene.output_per_prompt`), and subagent output share (`tokens.subagents.output` / (`tokens.main.output` + `tokens.subagents.output`), as %). For the context metrics a drop is the improvement; celebrate it. If none, mark this report "baseline month".

Snapshots with `"schema_version": "2.0"` have fixed paths. Older snapshots are free-form: compare only what you can find, show the context metrics as "new in 0.2.0", and add one line under the table: "Collector 0.2.0 trend break: prompt and token counts are now limited to the month by timestamp, subagent tokens are counted separately, context metrics are new, and usage % excludes holidays, so compare those with care." Record the deltas for Step 9 as `llm.deltas` = `{"vs": "<previous YYYY-MM>", "<metric>": <this month minus previous>, ...}` with metric keys `usage_pct`, `prompts_total`, `active_days_total`, `prompt_quality_overall_pct`, `interruptions_per_100_prompts`, `plan_mode_session_pct`, `delegation_session_pct`, `fully_achieved_pct`, `median_context_at_prompt`, `long_context_prompts_pct`, `cold_resume_prompts`, `output_per_prompt`, `subagent_output_share_pct` (null when either month lacks the number); in a baseline month `llm.deltas` stays null.

## Step 8 - Redacted examples (the only place content appears)

Pick from `prompt_sample.jsonl`: 2 of the user's best prompts (present them as "patterns worth repeating", naming what makes each work), and 2 prompts with easy headroom - for each of these, ALSO write the upgraded version of the same prompt so the example teaches instead of critiques ("same ask, with a done-when line: ..."). Add 1 friction example (facet `friction_detail` via `sessions.jsonl`) framed as "what we'd encode as a guardrail". Redact BEFORE writing them into the report:

- Replace client, product, and person names with `[client]`, `[product]`, `[name]`.
- Reduce file paths to basenames; drop URLs, hostnames, keys, and any credential-shaped string.
- If an example cannot be safely redacted, pick another.

Head the section with: "Examples (redacted; review before sharing)".

## Step 9 - Write outputs

1. `~/.claude/usage-reports/report-<YYYY-MM>.md` - the full report:
   TL;DR (3 wins, 3 next-month opportunities each with its payoff, one encouraging summary line) -> Headline block -> Category mix -> Prompt Quality -> Working style (with the Context hygiene paragraph) -> Learning signals -> Safety checklist -> Trends -> Examples -> Definitions appendix: copy `metrics.json.definitions` (it includes `long_context_prompt`, `cold_resume`, `cost_mix_pct`, `holidays`, `usage_pct` and the `trend_break_0_2_0` note) plus the score rubric version.
2. `~/.claude/usage-reports/report-<YYYY-MM>.json` - the collector's `shared.json` copied verbatim, with ONLY these fields filled in by you: `llm.category_mix_pct` (Step 3), `llm.coding_submix_pct` (Step 3), `llm.prompt_quality` (Step 4), `llm.learning_themes` (Step 6), `llm.deltas` (Step 7), and `security.data_retention_attestation` (Step 6c). No other key may be added, renamed or removed, and no other value changed: HR's aggregator (`manager/aggregate.py`) reads fixed paths from schema 2.0, and next month's trend section reads this same file back, so any drift breaks both. Write it with a small script so nothing else can change, e.g. (use `py -3` where only the Windows launcher exists):
   ```
   python3 - <<'EOF'
   import json, pathlib
   doc = json.loads(pathlib.Path("<scratchpad>/ccur/shared.json").read_text(encoding="utf-8"))
   doc["llm"].update({"category_mix_pct": {...}, "coding_submix_pct": {...}, "prompt_quality": {...},
                      "learning_themes": [...], "deltas": {...}})   # deltas: None in a baseline month
   doc["security"]["data_retention_attestation"] = {"question": "...", "answer": "...", "date": "YYYY-MM-DD", "self_reported": True}
   home = pathlib.Path.home() / ".claude" / "usage-reports"
   (home / "snapshots").mkdir(parents=True, exist_ok=True)
   for p in (home / "report-YYYY-MM.json", home / "snapshots" / "YYYY-MM.json"):
       p.write_text(json.dumps(doc, indent=1), encoding="utf-8")
   EOF
   ```
3. `~/.claude/usage-reports/snapshots/<YYYY-MM>.json` - byte-for-byte the same as (2); it feeds next month's trend section.
4. `~/.claude/usage-reports/<Member>-<Month>-<Year>.zip` - zip containing just the two files from (1) and (2) (`report-<YYYY-MM>.md` and `report-<YYYY-MM>.json`, no directory nesting, never the snapshot). `<Member>` is `shared.json.member` with each run of whitespace replaced by a dash; `<Month>` is the full month name (e.g. `August`); `<Year>` is the 4-digit year for the reported month, joined with dashes - e.g. `Mark-Taylor-August-2026.zip`. The name comes from `CCUR_MEMBER`, else the first line of `~/.claude/usage-reports/member.txt`, else `git config --global user.name`, else the OS user name (`member_source` says which). Build the zip with `python3 -m zipfile -c <zip> <md> <json>`, quoting the paths - stdlib, so it works wherever the collector does, whereas `zip` is not on every machine.

Finish by printing: the TL;DR, all three file paths (md, json, zip), and this exact instruction: "This report is yours - review the Examples section, then send <Member>-<Month>-<Year>.zip to HR." When `member_source` is `git` or `USER` and the name looks like a handle rather than a full name (e.g. `jdoe42`), add one line: "Tip: put your full name on the first line of ~/.claude/usage-reports/member.txt and next month's report and zip will use it."

## Hard privacy rules

- The shared report never contains: full prompts outside the redacted Examples section, session summaries, client names, absolute paths, tokens/keys, or anything from `sessions.jsonl` / `prompt_sample.jsonl` beyond what Steps 3-8 specify. The shared JSON is `shared.json` plus the `llm` fields and the attestation; nothing from the LOCAL ONLY files goes into it.
- `sessions.jsonl` and `prompt_sample.jsonl` stay in the scratchpad; never copy them to `~/.claude/usage-reports/`.
- If `cleanupPeriodDays` in `~/.claude/settings.json` is unset or < 45, add a one-line notice recommending 45+ so monthly runs always see the full month.

## Cost guard

One collector run, one classification pass, one scoring pass. Do not iterate over raw transcripts, do not re-score, do not read more than the two LOCAL ONLY files plus metrics.json and shared.json.
