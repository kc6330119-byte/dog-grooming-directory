"""
website_descriptions.py — production crawler that enriches listing descriptions
with original, fact-grounded content mined from each groomer's OWN website.

Pipeline (per listing):
  1. crawl    — fetch homepage + about/services pages, extract clean main text
                (trafilatura, precision-tuned). Cached to disk so re-runs and
                the LLM pass never re-crawl.
  2. compose  — Claude Haiku extracts distinguishing facts from the site text
                and writes an ORIGINAL 2-4 sentence description. It is grounded
                only in provided facts and must NOT copy site prose verbatim
                (avoids the scraped/copied-content policy problem). If the site
                yields nothing business-specific, it returns sufficient=false.
  3. fallback — listings with no usable site content keep the GBP fact-grounded
                description from generate_fact_descriptions.py.
  4. gate+write — run the same length/quality gate; write Airtable `Decription`.

SAFETY: dry-run by default, small --limit by default, results cached. Nothing
is written to Airtable without --apply. This is the production structure; the
Playwright fallback for JS-rendered sites (~25% of sites) is a documented hook,
intentionally not implemented yet (see crawl_site).

Usage:
  python3 website_descriptions.py                 # dry run, first 25 listings
  python3 website_descriptions.py --limit 200     # dry run, larger batch
  python3 website_descriptions.py --limit 200 --apply
  python3 website_descriptions.py --refresh        # ignore crawl cache, re-fetch
"""
import os, re, sys, json, time, argparse, hashlib
from pathlib import Path
from urllib.parse import urlparse, urljoin
from urllib import robotparser
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv("/Users/kevincollins/GitHub/dog-grooming-directory/.env", override=True)

BASE_DIR = Path("/Users/kevincollins/GitHub/dog-grooming-directory")
CACHE_DIR = BASE_DIR / "data" / "site_cache"
CRAWL_CACHE = CACHE_DIR / "crawl"
LLM_CACHE = CACHE_DIR / "llm"
for d in (CRAWL_CACHE, LLM_CACHE):
    d.mkdir(parents=True, exist_ok=True)

DESC_FIELD = "Decription"  # NB: misspelled in Airtable, matches the live field
HAIKU_MODEL = "claude-haiku-4-5-20251001"
UA = "Mozilla/5.0 (compatible; DogGroomerLocatorBot/1.0; +https://doggroomerlocator.com/about)"
TIMEOUT = 8
MIN_SITE_TEXT = 250          # below this, treat the site as no usable content
MIN_DESC_LEN = 300           # must match config.MIN_DESCRIPTION_LENGTH gate
CRAWL_DELAY = 0.5            # politeness pause between requests to the same host

SOCIAL = ("facebook.", "instagram.", "m.facebook", "fb.", "linktr.ee", "yelp.",
          "google.com", "sites.google", "business.site", "booking.", "moego.pet",
          "petco.com", "petsmart.com")

ABOUT_HINTS = ("about", "our-story", "who-we-are", "services", "grooming")


# ── crawl stage ───────────────────────────────────────────────────────────────

_robots_cache = {}

def robots_allows(url):
    """Best-effort robots.txt check, cached per host. Fails open on error."""
    try:
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in _robots_cache:
            rp = robotparser.RobotFileParser()
            rp.set_url(urljoin(base, "/robots.txt"))
            try:
                rp.read()
            except Exception:
                rp = None
            _robots_cache[base] = rp
        rp = _robots_cache[base]
        return rp.can_fetch(UA, url) if rp else True
    except Exception:
        return True


def _fetch(url):
    if not url.startswith("http"):
        url = "https://" + url
    if not robots_allows(url):
        return None, "robots-disallow", None
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT, allow_redirects=True)
        return r.status_code, r.text, r.url
    except Exception as e:
        return None, type(e).__name__, None


def _extract(html):
    if not html:
        return ""
    txt = trafilatura.extract(html, include_comments=False, include_tables=False,
                              favor_precision=True)
    return (txt or "").strip()


