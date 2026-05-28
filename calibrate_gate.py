"""
Calibrate the index gate: for each Airtable record, compute a composite
information-density score from BOTH Airtable structured fields and the joined
Outscraper `about` attributes, weighting *distinguishing* facts higher than
near-universal boilerplate (accessibility/payments). Show how many listings
pass candidate thresholds. Read-only.
"""
import os, re, json, glob
from collections import Counter
import openpyxl
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv("/Users/kevincollins/GitHub/dog-grooming-directory/.env")
OUTSCRAPER_DIR = "/Users/kevincollins/GitHub/dog-grooming-directory/outscraper_processed"

def norm(s):
    if s is None: return ""
    s = re.sub(r"[^a-z0-9 ]", "", str(s).strip().lower())
    return re.sub(r"\s+", " ", s)

def join_key(n, c, s): return f"{norm(n)}|{norm(c)}|{norm(s)}"

# generic/boilerplate categories: present on nearly every GBP, low differentiation
GENERIC_CATS = {"accessibility", "payments", "parking"}

def load_about():
    about_by_key = {}
    for path in sorted(glob.glob(os.path.join(OUTSCRAPER_DIR, "*.xlsx"))):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        header = [norm(h) for h in next(rows)]
        ci = {h: i for i, h in enumerate(header)}
        if "name" not in ci or "about" not in ci:
            wb.close(); continue
        for row in rows:
            name = row[ci["name"]] if ci["name"] < len(row) else None
            city = row[ci["city"]] if "city" in ci and ci["city"] < len(row) else None
            state = row[ci["state"]] if "state" in ci and ci["state"] < len(row) else None
            about = row[ci["about"]] if ci["about"] < len(row) else None
            if not name or not about or not str(about).strip(): continue
            k = join_key(name, city, state)
            if k not in about_by_key or len(str(about)) > len(str(about_by_key[k])):
                about_by_key[k] = about
        wb.close()
    return about_by_key

def about_facts(about_raw):
    """Return (distinguishing_count, generic_count, has_ownership_identity)."""
    try:
        data = json.loads(about_raw) if isinstance(about_raw, str) else about_raw
    except Exception:
        return 0, 0, False
    if not isinstance(data, dict): return 0, 0, False
    dist_n = gen_n = 0
    ownership = False
    for cat, attrs in data.items():
        cn = norm(cat)
        is_generic = cn in GENERIC_CATS
        trues = []
        if isinstance(attrs, dict):
            trues = [a for a, v in attrs.items() if v is True]
        elif isinstance(attrs, list):
            trues = [str(x) for x in attrs]
        for a in trues:
            al = a.lower()
            if "owned" in al or "identifies as" in al or "veteran" in al or "women-led" in al:
                ownership = True
        if is_generic: gen_n += len(trues)
        else: dist_n += len(trues)
    return dist_n, gen_n, ownership

about_by_key = load_about()
api = Api(os.environ["AIRTABLE_API_KEY"])
t = api.table(os.environ["AIRTABLE_BASE_ID"], os.environ.get("AIRTABLE_TABLE_NAME", "Groomers"))
recs = t.all(fields=["Name","City","State","Type","Rating","Review Count","Hours","Services","Specialties","Website URL"])

scores = []
detail = Counter()
for r in recs:
    f = r["fields"]
    s = 0.0
    # structured Airtable value facts
    if f.get("Services"): s += 2; detail["has_services"] += 1
    if f.get("Specialties"): s += 2; detail["has_specialties"] += 1
    if f.get("Rating") and f.get("Review Count"): s += 1; detail["has_socialproof"] += 1
    if f.get("Hours"): s += 1; detail["has_hours"] += 1
    if f.get("Website URL"): s += 0.5
    # joined about facts
    k = join_key(f.get("Name"), f.get("City"), f.get("State"))
    d = g = 0; own = False
    if k in about_by_key:
        d, g, own = about_facts(about_by_key[k])
        detail["matched"] += 1
    s += d * 1.0          # distinguishing about facts full weight
    s += min(g, 4) * 0.3  # boilerplate, capped + discounted
    if own: s += 1.5; detail["has_ownership"] += 1
    scores.append(s)

scores.sort()
n = len(scores)
print(f"Records: {n}  matched-to-about: {detail['matched']} ({100*detail['matched']/n:.1f}%)")
print(f"  has_services={detail['has_services']} has_specialties={detail['has_specialties']} "
      f"has_socialproof={detail['has_socialproof']} has_hours={detail['has_hours']} "
      f"has_ownership_identity={detail['has_ownership']}")
def pct(p): return scores[min(n-1, int(p*n))]
print(f"  score dist: min={scores[0]:.1f} p25={pct(.25):.1f} median={pct(.5):.1f} "
      f"p75={pct(.75):.1f} p90={pct(.9):.1f} max={scores[-1]:.1f}")
print("\nPass counts at candidate thresholds (>= score => INDEX):")
for thr in [3,4,5,6,7,8]:
    passed = sum(1 for x in scores if x >= thr)
    print(f"   thr {thr}: index {passed:>5} ({100*passed/n:.1f}%)  | noindex {n-passed:>5} ({100*(n-passed)/n:.1f}%)")
