#!/usr/bin/env python3
"""Combine everyone's shared report-YYYY-MM.json files into one team snapshot.

Usage: python3 aggregate.py <dir-with-report-json-files> [--out team-summary.md]
The .md reports are for reading; this consumes only the shared-safe .json.
Per the README ground rules: this table is for spotting shared training needs
and celebrating wins, not for ranking people.
"""

import argparse
import json
import sys
from pathlib import Path


def flat(d, prefix=""):
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flat(v, key + "."))
        else:
            out[key] = v
    return out


COLUMNS = [
    ("member", "Member"),
    ("window.from", "From"),
    ("headline.usage_pct", "Usage %"),
    ("headline.active_days", "Active days"),
    ("headline.prompts_total", "Prompts"),
    ("headline.sessions", "Sessions"),
    ("prompt_quality.overall_pct", "Prompt score %"),
    ("prompt_quality.delta_pct", "Score delta"),
    ("style.interruptions_per_100", "Interrupts/100"),
    ("style.plan_mode_pct", "Plan %"),
    ("style.delegation_pct", "Delegate %"),
    ("outcomes.fully_achieved_pct", "Fully achieved %"),
    ("foundation.total_guardrails", "Guardrails"),
    ("security.flags_total", "Safety items"),
    ("security.data_retention_attestation", "Retention off?"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reports_dir")
    ap.add_argument("--out", default="team-summary.md")
    args = ap.parse_args()

    rows = []
    for f in sorted(Path(args.reports_dir).glob("*.json")):
        try:
            rows.append(flat(json.loads(f.read_text())))
        except Exception as e:
            print(f"skip {f.name}: {e}", file=sys.stderr)
    if not rows:
        sys.exit("no readable report .json files found")

    keys = [k for k, _ in COLUMNS]
    heads = [h for _, h in COLUMNS]
    lines = ["| " + " | ".join(heads) + " |",
             "|" + "|".join("---" for _ in heads) + "|"]
    for r in sorted(rows, key=lambda r: str(r.get("member", ""))):
        lines.append("| " + " | ".join(str(r.get(k, "-")) for k in keys) + " |")

    Path(args.out).write_text("\n".join(lines) + "\n")
    print(f"{len(rows)} reports -> {args.out}")


if __name__ == "__main__":
    main()
