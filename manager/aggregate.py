#!/usr/bin/env python3
"""Combine everyone's shared report-YYYY-MM.json files into one team snapshot.

Usage: python3 aggregate.py <dir-with-report-zips-or-json> [--out team-summary.md]
Members send a zip of their .md + .json, so the folder is read either way: a
loose .json, or the .json inside each zip. The .md reports are for reading;
this consumes only the shared-safe .json.
Per the README ground rules: this table is for spotting shared training needs
and celebrating wins, not for ranking people.
"""

import argparse
import json
import sys
import zipfile
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


def report_blobs(reports_dir):
    """(label, json text) per report, from a loose .json or from inside a .zip."""
    d = Path(reports_dir)
    if not d.is_dir():
        sys.exit(f"not a folder: {reports_dir}")
    for f in sorted(d.iterdir()):
        suffix = f.suffix.lower()
        try:
            if suffix == ".json":
                yield f.name, f.read_text()
            elif suffix == ".zip":
                with zipfile.ZipFile(f) as z:
                    for name in sorted(z.namelist()):
                        if name.lower().endswith(".json"):
                            yield f"{f.name}:{name}", z.read(name).decode()
        except Exception as e:
            print(f"skip {f.name}: {e}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reports_dir")
    ap.add_argument("--out", default="team-summary.md")
    args = ap.parse_args()

    rows = []
    for label, text in report_blobs(args.reports_dir):
        try:
            rows.append(flat(json.loads(text)))
        except Exception as e:
            print(f"skip {label}: {e}", file=sys.stderr)
    if not rows:
        sys.exit("no readable report .json found (loose or inside a .zip)")

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
