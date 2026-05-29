# AdSense "Low Value Content" Remediation Playbook

A portable process for fixing directory sites that failed (or are at risk of failing)
Google AdSense for **"Low Value Content"** — and the same signal that demotes them in
Google Search. Built and validated on **Dog Groomer Locator**; written so it can be
recreated on the sister sites (Holistic Vet Directory, etc.).

## When to use this

Use it on any directory built on the same infrastructure (Python static-site generator →
Airtable CMS → Netlify) whose listing descriptions are **spun/templated** (hash-seeded
spintax, fixed sentence banks, or synonym-shuffled boilerplate). That pattern is Google's
March-2024 **"scaled content abuse"** — the literal root cause of the failures. The fix is
**original per-page value**, not more HTML/technical polish.

## The two-phase fix (what we built)

1. **Fact-grounded descriptions (baseline).** Replace every spun description with prose
   composed *only* from facts that are true for that specific business — structured fields
   (type, rating, hours, services, specialties) joined to the source's "about"/attributes
   data. Variation comes from *real differing facts*, not synonym shuffling, so it stops
   triggering the scaled-content signal. This covers 100% of listings.
2. **Website enrichment (per-page value).** For listings that have their own website,
   crawl it, have an LLM extract distinguishing facts and write an **original** description,
   and fall back to the Phase-1 description when the site is dead/JS-rendered/boilerplate.
   This is what actually adds value *beyond the business's own Google profile* — the thing
   the reviewer is looking for.

Ship Phase 1 to everything first; Phase 2 is an incremental quality upgrade on top.

---

## Ready-to-paste prompt

> Copy everything in the block below into a fresh Claude Code session **in the target
> site's repo**. It is written to discover that repo's specifics rather than assume Dog
> Groomer Locator's, and it carries every hard-won constraint so the new instance doesn't
> repeat our mistakes.

