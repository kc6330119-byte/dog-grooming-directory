#!/usr/bin/env python3
"""Extract groomer slugs with Google traffic from a GSC Performance export.

Writes data/gsc_protected_urls.txt with one slug per line. These slugs are
grandfathered through the description_quality_check in build.py so the strict
quality gate cannot regress URLs already earning traffic.

MERGE IS THE DEFAULT, AND IT MATTERS. A single GSC export is a 28-day snapshot;
during a ranking demotion, impressions are depressed, so a fresh export under-
represents the pages that have earned traffic over time. Overwriting the list
with one export would (a) DROP previously-protected pages that are temporarily
suppressed and (b) re-index hundreds of impression-only pages from any short
traffic spike, re-inflating the thin indexed surface we are trying to shrink.
So by default this script UNIONS the export's qualifying slugs into the existing
list and never removes anything. Use --overwrite only for a deliberate rebuild
from scratch.

By default only CLICK-earning slugs (clicks>0) are added — clicks are the clean
"a human chose this result" signal. Pass --include-impressions to also add slugs
with >5 impressions (looser; risks re-inflating the thin surface during a spike).

Usage:
    python scripts/extract_gsc_protected.py path/to/Performance-export.xlsx
    python scripts/extract_gsc_protected.py export.xlsx --include-impressions
    python scripts/extract_gsc_protected.py export.xlsx --overwrite   # rare
"""
import argparse
import re
from pathlib import Path

import openpyxl

THRESHOLD_IMPRESSIONS = 5  # with --include-impressions, protect URLs with > this many impressions
URL_RE = re.compile(r'^https://doggroomerlocator\.com/groomer/([a-z0-9-]+)(\.html)?$')
OUT = Path(__file__).parent.parent / "data" / "gsc_protected_urls.txt"


def extract(xlsx_path: Path, include_impressions: bool) -> set:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    slugs = set()
    for row in wb['Pages'].iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        url, clicks, impr, _ctr, _pos = row
        m = URL_RE.match(url)
        if not m:
            continue
        qualifies = (clicks or 0) > 0 or (include_impressions and (impr or 0) > THRESHOLD_IMPRESSIONS)
        if qualifies:
            slugs.add(m.group(1))
    return slugs


def load_existing() -> set:
    if not OUT.exists():
        return set()
    return {
        line.strip()
        for line in OUT.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


def main():
    ap = argparse.ArgumentParser(description="Refresh data/gsc_protected_urls.txt from a GSC export.")
    ap.add_argument("xlsx", help="path to a GSC Performance export (.xlsx)")
    ap.add_argument("--include-impressions", action="store_true",
                    help="also protect slugs with >5 impressions (looser; risks thin-surface re-inflation)")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace the list instead of merging (rare; drops anything not in this export)")
    args = ap.parse_args()

    src = Path(args.xlsx)
    new_slugs = extract(src, args.include_impressions)
    existing = set() if args.overwrite else load_existing()
    merged = existing | new_slugs
    added = merged - existing

    signal = "clicks>0" + (" OR impressions>5" if args.include_impressions else "")
    mode = "OVERWRITE" if args.overwrite else "MERGE"
    header = [
        f"# Groomer slugs grandfathered past description_quality_check in build.py.",
        f"# Mode: {mode} | signal: {signal} | source: {src.name}",
        f"# Merge preserves all prior entries; overwrite would drop pages not in this export.",
    ]
    OUT.write_text("\n".join(header + sorted(merged)) + "\n")
    print(f"{mode}: {len(existing)} existing + {len(added)} added = {len(merged)} slugs -> {OUT}")


if __name__ == "__main__":
    main()
