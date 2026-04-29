#!/usr/bin/env python3
"""Extract groomer slugs with Google traffic from a GSC Performance export.

Writes data/gsc_protected_urls.txt with one slug per line. These slugs are
grandfathered through the description_quality_check in build.py for 60 days
so the new strict quality gate cannot regress URLs already earning traffic.

Usage:
    python scripts/extract_gsc_protected.py path/to/Performance-export.xlsx
"""
import re
import sys
from pathlib import Path

import openpyxl

THRESHOLD_IMPRESSIONS = 5  # protect URLs with > this many impressions even if 0 clicks
URL_RE = re.compile(r'^https://doggroomerlocator\.com/groomer/([a-z0-9-]+)(\.html)?$')


def extract(xlsx_path: Path) -> set[str]:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    slugs = set()
    for row in wb['Pages'].iter_rows(min_row=2, values_only=True):
        if not row[0]:
            continue
        url, clicks, impr, _ctr, _pos = row
        m = URL_RE.match(url)
        if not m:
            continue
        if (clicks or 0) > 0 or (impr or 0) > THRESHOLD_IMPRESSIONS:
            slugs.add(m.group(1))
    return slugs


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    src = Path(sys.argv[1])
    slugs = extract(src)
    out = Path(__file__).parent.parent / "data" / "gsc_protected_urls.txt"
    with out.open("w") as f:
        f.write("# Groomer slugs with measurable Google traffic (clicks>0 OR impressions>5)\n")
        f.write(f"# Source: {src.name}\n")
        f.write("# Grandfathered through description_quality_check in build.py.\n")
        for slug in sorted(slugs):
            f.write(slug + "\n")
    print(f"Wrote {len(slugs)} slugs to {out}")


if __name__ == "__main__":
    main()
