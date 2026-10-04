#!/usr/bin/env python3
"""Combine everyone's shared report-YYYY-MM.json files into one team snapshot.

Usage: python3 aggregate.py <dir-with-report-zips-or-json> [--out team-summary.md]
Members send a zip of their .md + .json, so the folder is read either way: a
loose .json, or the .json inside each zip. Anything under a snapshots/ folder
inside a zip is skipped (it is a copy of the report). The .md reports are for
reading; this consumes only the shared-safe .json.

Schema 2.0 files (collector 0.2.0+; the skill copies the collector's shared.json
verbatim) are read by fixed paths. Older free-form files get a best-effort read
and are marked "old schema": their keys differ per member and their numbers are
not comparable (no holiday adjustment, whole-session main-thread tokens), so
their token and context columns stay empty.
One row per (member, window start); a schema 2.0 file wins over an old one, a
finished report (llm block filled) over a raw shared.json, then the newer
generated_at.
Per the README ground rules: this table is for spotting shared training needs
and celebrating wins, not for ranking people.
"""

import argparse
import json
import sys
import zipfile
from pathlib import Path

COLUMNS = ["Member", "Window", "Usage % (holiday-adjusted)", "Active wd", "Prompts",
           "Sessions", "Output M", "Context re-read B (main+subagents)", "Median ctx K",
           "Long-ctx prompts %", "Cold resumes", "Opus % of output", "Prompt score %",
           "Plan %", "Delegate %", "Safety items", "Retention off?"]

# Old free-form reports: the key paths members' reports actually used, first hit wins.
OLD_SCHEMA_PATHS = {
    "Usage % (holiday-adjusted)": ["headline.usage_pct", "headline.monthly_usage_pct"],
    "Active wd": ["headline.active_workdays", "headline.active_days"],
    "Prompts": ["headline.prompts_total", "headline.prompts"],
    "Sessions": ["headline.sessions"],
    "Prompt score %": ["prompt_quality.overall_pct"],
    "Plan %": ["working_style.plan_mode_session_pct", "style.plan_mode_pct",
               "plan_mode_session_pct"],
    "Delegate %": ["working_style.delegation_session_pct", "style.delegation_pct",
                   "delegation_session_pct"],
    "Safety items": ["security.flags_total"],
    "Retention off?": ["security.data_retention_attestation.answer",
                       "security.data_retention_attestation",
                       "security.attestation.answer",
                       "data_retention_attestation.answer",
                       "data_retention_attestation"],
}


def get(d, path):
    """Value at a dotted path in nested dicts, or None."""
    for part in path.split("."):
        if not isinstance(d, dict):
            return None
        d = d.get(part)
    return d


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def scaled(v, div, nd):
    v = num(v)
    if v is None:
        return None
    return int(round(v / div)) if nd == 0 else round(v / div, nd)


def total(*vals):
    vals = [num(v) for v in vals]
    return None if all(v is None for v in vals) else sum(v or 0 for v in vals)


def window_label(w):
    w = w if isinstance(w, dict) else {}
    if not w.get("from"):
        return None
    label = f"{w['from']}..{w['to']}" if w.get("to") else str(w["from"])
    return label + " (partial)" if w.get("partial") or w.get("partial_month") else label


def opus_share(shares):
    if not isinstance(shares, dict) or not shares:
        return None
    return round(sum(num(v) or 0 for m, v in shares.items() if "opus" in str(m).lower()), 1)


def row_v2(d):
    """Schema 2.0: every column from a fixed path."""
    active = get(d, "headline.active_workdays")
    workdays = get(d, "window.workdays_excl_holidays")
    output = total(get(d, "tokens.main.output"), get(d, "tokens.subagents.output"))
    reread = total(get(d, "tokens.main.cache_read"), get(d, "tokens.subagents.cache_read"))
    return {
        "Member": d.get("member"),
        "Window": window_label(d.get("window")),
        "Usage % (holiday-adjusted)": get(d, "headline.usage_pct"),
        "Active wd": f"{active}/{workdays}" if num(active) is not None
        and num(workdays) is not None else active,
        "Prompts": get(d, "headline.prompts_total"),
        "Sessions": get(d, "headline.sessions"),
        "Output M": scaled(output, 1e6, 1),
        "Context re-read B (main+subagents)": scaled(reread, 1e9, 2),
        "Median ctx K": scaled(get(d, "context_hygiene.median_context_at_prompt"), 1e3, 0),
        "Long-ctx prompts %": get(d, "context_hygiene.long_context_prompts.pct_of_prompts"),
        "Cold resumes": get(d, "context_hygiene.cold_resume_prompts.count"),
        "Opus % of output": opus_share(get(d, "tokens.model_output_share_pct")),
        "Prompt score %": get(d, "llm.prompt_quality.overall_pct"),
        "Plan %": get(d, "working_style.plan_mode_session_pct"),
        "Delegate %": get(d, "working_style.delegation_session_pct"),
        "Safety items": get(d, "security.flags_total"),
        "Retention off?": get(d, "security.data_retention_attestation.answer"),
        "_output": output, "_reread": reread,
    }