def _find_secondary(html, base_url, host):
    """Return up to 2 same-host about/services URLs to deepen context."""
    found = []
    try:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            txt = (a.get_text() or "").strip().lower()
            href = a["href"].lower()
            if any(h in txt or h in href for h in ABOUT_HINTS):
                full = urljoin(base_url, a["href"])
                if urlparse(full).netloc.lower().replace("www.", "") == host and full not in found:
                    found.append(full)
            if len(found) >= 2:
                break
    except Exception:
        pass
    return found


def crawl_site(url, use_cache=True):
    """Fetch homepage + secondary pages, return cleaned combined text or ''.

    NOTE: JS-rendered sites (Wix/Canva/app builders, ~25% of sites) return near-
    empty text here. The planned Playwright fallback would render those; it is
    intentionally not wired up yet. Such sites simply fall through to the GBP
    fallback description.
    """
    host = urlparse(url if url.startswith("http") else "http://" + url).netloc.lower().replace("www.", "")
    cache_path = CRAWL_CACHE / f"{hashlib.md5(url.encode()).hexdigest()}.json"
    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text())

    result = {"url": url, "host": host, "text": "", "status": None}
    if any(s in host for s in SOCIAL) or not host:
        result["status"] = "social/skip"
        cache_path.write_text(json.dumps(result))
        return result

    code, html, final = _fetch(url)
    result["status"] = code
    if code and isinstance(code, int) and code < 400 and html:
        parts = [_extract(html)]
        for sec in _find_secondary(html, final or url, host):
            time.sleep(CRAWL_DELAY)
            sc, sh, _ = _fetch(sec)
            if sc and isinstance(sc, int) and sc < 400:
                parts.append(_extract(sh))
        result["text"] = "\n".join(p for p in parts if p).strip()
    cache_path.write_text(json.dumps(result))
    return result


# ── compose stage (Haiku) ───────────────────────────────────────────────────

_anthropic_client = None

def _client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"], timeout=40.0)
    return _anthropic_client


LLM_SYSTEM = (
    "You write factual directory descriptions for dog grooming businesses. You are given "
    "raw text scraped from the business's own website. Extract concrete, business-specific "
    "facts: services, specialties, breeds, hours/days, location specifics, ownership, "
    "years of experience, certifications, pricing, and stated approach or philosophy. Then "
    "write an ORIGINAL 2-4 sentence description in your own words grounded ONLY in those "
    "facts plus the structured data provided. Rules: never copy sentences or distinctive "
    "phrases from the source text — paraphrase into your own words; never invent facts; no "
    "filler like 'nestled', 'boasting', 'dedicated team', 'state-of-the-art'. "
    "Set sufficient=true whenever the text contains ANY concrete information about THIS "
    "business (e.g. services offered, days open, self- vs full-service, owner or staff "
    "experience, location, or approach). Only set sufficient=false when the text is purely "
    "navigation links, cookie/legal notices, an error page, or says nothing specific about "
    "this business. Respond with strict JSON only."
)

LLM_SCHEMA_HINT = (
    'Return ONLY this JSON, nothing else: '
    '{"sufficient": true|false, '
    '"description": "the 2-4 sentence original description (empty string if not sufficient)"}'
)


def llm_compose(name, city, state, gbp_summary, site_text, use_cache=True):
    key = hashlib.md5(f"{name}|{city}|{state}|{site_text[:4000]}".encode()).hexdigest()
    cache_path = LLM_CACHE / f"{key}.json"
    if use_cache and cache_path.exists():
        return json.loads(cache_path.read_text())

    user = (
        f"Business: {name}\nLocation: {city}, {state}\n"
        f"Structured data (already known): {gbp_summary}\n\n"
        f"Website text (raw, may contain navigation/boilerplate):\n\"\"\"\n{site_text[:6000]}\n\"\"\"\n\n"
        f"{LLM_SCHEMA_HINT}"
    )
    try:
        msg = _client().messages.create(
            model=HAIKU_MODEL,
            max_tokens=600,
            system=LLM_SYSTEM,
            messages=[{"role": "user", "content": user}],
        )
        raw = msg.content[0].text.strip()
        raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
        data = json.loads(raw)
    except Exception as e:
        data = {"sufficient": False, "facts": {}, "description": "", "error": str(e)}
    cache_path.write_text(json.dumps(data))
    return data


# ── fallback + gate ───────────────────────────────────────────────────────────

_gbp = None

