"""
Task #1 analysis (read-only): measure how well the Outscraper `about` attribute
data can be joined to Airtable records, and what the per-business
distinguishing-fact count distribution looks like. This calibrates the gating
threshold for generate_fact_descriptions.py. Writes nothing.
"""
import os
import re
import json
import glob
from collections import Counter, defaultdict

import openpyxl
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv("/Users/kevincollins/GitHub/dog-grooming-directory/.env")

OUTSCRAPER_DIR = "/Users/kevincollins/GitHub/dog-grooming-directory/outscraper_processed"


def norm(s):
    if s is None:
        return ""
    s = str(s).strip().lower()
    s = re.sub(r"[^a-z0-9 ]", "", s)
    s = re.sub(r"\s+", " ", s)
    return s


def join_key(name, city, state):
    return f"{norm(name)}|{norm(city)}|{norm(state)}"


def find_cols(header):
    """Locate columns by header name, robust across the 7 files."""
    idx = {}
    for i, h in enumerate(header):
        hl = norm(h)
        if hl == "name" and "name" not in idx:
            idx["name"] = i
        elif hl == "city" and "city" not in idx:
            idx["city"] = i
        elif hl == "state" and "state" not in idx:
            idx["state"] = i
        elif hl == "about" and "about" not in idx:
            idx["about"] = i
    return idx


# ---- Load + dedupe Outscraper about attributes ----
about_by_key = {}
files = sorted(glob.glob(os.path.join(OUTSCRAPER_DIR, "*.xlsx")))
total_rows = 0
rows_with_about = 0
for path in files:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = next(rows)
    cols = find_cols(header)
    if "name" not in cols or "about" not in cols:
        print(f"  SKIP {os.path.basename(path)} (missing name/about cols: {cols})")
        wb.close()
        continue
    for row in rows:
        total_rows += 1
        name = row[cols["name"]] if cols["name"] < len(row) else None
        city = row[cols.get("city", -1)] if cols.get("city", -1) >= 0 and cols["city"] < len(row) else None
        state = row[cols.get("state", -1)] if cols.get("state", -1) >= 0 and cols["state"] < len(row) else None
        about = row[cols["about"]] if cols["about"] < len(row) else None
        if not name:
            continue
        k = join_key(name, city, state)
        if about and str(about).strip():
            rows_with_about += 1
            # keep the longest about blob if duplicate keys
            if k not in about_by_key or len(str(about)) > len(str(about_by_key[k])):
                about_by_key[k] = about
    wb.close()

print(f"Outscraper files: {len(files)}")
print(f"Total data rows scanned: {total_rows}")
print(f"Rows with non-empty about: {rows_with_about}")
print(f"Unique join keys with about: {len(about_by_key)}")


# ---- Parse about JSON into a flat fact set ----
def parse_about(about_raw):
    """Return (categories_dict, flat_true_facts list)."""
    try:
        data = json.loads(about_raw) if isinstance(about_raw, str) else about_raw
    except Exception:
        return {}, []
    if not isinstance(data, dict):
        return {}, []
    flat = []
    for category, attrs in data.items():
        if isinstance(attrs, dict):
            for attr_name, val in attrs.items():
                if val is True:
                    flat.append((category, attr_name))
        elif isinstance(attrs, list):
            for item in attrs:
                flat.append((category, str(item)))
    return data, flat


fact_counts = []
category_counter = Counter()
sample_keys = list(about_by_key.keys())[:3]
for k, about_raw in about_by_key.items():
    cats, flat = parse_about(about_raw)
    fact_counts.append(len(flat))
    for cat in cats.keys():
        category_counter[cat] += 1

# ---- Join to Airtable ----
api = Api(os.environ["AIRTABLE_API_KEY"])
table = api.table(os.environ["AIRTABLE_BASE_ID"], os.environ.get("AIRTABLE_TABLE_NAME", "Groomers"))

at_records = table.all(fields=["Name", "City", "State", "Decription"])
print(f"\nAirtable records: {len(at_records)}")

matched = 0
matched_facts = []
desc_len_when_matched = []
for rec in at_records:
    f = rec["fields"]
    k = join_key(f.get("Name"), f.get("City"), f.get("State"))
    if k in about_by_key:
        matched += 1
        _, flat = parse_about(about_by_key[k])
        matched_facts.append(len(flat))

print(f"Airtable records matched to an about blob: {matched} ({100*matched/max(1,len(at_records)):.1f}%)")

# ---- Distributions ----
def dist(label, counts):
    if not counts:
        print(f"\n{label}: (none)")
        return
    counts = sorted(counts)
    n = len(counts)
    def pct(p):
        return counts[min(n-1, int(p*n))]
    buckets = Counter()
    for c in counts:
        if c == 0: buckets["0"] += 1
        elif c <= 2: buckets["1-2"] += 1
        elif c <= 4: buckets["3-4"] += 1
        elif c <= 7: buckets["5-7"] += 1
        elif c <= 11: buckets["8-11"] += 1
        else: buckets["12+"] += 1
    print(f"\n{label} (n={n}): min={counts[0]} p25={pct(.25)} median={pct(.5)} p75={pct(.75)} p90={pct(.9)} max={counts[-1]}")
    for b in ["0","1-2","3-4","5-7","8-11","12+"]:
        print(f"   {b:>5} facts: {buckets[b]:>5}  ({100*buckets[b]/n:.1f}%)")

dist("All about-blobs: # true/listable facts", fact_counts)
dist("MATCHED Airtable records: # facts", matched_facts)

print("\nTop attribute categories (across about-blobs):")
for cat, cnt in category_counter.most_common(15):
    print(f"   {cnt:>5}  {cat}")
