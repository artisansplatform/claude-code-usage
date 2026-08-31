---
name: usage-report
description: Generate the user's personal monthly Claude Code growth report (wins, prompt-craft score, trends, and next-month suggestions), write it to ~/.claude/usage-reports/, and have them review the Examples section before sharing.
---

# Monthly growth report

You produce the user's personal growth report from their LOCAL Claude Code data. Nothing is uploaded; the user reviews the finished file and shares it themselves.

**Tone rules (apply to every sentence of the report):** write in second person ("you"), lead every section with what is going well, and frame every gap as a specific, small opportunity ("try adding a done-when line to your next brief") rather than a criticism. Never use scolding words (weak, poor, failure, violation, bad habit) in the report body; never compare the user to other people; celebrate month-over-month improvement explicitly wherever a delta is positive. The numbers themselves stay honest and unrounded - warmth in the words, accuracy in the figures.

**Month selection**: if the user passed an argument like `2026-08`, use that calendar month. Otherwise: today is day 1-7 of a month -> report the previous full month; else report the current month to date and label the report "(partial month)".

## Step 1 - Ask the one question, then collect

FIRST, ask the data-retention question from Step 6c (one AskUserQuestion call). It is the run's only interaction; asking it up front means everything after runs unattended instead of blocking mid-run while the user is away.

Then run the bundled collector at `${CLAUDE_PLUGIN_ROOT}/bin/ccur-collect` (do not assume it is on PATH):

```
${CLAUDE_PLUGIN_ROOT}/bin/ccur-collect --from <YYYY-MM-01> --to <last-day> --out <scratchpad>/ccur
```

Read `metrics.json` fully. Read `sessions.jsonl` and `prompt_sample.jsonl` only as instructed below. NEVER read raw transcripts under `~/.claude/projects/` yourself; the collector already parsed them, and reading them would blow up cost.

If `metrics.json` shows fewer sessions than `rhythm.prompts_total` implies (transcripts already cleaned up), say so in the report header and rely on history-based metrics. If facet coverage is low (< 40%), note that running `/insights` first enriches category/outcome data, then continue with what exists.

## Step 2 - Deterministic sections

Use the numbers exactly as computed; the definitions live in `metrics.json.definitions` and must not be reinterpreted between months. Headline block (keep this exact shape; it is what managers compare across people and months):

```
Monthly Usage: <usage_pct>% (<active_days>/<workdays> Mon-Fri days)
Avg Daily Usage: <active hours per active day, from sessions.active_minutes_total>
Peak Day: <weekday with max prompts> | Peak Hour: <top hour, local>
Heavy / Light / Inactive days: <n> / <n> / <workdays - active_days>
Sessions: <count> | Prompts: <prompts_total> | Projects: <distinct_projects>
```

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

For sessions without facets, classify from `sessions.jsonl` (`first_prompt` + `top_tools` + project name), max 200 rows, in one pass. Report the mix as % of sessions, plus a Coding sub-mix (feature / bug fix / testing / refactor / optimization) from the same data.

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

Rules: judge the prompt as written, not the outcome. Score in one batch. Report overall %, per-dimension means, n, and note the dimension with the most headroom (call it "your biggest opportunity", with the expected payoff, e.g. fewer re-explains).

Hygiene: `metrics.json.hygiene` counts sampled prompts where credential-shaped strings were auto-masked. If > 0, add a safety-checklist item in Step 6b (count only; NEVER quote or describe the credential itself) suggesting env vars / `!` commands reading from files as the easy alternative to pasting secrets.

## Step 5 - Working style and leverage

From `metrics.json`: interruptions per 100 prompts, tool error share, plan-mode session %, delegation session %, slash-command usage (which ones, how often), model mix and token totals (label costs "estimate"), median response time if present, cache-read ratio (cache_read / (input + cache_read)). One short paragraph naming the user's working style and the single habit that would raise their leverage most next month.

## Step 6 - Learning signals

- Frictions: report facet `frictions` counts and `outcomes` mix (fully/partially achieved).
- Cluster the friction types plus interrupted sessions into at most 3 recurring themes.
- For each theme, check `foundation` in metrics.json: did a plausible guardrail appear (CLAUDE.md grown, new skill/command/hook, new memory files)? Label each theme `encoded` (guardrail exists), `recurring` (seen last month too, no guardrail), or `new`.
- Foundation table: per active project, CLAUDE.md lines, skills, commands, hooks; plus global skills/hooks/plugins/memory counts.

## Step 6b - Safety checklist