def gbp_fallback(record_fields):
    """Lazy-load the GBP fact-grounded generator and reuse its composer."""
    global _gbp
    if _gbp is None:
        import generate_fact_descriptions as g
        _gbp = {"mod": g, "about": g.load_about()}
    g = _gbp["mod"]
    k = g.join_key(record_fields.get("Name"), record_fields.get("City"), record_fields.get("State"))
    about = g.parse_about(_gbp["about"].get(k)) if k in _gbp["about"] else {}
    return g.compose(record_fields, about)


def gbp_summary(f):
    bits = [f.get("Type", "")]
    if f.get("Services"): bits.append("services: " + ", ".join(f["Services"]))
    if f.get("Specialties"): bits.append("specialties: " + ", ".join(f["Specialties"]))
    if f.get("Rating") and f.get("Review Count"):
        bits.append(f"{f['Rating']} stars / {f['Review Count']} reviews")
    return "; ".join(b for b in bits if b)


# ── orchestration ─────────────────────────────────────────────────────────────

def process_record(rec, use_cache):
    f = rec["fields"]
    url = (f.get("Website URL") or "").strip()
    out = {"id": rec["id"], "name": f.get("Name", ""), "source": "gbp", "description": "", "site_chars": 0}

    crawl = crawl_site(url, use_cache=use_cache) if url else {"text": ""}
    site_text = crawl.get("text", "")
    out["site_chars"] = len(site_text)

    if len(site_text) >= MIN_SITE_TEXT:
        result = llm_compose(f.get("Name", ""), f.get("City", ""), f.get("State", ""),
                             gbp_summary(f), site_text, use_cache=use_cache)
        desc = (result.get("description") or "").strip()
        if result.get("sufficient") and len(desc) >= MIN_DESC_LEN:
            out["source"] = "website"
            out["description"] = desc
            return out

    # fallback: GBP fact description
    out["description"] = gbp_fallback(f)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25, help="number of listings to process")
    ap.add_argument("--apply", action="store_true", help="write Decription to Airtable")
    ap.add_argument("--refresh", action="store_true", help="ignore crawl/LLM cache")
    ap.add_argument("--workers", type=int, default=6)
    args = ap.parse_args()
    use_cache = not args.refresh

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ANTHROPIC_API_KEY not set in .env — required for the compose stage.")

    api = Api(os.environ["AIRTABLE_API_KEY"])
    table = api.table(os.environ["AIRTABLE_BASE_ID"], os.environ.get("AIRTABLE_TABLE_NAME", "Groomers"))
    recs = table.all(fields=["Name", "City", "State", "Type", "Rating", "Review Count",
                             "Hours", "Services", "Specialties", "Website URL"])
    batch = recs[:args.limit]
    print(f"Processing {len(batch)} of {len(recs)} listings "
          f"({'APPLY' if args.apply else 'DRY RUN'}, cache={'on' if use_cache else 'off'})...\n")

    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_record, r, use_cache): r for r in batch}
        for i, fut in enumerate(as_completed(futs), 1):
            results.append(fut.result())
            if i % 25 == 0:
                print(f"  ...{i}/{len(batch)}")

    from collections import Counter
    src = Counter(r["source"] for r in results)
    web = [r for r in results if r["source"] == "website"]
    print(f"\n=== RESULTS ===")
    print(f"  website-derived (original): {src['website']} ({100*src['website']/len(results):.0f}%)")
    print(f"  GBP fallback: {src['gbp']} ({100*src['gbp']/len(results):.0f}%)")
    print("\n=== SAMPLE WEBSITE-DERIVED DESCRIPTIONS ===")
    for r in web[:6]:
        print(f"\n[{r['name']}] (site {r['site_chars']} chars)\n{r['description']}")

    if not args.apply:
        print("\nDRY RUN — nothing written. Re-run with --apply to write Airtable.")
        return

    updates = [{"id": r["id"], "fields": {DESC_FIELD: r["description"]}} for r in results if r["description"]]
    print(f"\n--apply: writing {len(updates)} records ...")
    for i in range(0, len(updates), 10):
        table.batch_update(updates[i:i+10])
        print(f"  updated {min(i+10, len(updates))}/{len(updates)}")
    print("Done.")


if __name__ == "__main__":
    main()