def row_old(d):
    """Pre-2.0 free-form report: best effort over the keys members used."""
    row = {c: None for c in COLUMNS}
    row.update({"Member": f"{d.get('member')} (old schema)",
                "Window": window_label(d.get("window")),
                "_output": None, "_reread": None})
    for col, paths in OLD_SCHEMA_PATHS.items():
        for path in paths:
            v = get(d, path)
            if v is not None and not isinstance(v, (dict, list)):
                row[col] = v
                break
    return row


def report_blobs(reports_dir):
    """(label, json text) per report, from a loose .json or from inside a .zip."""
    d = Path(reports_dir)
    if not d.is_dir():
        sys.exit(f"not a folder: {reports_dir}")
    for f in sorted(d.iterdir()):
        suffix = f.suffix.lower()
        try:
            if suffix == ".json":
                yield f.name, f.read_text(encoding="utf-8-sig")
            elif suffix == ".zip":
                found = 0
                with zipfile.ZipFile(f) as z:
                    for name in sorted(z.namelist()):
                        norm = name.replace("\\", "/").lower()
                        if not norm.endswith(".json") or "snapshots/" in norm:
                            continue
                        found += 1
                        yield f"{f.name}:{name}", z.read(name).decode("utf-8-sig")
                if not found:
                    print(f"skip {f.name}: no report .json inside", file=sys.stderr)
        except Exception as e:
            print(f"skip {f.name}: {e}", file=sys.stderr)


def cell(v):
    return "-" if v is None else str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reports_dir")
    ap.add_argument("--out", default="team-summary.md")
    args = ap.parse_args()

    best = {}   # (member, window start) -> (rank, label, row)
    for label, text in report_blobs(args.reports_dir):
        try:
            data = json.loads(text)
        except Exception as e:
            print(f"skip {label}: {e}", file=sys.stderr)
            continue
        if not isinstance(data, dict) or not data.get("member"):
            print(f"skip {label}: not a member report", file=sys.stderr)
            continue
        v2 = str(data.get("schema_version", "")).startswith("2.")
        row = row_v2(data) if v2 else row_old(data)
        row["_v2"] = v2
        key = (" ".join(str(data["member"]).split()).casefold(),
               str(get(data, "window.from")))
        # a finished report (llm block filled) beats a raw shared.json copy
        filled = v2 and any(v is not None for v in (data.get("llm") or {}).values())
        rank = (v2, filled, str(data.get("generated_at") or ""),
                label.rsplit("/", 1)[-1].rsplit(":", 1)[-1].startswith("report-"))
        if key in best:
            kept = max(best[key], (rank, label, row), key=lambda t: t[0])
            dropped = best[key] if kept is not best[key] else (rank, label, row)
            print(f"skip {dropped[1]}: duplicate of {kept[1]}", file=sys.stderr)
            best[key] = kept
        else:
            best[key] = (rank, label, row)
    if not best:
        sys.exit("no readable report .json found (loose or inside a .zip)")

    rows = [r for _, _, r in sorted(best.values(),
                                    key=lambda t: (str(t[2]["Member"]).casefold(),
                                                   str(t[2]["Window"])))]
    lines = ["| " + " | ".join(COLUMNS) + " |",
             "|" + "|".join("---" for _ in COLUMNS) + "|"]
    for r in rows:
        lines.append("| " + " | ".join(cell(r.get(c)) for c in COLUMNS) + " |")

    v2_rows = [r for r in rows if r["_v2"]]
    old_rows = len(rows) - len(v2_rows)
    output = sum(num(r["_output"]) or 0 for r in v2_rows)
    reread = sum(num(r["_reread"]) or 0 for r in v2_rows)
    summary = [
        f"Team totals ({len(rows)} rows): prompts {sum(num(r['Prompts']) or 0 for r in rows)}"
        f" | sessions {sum(num(r['Sessions']) or 0 for r in rows)}"
        f" | output {output / 1e6:.1f}M | context re-read {reread / 1e9:.2f}B"
        f" (tokens: schema 2.0 rows only)",
        f"Old-schema rows: {old_rows} (best-effort read; not comparable with 2.0 rows)",
    ]
    windows = {r["Window"] for r in rows}
    if len(windows) > 1:
        summary.append(f"Note: rows cover {len(windows)} different windows; check the "
                       f"Window column before comparing.")
    Path(args.out).write_text("\n".join(lines) + "\n\n" + "\n\n".join(summary) + "\n",
                              encoding="utf-8")
    print(f"{len(rows)} reports -> {args.out}")
    for s in summary:
        print(s)


if __name__ == "__main__":
    main()
