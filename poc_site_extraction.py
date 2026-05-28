"""
PROOF OF CONCEPT (read-only, no Airtable writes) — measure how much usable,
fact-rich content we can realistically extract from groomers' own websites.

Samples ~60 real-domain listings, fetches the homepage + a best-guess About
page, extracts main content with trafilatura, and reports:
  - fetch success / dead / blocked
  - usable-content yield (enough real text to mine)
  - likely JS-rendered (fetched but near-empty text)
  - what differentiating FACTS are detectable (years in business,
    certifications, breeds, philosophy signals)

This is a yield measurement, not the production crawler. Politeness: low
concurrency, short timeouts, descriptive UA, each domain hit at most twice.
"""
import os, re, sys, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse, urljoin

import requests
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv("/Users/kevincollins/GitHub/dog-grooming-directory/.env")

SAMPLE_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 60
UA = "Mozilla/5.0 (compatible; DogGroomerLocatorBot/1.0; +https://doggroomerlocator.com/about)"
TIMEOUT = 8
SOCIAL = ("facebook.", "instagram.", "m.facebook", "fb.", "linktr.ee", "yelp.",
          "google.com", "sites.google", "business.site", "booking.", "moego.pet",
          "petco.com", "petsmart.com")

CERT_PAT = re.compile(r"\b(NDGAA|IPG|certified (?:master )?groomer|master groomer|"
                      r"national dog groomers|AKC|fear free|certified professional)\b", re.I)
YEARS_PAT = re.compile(r"\b(?:since|established|est\.?|serving\s+\w+\s+since)\s+(19\d{2}|20\d{2})\b", re.I)
YEARS_PAT2 = re.compile(r"\b(\d{1,2})\+?\s+years?\s+(?:of\s+)?(?:experience|in business|grooming)\b", re.I)
PHILOSOPHY = re.compile(r"\b(stress[- ]free|low[- ]stress|family[- ]owned|one[- ]on[- ]one|"
                        r"by appointment|small dogs only|cage[- ]free|hand[- ]?strip|"
                        r"holistic|all[- ]natural|hypoallergenic)\b", re.I)


def host(u):
    try:
        return urlparse(u if u.startswith("http") else "http://" + u).netloc.lower().replace("www.", "")
    except Exception:
        return ""


def fetch(url):
    if not url.startswith("http"):
        url = "https://" + url
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code, r.text, r.url
    except Exception as e:
        return None, f"{type(e).__name__}", None


def find_about(html, base_url):
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            txt = (a.get_text() or "").strip().lower()
            href = a["href"].lower()
            if "about" in txt or "/about" in href or "our-story" in href or "who-we-are" in href:
                return urljoin(base_url, a["href"])
    except Exception:
        pass
    return None


def extract_text(html):
    if not html:
        return ""
    txt = trafilatura.extract(html, include_comments=False, include_tables=False,
                              no_fallback=False, favor_recall=True)
    return (txt or "").strip()


def mine_facts(text):
    facts = {}
    yrs = YEARS_PAT.search(text)
    yrs2 = YEARS_PAT2.search(text)
    if yrs:
        facts["since_year"] = yrs.group(1)
    elif yrs2:
        facts["years_experience"] = yrs2.group(1)
    certs = sorted(set(m.group(0) for m in CERT_PAT.finditer(text)))
    if certs:
        facts["certifications"] = certs[:3]
    phil = sorted(set(m.group(0).lower() for m in PHILOSOPHY.finditer(text)))
    if phil:
        facts["signals"] = phil[:5]
    return facts


def process(rec):
    f = rec["fields"]
    url = (f.get("Website URL") or "").strip()
    name = f.get("Name", "")
    h = host(url)
    out = {"name": name, "host": h, "status": None, "text_len": 0, "facts": {}, "category": ""}
    if any(s in h for s in SOCIAL) or not h:
        out["category"] = "social/skip"
        return out
    code, html, final = fetch(url)
    out["status"] = code
    if code is None:
        out["category"] = f"dead/error ({html})"
        return out
    if code >= 400:
        out["category"] = f"http {code}"
        return out
    text = extract_text(html)
    # try about page for more signal
    about_url = find_about(html, final or url)
    about_text = ""
    if about_url and host(about_url) == h:
        time.sleep(0.3)
        ac, ah, _ = fetch(about_url)
        if ac and ac < 400:
            about_text = extract_text(ah)
    combined = (text + "\n" + about_text).strip()
    out["text_len"] = len(combined)
    out["facts"] = mine_facts(combined)
    out["sample"] = combined[:240].replace("\n", " ")
    if len(combined) >= 250:
        out["category"] = "USABLE"
    elif code < 400:
        out["category"] = "fetched but thin (likely JS-rendered)"
    return out


def main():
    api = Api(os.environ["AIRTABLE_API_KEY"])
    t = api.table(os.environ["AIRTABLE_BASE_ID"], os.environ.get("AIRTABLE_TABLE_NAME", "Groomers"))
    recs = t.all(fields=["Name", "Website URL"])
    real = [r for r in recs if (r["fields"].get("Website URL") or "").strip()
            and not any(s in host(r["fields"]["Website URL"]) for s in SOCIAL)]
    random.seed(42)
    sample = random.sample(real, min(SAMPLE_SIZE, len(real)))
    print(f"Sampling {len(sample)} real-domain sites (of {len(real)} candidates)...\n")

    results = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(process, r): r for r in sample}
        for fut in as_completed(futs):
            results.append(fut.result())

    from collections import Counter
    cats = Counter()
    for r in results:
        c = r["category"]
        key = ("USABLE" if c == "USABLE"
               else "fetched-thin (JS?)" if "JS" in c
               else "social/skip" if "social" in c
               else "dead/error" if "dead" in c or "error" in c
               else "http-error")
        cats[key] += 1
    usable = [r for r in results if r["category"] == "USABLE"]
    print("=== YIELD ===")
    for k in ["USABLE", "fetched-thin (JS?)", "http-error", "dead/error", "social/skip"]:
        print(f"  {cats.get(k,0):>3}  {k}")
    print(f"\nUsable yield: {len(usable)}/{len(sample)} = {100*len(usable)/len(sample):.0f}%")
    # fact richness among usable
    with_year = sum(1 for r in usable if "since_year" in r["facts"] or "years_experience" in r["facts"])
    with_cert = sum(1 for r in usable if "certifications" in r["facts"])
    with_sig = sum(1 for r in usable if "signals" in r["facts"])
    print(f"  of usable: {with_year} have years/since, {with_cert} have certifications, {with_sig} have philosophy signals")
    print(f"  median usable text length: {sorted(len(str(r.get('sample',''))) for r in usable)}")

    print("\n=== SAMPLE USABLE EXTRACTIONS ===")
    for r in usable[:8]:
        print(f"\n[{r['host']}] {r['name']}  ({r['text_len']} chars)")
        print(f"  facts: {r['facts']}")
        print(f"  text: {r['sample']}")

    print("\n=== A FEW FAILURES (for diagnosis) ===")
    for r in [x for x in results if x["category"] not in ("USABLE", "social/skip")][:8]:
        print(f"  [{r['host']}] {r['category']}  (text {r['text_len']})")


if __name__ == "__main__":
    main()