```text
You are remediating this directory site for Google AdSense "Low Value Content" (and the
matching Google Search quality demotion). I have a proven process from a sister site; your
job is to recreate it here, adapting to THIS repo's specifics.

ROOT CAUSE (do not re-litigate): the listing descriptions are spun/templated synthetic
content (Google's "scaled content abuse," March 2024 policy). Pages assembled purely from
scraped map data + spun text add no value over the business's own Google Business Profile.
The fix is ORIGINAL per-page value — NOT more HTML hygiene, NOT a bigger spintax bank, NOT
FAQ/Q&A blocks on listing pages (that sank one of our sites).

STEP 0 — INVESTIGATE FIRST, do not assume. Report back what you find before writing code:
  - The build system (build.py or equivalent), how it reads the CMS, and how it renders
    listing pages.
  - The CMS schema (Airtable field names — note any misspellings like our "Decription";
    read both spellings if present). Identify: name, city, state, type/category, rating,
    review count, hours, services, specialties, website URL, description.
  - The current description generator(s). Identify which one is the spun/synthetic one
    (it's the root cause — do NOT reuse or extend it).
  - The content-quality gate: is there a min-length + vocabulary + junk-filter + contact-
    signal check that decides indexed vs. noindexed? What's the threshold and current
    indexed ratio?
  - Any source "about"/attributes export (e.g. Outscraper JSON) that can be joined to the
    CMS by normalized name+city+state. Measure the join coverage.
  - Any "protected URLs" mechanism that grandfathers pages already earning search traffic
    past the gate (so a ranking page can't get noindexed on the next build).

PHASE 1 — FACT-GROUNDED DESCRIPTIONS:
  - Write a generator that composes each description from ONLY-TRUE clauses for that
    business: ownership/identity, services & specialties (dedupe specialties already named
    in services), hours, practical info, social proof, etc. Variation must come from real
    differing facts, never synonym shuffling.
  - It must ONLY UPDATE existing CMS records, NEVER INSERT new ones.
  - No length padding: descriptions that fall below the gate stay short and get noindexed —
    that deliberately shrinks the synthetic indexed surface. Don't pad to clear the gate.
  - Dry-run by default; require an explicit --apply flag to write. Back up the existing
    descriptions to a timestamped JSON keyed by record id before the first --apply.
  - Raise/confirm the gate so it indexes only listings with genuinely sufficient content.

PHASE 2 — WEBSITE-ENRICHMENT CRAWLER (only after Phase 1 ships):
  Pipeline per listing: crawl the business's OWN website (homepage + about/services pages)
  -> LLM extracts distinguishing facts and writes an ORIGINAL 2-4 sentence description ->
  fall back to the Phase-1 description -> run the same gate -> write the CMS field.
  - CRAWLING: be polite. Descriptive bot User-Agent with a contact URL, robots.txt-aware
    (fail open), short timeouts, a delay between requests to the same host, low concurrency.
    Cache every crawl AND every LLM response to disk so re-runs and tuning never re-fetch
    or re-bill. Skip social/aggregator/booking domains (facebook, instagram, yelp, google,
    sites.google, business.site, booking/moego, chain stores) — they aren't the business's
    own site.
  - EXTRACTION: use a cheap fast model (we used Claude Haiku). Extract concrete facts, then
    write ORIGINAL prose grounded only in those facts + the structured data. NEVER copy
    sentences or distinctive phrases from the source (that's scraped-content + copyright
    violation — the very thing we're fixing). NEVER invent facts. Ban filler ("nestled",
    "boasting", "dedicated team", "state-of-the-art"). Return strict JSON
    {"sufficient": bool, "description": str}.
  - JS-rendered sites (Wix/Canva/app builders, ~25% of sites) return near-empty text;
    let them fall through to the Phase-1 fallback. A Playwright renderer is an optional
    later hook — leave it documented but unimplemented unless asked.
  - Defaults: dry-run, small --limit (e.g. 25). Validate output quality on a small batch
    before any large/full run.

GOTCHAS WE HIT (save yourself the debugging):
  - load_dotenv from .env with override=True. A shell may export an EMPTY API-key var that
    silently shadows the real key in .env; guard for empty (not just missing) keys.
  - LLM sufficiency prompts skew too strict — ordinary marketing prose IS fact-rich content;
    only mark insufficient for pure navigation/cookie/error/empty pages.
  - Give the LLM enough max_tokens (we needed ~600); too low TRUNCATES the JSON mid-string
    and every parse silently fails. Keep the output schema minimal (just the fields you use).

NEVER:
  - Insert new CMS records (only update existing).
  - Copy/republish website text verbatim.
  - Add aggregateRating/review structured data from scraped ratings (structured-data-spam
    manual-action risk).
  - Commit secrets; .env is gitignored.

DEPLOY: build locally, verify rendered pages (indexed ones have a real body description +
canonical + clean meta; noindexed ones carry noindex and suppressed ads), then hand the
git push / Netlify deploy to me — I drive deploys.

AFTER ANY DATA REFRESH (document this in the repo's CLAUDE.md): re-run the protected-URLs
extractor against a fresh Search Console export, then re-run the description generator so
new listings get the same treatment.
```

---

## Reference: files this produced on Dog Groomer Locator

Names will differ per repo, but the shapes are reusable:

- `generate_fact_descriptions.py` — Phase 1 generator (compose-only-true-clauses, dry-run,
  `--apply`, updates the misspelled `Decription` field, never inserts).
- `website_descriptions.py` — Phase 2 crawler (crawl → Haiku extract+compose → GBP fallback
  → gate → write; disk-cached crawl + LLM; robots-aware; dry-run + `--limit` defaults).
- `poc_site_extraction.py` — read-only yield measurement run *before* building the crawler
  (sampled ~60 real domains; ~70% usable text yield, ~25% JS-rendered).
- `analyze_fact_coverage.py`, `calibrate_gate.py` — measured the structured-data join
  coverage and calibrated the gate threshold.
- `data/decription_backup_*.json` — timestamped backup of pre-remediation descriptions.
- Gate lives in `build.py` (`description_quality_check`, `annotate_listing_quality`,
  `public_groomers`) + `config.py` (`MIN_DESCRIPTION_LENGTH`, vocab/junk term lists).

## Honest framing to keep in mind

Phase 1 alone removes the spun-content signal but doesn't add value beyond the GBP — "better
odds than a spun site, not a guarantee of approval." Phase 2 (real website-derived content)
is what genuinely adds original value. Don't oversell Phase 1 as a fix on its own.
