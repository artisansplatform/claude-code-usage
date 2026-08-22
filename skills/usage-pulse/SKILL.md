---
name: usage-pulse
description: Quick weekly Claude Code usage pulse (deterministic numbers only, no LLM scoring) printed to the terminal and snapshotted locally. Nothing is shared.
---

# Weekly usage pulse

A 1-minute self-check. Deterministic only; no prompt scoring, no classification, no content.

1. Window = the last 7 full days ending yesterday (local time). If the user passed a date range, use that instead.
2. Run `${CLAUDE_PLUGIN_ROOT}/bin/ccur-collect --from <start> --to <end> --out <scratchpad>/ccur-pulse` (the collector is not on PATH). Read only `metrics.json`.
3. Print a pulse of at most 15 lines:

```
Claude Code pulse <start>..<end>
Active days: n/7 | Prompts: N | Sessions: N | Projects: N
Peak: <weekday> <hour> | Heavy days: n | Interruptions/100 prompts: x
Plan mode: n sessions | Delegation: n sessions | Tool errors: n
Top projects: a (x%), b (y%)
Top tools: ...
vs last week: prompts +x%, active days +n, interruptions/100 [up|down]
One-line nudge: <single most useful habit change, from the numbers only>
```

4. Append the headline numbers to `~/.claude/usage-reports/weekly/<ISO-year>-W<week>.json` (create dirs as needed) so the monthly report and next week's "vs last week" line can use them.
5. No file is meant to be shared; say so if asked. Do not read `sessions.jsonl` or `prompt_sample.jsonl`; the pulse is numbers-only.