From `metrics.json.security`, build a "Safety checklist" section. Frame it as the team looking out for each other: items are things worth tidying, never accusations. Table rows (names/counts only; NEVER quote a credential, URL parameter, or command):

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
| Plugin marketplaces | names + sources | any source outside the team's approved list (the team marketplace + `claude-plugins-official`) |
| MCP servers | name + type:binary/host | any server without an obvious reason - worth a quick team mention |
| Skills installed | names | any skill not from the team repo or written by the user - worth a quick team mention |
| Claude Code versions in window | newest + count | a single version across a full month (auto-update likely off, so security fixes are not arriving) |
| cleanupPeriodDays | value | unset or < 45 |

When N items need tidying, the TL;DR gets one line: "Safety checklist: N small things to tidy (details inside)". The team goal behind this table, state it once in the section intro: the assistant should never be able to do something unrecoverable or production-affecting without a human in the loop. When zero, say "Safety checklist: all clear" - a clean checklist deserves the mention. Every item pairs with its one-line fix. These are conversation-starters, not verdicts: an unlisted MCP server is usually perfectly legitimate.

## Step 6c - Data-retention attestation

Asked at the START of the run (see Step 1); this section is where the answer lands in the report. The consumer "Help improve Claude" toggle is an account-side setting, not readable from the machine. The question (options Yes / No / Unsure): "Is 'Help improve Claude' turned OFF at claude.ai Settings -> Privacy?" Record the answer verbatim with today's date in the report and snapshot as `data_retention_attestation`. If No or Unsure, add a next-month opportunity line with the exact settings path so it takes one minute to fix. Do not present the attestation as verified fact; label it "self-reported".

## Step 7 - Trends

Read all `~/.claude/usage-reports/snapshots/*.json`. If a previous month exists, add a delta table for: usage %, prompts, active days, category mix top-3, prompt quality (overall + dims), interruptions/100, plan-mode %, delegation %, fully-achieved %, foundation counts. If none, mark this report "baseline month".

## Step 8 - Redacted examples (the only place content appears)

Pick from `prompt_sample.jsonl`: 2 of the user's best prompts (present them as "patterns worth repeating", naming what makes each work), and 2 prompts with easy headroom - for each of these, ALSO write the upgraded version of the same prompt so the example teaches instead of critiques ("same ask, with a done-when line: ..."). Add 1 friction example (facet `friction_detail` via `sessions.jsonl`) framed as "what we'd encode as a guardrail". Redact BEFORE writing them into the report:

- Replace client, product, and person names with `[client]`, `[product]`, `[name]`.
- Reduce file paths to basenames; drop URLs, hostnames, keys, and any credential-shaped string.
- If an example cannot be safely redacted, pick another.

Head the section with: "Examples (redacted; review before sharing)".

## Step 9 - Write outputs

1. `~/.claude/usage-reports/report-<YYYY-MM>.md` - the full report:
   TL;DR (3 wins, 3 next-month opportunities each with its payoff, one encouraging summary line) -> Headline block -> Category mix -> Prompt Quality -> Working style -> Learning signals -> Safety checklist -> Trends -> Examples -> Definitions appendix (copy from metrics.json + score rubric version).
2. `~/.claude/usage-reports/report-<YYYY-MM>.json` - shared-safe numbers only (member, window, headline numbers, category mix, prompt score + dims, interruptions/100, plan/delegation %, outcomes, foundation counts, security block {flags_total, per-check values, attestation}, deltas). No prompt text, no summaries, no project paths (project basenames are fine).
3. `~/.claude/usage-reports/snapshots/<YYYY-MM>.json` - same as (2); it feeds next month's trend section.
4. `~/.claude/usage-reports/<Member> <Month> <Year>.zip` - zip containing just the two files from (1) and (2) (`report-<YYYY-MM>.md` and `report-<YYYY-MM>.json`, no directory nesting). `<Member>` is `metrics.json.member`; `<Month>` is the full month name (e.g. `August`); `<Year>` is the 4-digit year for the reported month - e.g. `Nishit August 2026.zip`. Build it with `zip -j`.

Finish by printing: the TL;DR, all three file paths (md, json, zip), and this exact instruction: "This report is yours - review the Examples section, then send <Member> <Month> <Year>.zip to HR."

## Hard privacy rules

- The shared report never contains: full prompts outside the redacted Examples section, session summaries, client names, absolute paths, tokens/keys, or anything from `sessions.jsonl` / `prompt_sample.jsonl` beyond what Steps 3-8 specify.
- `sessions.jsonl` and `prompt_sample.jsonl` stay in the scratchpad; never copy them to `~/.claude/usage-reports/`.
- If `cleanupPeriodDays` in `~/.claude/settings.json` is unset or < 45, add a one-line notice recommending 45+ so monthly runs always see the full month.

## Cost guard

One collector run, one classification pass, one scoring pass. Do not iterate over raw transcripts, do not re-score, do not read more than the two LOCAL ONLY files plus metrics.json.
