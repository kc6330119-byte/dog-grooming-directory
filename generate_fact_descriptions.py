"""
generate_fact_descriptions.py — fact-grounded listing descriptions.

Replaces the hash-seeded spintax approach (enrich_descriptions.py) and the
AI-prose approach (auto_descriptions.py). Each description is assembled ONLY
from facts that are true for that specific business, joined from:
  - Airtable structured fields (Type, Rating, Review Count, Hours, Services,
    Specialties)
  - Outscraper `about` attribute JSON (ownership identity, service options,
    planning, accessibility, parking, payments, crowd), joined by
    normalized name+city+state.

Variation between listings comes from real differing facts, not shuffled
synonyms — removing the "scaled content abuse" spam signal. There is no length
padding: descriptions that come out under build.py's MIN_DESCRIPTION_LENGTH
(250) are left short on purpose and the existing quality gate will noindex them,
shrinking the indexed surface to genuinely fact-rich listings.

Usage:
  python3 generate_fact_descriptions.py            # dry run: stats + samples + review file
  python3 generate_fact_descriptions.py --apply    # write the "Decription" field in Airtable
"""
import os, re, json, glob, sys
from collections import Counter
import openpyxl
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv("/Users/kevincollins/GitHub/dog-grooming-directory/.env")
OUTSCRAPER_DIR = "/Users/kevincollins/GitHub/dog-grooming-directory/outscraper_processed"
DESC_FIELD = "Decription"  # NB: the live Airtable field is misspelled
APPLY = "--apply" in sys.argv

TYPE_PHRASE = {
    "Full-Service Salon": "full-service dog grooming salon",
    "Mobile Grooming": "mobile dog grooming service",
    "Pet Spa": "pet grooming spa",
    "Self-Service Wash": "self-service dog wash",
    "Pet Store with Grooming": "pet store offering dog grooming",
}

def norm(s):
    if s is None: return ""
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", str(s).strip().lower()))

def join_key(n, c, s): return f"{norm(n)}|{norm(c)}|{norm(s)}"

def oxford(items):
    items = [i for i in items if i]
    if not items: return ""
    if len(items) == 1: return items[0]
    if len(items) == 2: return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"

# ---------- load + dedupe Outscraper about ----------
def load_about():
    by_key = {}
    for path in sorted(glob.glob(os.path.join(OUTSCRAPER_DIR, "*.xlsx"))):
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        rows = ws.iter_rows(values_only=True)
        ci = {h: i for i, h in enumerate(norm(x) for x in next(rows))}
        if "name" not in ci or "about" not in ci:
            wb.close(); continue
        for row in rows:
            name = row[ci["name"]] if ci["name"] < len(row) else None
            city = row[ci["city"]] if "city" in ci and ci["city"] < len(row) else None
            state = row[ci["state"]] if "state" in ci and ci["state"] < len(row) else None
            about = row[ci["about"]] if ci["about"] < len(row) else None
            if not name or not about or not str(about).strip(): continue
            k = join_key(name, city, state)
            if k not in by_key or len(str(about)) > len(str(by_key[k])):
                by_key[k] = about
        wb.close()
    return by_key

def parse_about(raw):
    """Flatten about JSON into a deduped set of true attribute strings keyed by category."""
    try:
        data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        return {}
    if not isinstance(data, dict): return {}
    out = {}
    for cat, attrs in data.items():
        trues = set()
        if isinstance(attrs, dict):
            trues = {a for a, v in attrs.items() if v is True}
        elif isinstance(attrs, list):
            trues = {str(x) for x in attrs}
        if trues:
            out.setdefault(norm(cat), set()).update(trues)
    return out

# ---------- hours summary ----------
DAYS = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
NUMWORD = {1:"one",2:"two",3:"three",4:"four",5:"five",6:"six",7:"seven"}
def hours_clause(hours):
    if not hours: return ""
    h = str(hours)
    if h.lower().startswith("daily"):
        return "It is open daily"
    open_days = [d for d in DAYS if re.search(rf"{d}:\s*(?!Closed)\S", h)]
    if not open_days: return ""
    sat = "Saturday" in open_days
    sun = "Sunday" in open_days
    n = len(open_days)
    if n == 7: base = "It is open seven days a week"
    else:
        unit = "day" if n == 1 else "days"
        base = f"It is open {NUMWORD.get(n, n)} {unit} a week"
    if sat and sun: base += ", including weekends"
    elif sat: base += ", including Saturdays"
    return base

# ---------- compose ----------
def compose(f, about):
    name = (f.get("Name") or "").strip()
    city = (f.get("City") or "").strip()
    state = (f.get("State") or "").strip()
    typ = f.get("Type") or ""
    phrase = TYPE_PHRASE.get(typ, "dog grooming business")
    loc = f"{city}, {state}".strip(", ")
    sentences = []

    # 1. opening (always)
    sentences.append(f"{name} is a {phrase}" + (f" in {loc}." if loc else "."))

    # 2. ownership identity
    own = []
    for cat in ("from the business", "other"):
        for a in about.get(cat, set()):
            al = a.lower()
            if "women-owned" in al: own.append("women-owned")
            elif "veteran-owned" in al: own.append("veteran-owned")
            elif "lgbtq" in al and "owned" in al: own.append("LGBTQ+-owned")
            elif "small business" in al: own.append("a small business")
            elif "identifies as" in al: own.append(al.replace("identifies as", "").strip())
    own = list(dict.fromkeys(own))
    if own:
        sentences.append(f"The business identifies as {oxford(own)}.")

    # 3. services / specialties (drop specialties already covered by services)
    services = f.get("Services") or []
    specialties = f.get("Specialties") or []
    svc_lower = {s.lower() for s in services}
    specialties = [s for s in specialties if s.lower() not in svc_lower]
    if services:
        sentences.append(f"Grooming services include {oxford(services)}.")
    if specialties:
        sentences.append(f"It specializes in {oxford(specialties)}.")

    # 4. service options
    opts = about.get("service options", set())
    opt_phrases = []
    for a in opts:
        al = a.lower()
        if "onsite" in al: opt_phrases.append("onsite services")
        elif "curbside" in al: opt_phrases.append("curbside service")
        elif "online appointment" in al: opt_phrases.append("online appointment booking")
        elif "in-store" in al: opt_phrases.append("in-store shopping")
        elif "same-day" in al: opt_phrases.append("same-day service")
    opt_phrases = list(dict.fromkeys(opt_phrases))
    if opt_phrases:
        sentences.append(f"Available options include {oxford(opt_phrases)}.")

    # 5. planning
    plan = about.get("planning", set())
    if any("required" in p.lower() for p in plan):
        sentences.append("Appointments are required.")
    elif any("recommend" in p.lower() for p in plan):
        sentences.append("Appointments are recommended.")

    # 6. practical/visit info — one concise clause
    practical = []
    if any("wheelchair accessible entrance" in a.lower() for a in about.get("accessibility", set())):
        practical.append("a wheelchair-accessible entrance")
    parking = about.get("parking", set())
    if any("free" in p.lower() for p in parking):
        practical.append("free parking")
    pay = about.get("payments", set())
    pay_kinds = []
    if any("credit" in p.lower() for p in pay): pay_kinds.append("credit cards")
    if any("debit" in p.lower() for p in pay): pay_kinds.append("debit cards")
    if any("nfc" in p.lower() or "mobile payment" in p.lower() for p in pay): pay_kinds.append("mobile payments")
    if practical:
        clause = f"The location offers {oxford(practical)}"
        if pay_kinds:
            clause += f", and accepts {oxford(pay_kinds)}"
        sentences.append(clause + ".")
    elif pay_kinds:
        sentences.append(f"It accepts {oxford(pay_kinds)}.")

    # 7. crowd
    crowd = about.get("crowd", set())
    crowd_phrases = []
    if any("lgbtq" in c.lower() for c in crowd): crowd_phrases.append("LGBTQ+ friendly")
    if any("transgender" in c.lower() for c in crowd): crowd_phrases.append("a transgender safe space")
    if crowd_phrases:
        sentences.append(f"The business is described as {oxford(crowd_phrases)}.")

    # 8. hours
    hc = hours_clause(f.get("Hours"))
    if hc:
        sentences.append(hc + ".")

    # 9. social proof (last)
    rating = f.get("Rating")
    reviews = f.get("Review Count")
    if rating and reviews:
        try:
            rn = int(reviews)
            sentences.append(f"It holds a {rating}-star rating from {rn:,} Google review" + ("s" if rn != 1 else "") + ".")
        except (ValueError, TypeError):
            pass

    return " ".join(sentences)

# ---------- run ----------
def main():
    about_by_key = load_about()
    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(os.environ["AIRTABLE_BASE_ID"], os.environ.get("AIRTABLE_TABLE_NAME", "Groomers"))
    recs = table.all(fields=["Name","City","State","Type","Rating","Review Count","Hours","Services","Specialties"])

    results = []  # (rec_id, name, text, length)
    for r in recs:
        f = r["fields"]
        k = join_key(f.get("Name"), f.get("City"), f.get("State"))
        about = parse_about(about_by_key.get(k)) if k in about_by_key else {}
        text = compose(f, about)
        results.append((r["id"], f.get("Name",""), text, len(text)))

    lengths = sorted(x[3] for x in results)
    n = len(lengths)
    def pct(p): return lengths[min(n-1, int(p*n))]
    idx = sum(1 for L in lengths if L >= 250)
    print(f"Generated {n} descriptions.")
    print(f"  length: min={lengths[0]} p25={pct(.25)} median={pct(.5)} p75={pct(.75)} p90={pct(.9)} max={lengths[-1]}")
    print(f"  >=250 chars (will INDEX): {idx} ({100*idx/n:.1f}%)   <250 (will noindex): {n-idx} ({100*(n-idx)/n:.1f}%)")

    # samples across the spectrum
    by_len = sorted(results, key=lambda x: x[3])
    picks = [by_len[int(p*(n-1))] for p in (0.10, 0.35, 0.55, 0.75, 0.90, 0.98)]
    review_lines = ["# Fact-grounded description samples\n"]
    print("\n===== SAMPLES (low → high information density) =====")
    for _id, name, text, L in picks:
        block = f"[{L} chars] {name}\n{text}\n"
        print("\n" + block)
        review_lines.append(f"## {name}  _({L} chars, {'INDEX' if L>=250 else 'noindex'})_\n\n{text}\n")
    with open("/Users/kevincollins/GitHub/dog-grooming-directory/FACT_DESCRIPTIONS_SAMPLE.md", "w") as fh:
        fh.write("\n".join(review_lines))
    print("\nWrote review file: FACT_DESCRIPTIONS_SAMPLE.md")

    if not APPLY:
        print("\nDRY RUN — nothing written. Re-run with --apply to write the Decription field.")
        return

    print("\n--apply: writing to Airtable ...")
    updates = [{"id": _id, "fields": {DESC_FIELD: text}} for _id, _n, text, _L in results]
    for i in range(0, len(updates), 10):
        table.batch_update(updates[i:i+10])
        print(f"  updated {min(i+10, len(updates))}/{len(updates)}")
    print("Done.")

if __name__ == "__main__":
    main()
