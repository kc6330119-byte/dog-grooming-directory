# Dog Groomer Locator — Independent AdSense & SEO Audit (2026-05-28)

**Auditor:** Claude (Opus 4.8), independent pass
**Method:** Analyzed the 28-day GSC Performance export (2026-04-01 → 2026-05-26), the current `dist/` build output (4,668 sitemap URLs / 5,316 generated groomer pages), `build.py`, `config.py`, `enrich_descriptions.py`, templates, and the two prior audits (2026-04-29, 2026-05-24). No code or site changes were made — this is advisory only, per your change-freeze.
**Scope:** AdSense "Low Value Content" risk + organic search health, with specific attention to *why* the two sister directories failed and whether DGL shares that failure mode.

---

## Executive Summary

The May 24 remediations were the right hygiene work and they landed cleanly. Technically, the site is in good shape: ads are gated off, thin listings are `noindex` and **orphaned** (0 indexable pages link to them), `.html` URLs 301 to extensionless canonicals, the sitemap is clean (0 `.html`, 0 duplicates), and the blog posts are genuinely substantial (1,500–2,700 words).

**But the hygiene fixes do not address the root problem, and your fresh GSC data confirms the root problem is actively biting.** Two findings dominate everything else:

1. **The search-visibility collapse did not recover — it deepened.** The May 13 cliff the prior audit flagged is now a **sustained 2-week suppression through May 26**. Daily impressions sit at 70–150 (down from an 8,000–10,500 peak in late April) and average position has decayed from ~15 to **40–60**. This is not "fewer pages indexed." Site-wide *position* decay is a **quality/ranking demotion** — Google has already made a low-value judgment about this site.

2. **The listing descriptions are programmatically spun, and that is the same fingerprint that failed your other two sites.** `enrich_descriptions.py` is a Mad-Libs/spintax generator: it assembles every description from a fixed bank of ~30 template sentences (6 openings × 5 type sentences × 4 service intros × 3 price × 3 rating × 4 closings × 3 hours), selected by bit-shifts of the slug's MD5 hash. The output *looks* varied (no two are verbatim-identical) but is structurally identical at scale. This is textbook **scaled content abuse** under Google's March 2024 spam policy, and it is the literal definition of AdSense's "low-value, mass-produced content."

**My verdict: in its current form, DGL is likely to be rejected for the same "Low Value Content" reason as the other two sites.** The shared infrastructure produces the shared failure: a 99.1%-directory site whose pages are synthetic recombinations of scraped Google-Maps data, providing no added value over the businesses' own Google listings. The technical polish doesn't change that classification.

On your change-freeze: **the polish work is worth keeping frozen, but I would not expect the pending review to pass.** You have a decision to make (see "What to do about the pending review" at the end) — there's little downside to letting it run, but plan for a rejection and a real content strategy rather than another polish pass.

### Top priorities
1. **Stop relying on spun descriptions** — replace the generation *method*, not just bad phrases (root cause; High).
2. **Diagnose the position decay in the GSC UI** — confirm whether it's a quality demotion vs. an indexing wound (Critical to know before any move).
3. **Solve the "added value" problem** — give listing pages something Google's own Business Profile doesn't have (High; this is the actual AdSense bar).
4. **Raise the editorial floor meaningfully** — 0.9% editorial is unchanged and still reads as a directory, not a publisher (High).

---

## What the prior audits got right (and what I'm confirming)

I independently verified the May 24 remediations in the current build, and they hold up:

| Remediation | Status in current `dist/` |
|---|---|
| Ads gated (`ADSENSE_ENABLED` off, no placeholders) | ✅ Confirmed |
| Thin listings `noindex` + ads suppressed | ✅ 833 of 5,316 groomer pages noindexed |
| Thin listings excluded from public grids/sitemap | ✅ Orphaned — 0 indexable pages link to sampled thin slugs |
| `.html` → extensionless 301s | ✅ 6,063 redirect rules; canonicals point extensionless |
| Sitemap clean | ✅ 0 `.html`, 0 duplicate URLs |
| Quality gate (250-char min, vocab, junk filter) | ✅ In `description_quality_check()` |
| OG image, `ads.txt`, broken `/category/mobile` link | ✅ All present/fixed |

**So this audit does not re-litigate those.** They were necessary. They are just not sufficient, because they treat symptoms (which pages get indexed, where ads show) rather than the cause (what the pages actually *are*).

---

## SEO Findings

### Finding 1 — The visibility collapse is sustained and looks like a quality demotion — **CRITICAL**

**Evidence (full 56-day export):**

| Period | Avg impressions/day | Avg position |
|---|---:|---:|
| Late-April peak (Apr 27–May 1) | ~8,000–10,500 | ~15 |
| Mid–late May (May 17–26) | **70–150** | **40–60** |

- Total: 248 clicks / 93,143 impressions over 56 days = **0.27% CTR**.
- Last 10 days (May 17–26): essentially **0–1 clicks/day**, impressions flat at the floor, position 24–60.

**Interpretation (this is where I differ from the May 24 read).** The prior audit leaned toward a self-inflicted indexing wound — too many pages noindexed at once + a stale `gsc_protected_urls.txt`. That's plausible for the *impression volume* drop. But it doesn't explain the **site-wide average-position decay from ~15 to ~50**. If the cause were simply "fewer URLs in the index," the surviving URLs would hold their positions and you'd see lower impressions at a *stable* position. Instead, ranking degraded across the board. **That pattern is consistent with an algorithmic quality demotion** (Helpful Content / scaled-content systems), not just a smaller index.

This matters enormously for AdSense: Google Search quality systems and AdSense content-policy review draw on the same underlying "is this helpful/original content" signals. **A site Search has already demoted as low-value is a site AdSense is primed to reject.**

**Recommended (diagnostic, no site change):** In the GSC UI (not the export), check:
- **Page Indexing** report for May 10–26: how many URLs flipped to "Crawled – currently not indexed" or "Discovered – not indexed"? A spike there = quality signal, not just your noindex.
- **Crawl Stats** for the same window.
- **URL Inspection** on 3 URLs that *had* impressions in April and now don't: one state page, one high-impression groomer page, one extensionless URL with `.html` history. Look at "Page indexing" status and last-crawl date.

This tells you which hypothesis is true *before* you touch anything.

### Finding 2 — Traffic is almost entirely navigational/brand intent, where the directory adds no value — **HIGH**

**Evidence (Queries + Pages sheets):**
- Top queries are business names, not categories: *"that pet spot," "woof gang santa clara reviews," "paragon grooming & pet co. lynden reviews," "petsense by tractor supply anderson grooming."*
- Page clicks concentrate on individual `/groomer/` pages (233 of 248 clicks). State pages get impressions but ~0 clicks; category pages got **0 clicks on 1,269 impressions**; blog posts are 1 click / 88 impressions.
- Broad discovery terms are not competitive: *"dog grooming near me"* and *"best dog groomers near me"* sit at position 27–63 with 0 clicks.

**Why this is the core AdSense problem, not just an SEO observation.** When someone searches *"woof gang santa clara reviews,"* they want that business's reviews — which Google already shows in the Business Profile, with real reviews, real photos, hours, and a map. Your page for that business offers: a **scraped** photo (downloaded from Google Places), a Google-derived star rating, and a **synthetic** description. There is no original review, no firsthand visit, no verified detail, nothing the user couldn't get one tap away from Google itself. **That is the precise definition of "replicated content with no added value"** in the AdSense Publisher Policies — and it describes 99.1% of your indexable pages.

**Recommended:** Decide what the directory *uniquely* offers. Options that create genuine added value: structured price ranges aggregated by service/size, side-by-side comparison within a city, a verification/"last reviewed" layer with a human signal, owner-submitted info, or editorial curation ("best for anxious dogs in Phoenix"). Without one of these, the listing pages cannot clear the AdSense bar no matter how clean the HTML is.

### Finding 3 — Editorial ratio is unchanged at 0.9% — **HIGH**

**Evidence:** Current sitemap = 4,668 URLs. Directory (groomer/city/state/category) = 4,624 (99.1%). Editorial/static = 44 (0.9%): 35 blog posts + breed guide + 8 static pages. **Identical ratio to the April 29 audit.**

The 35 blog posts are actually good — 1,500–2,700 words, credentialed authors (E-E-A-T is set up correctly in `config.AUTHORS`). The problem is they're a rounding error against 4,483 synthetic listing pages, and they earn ~0 traffic. To a reviewer sampling the site, it reads as a directory with a token blog.

**Recommended:** This is not "publish filler to hit a ratio." It's that a publisher-grade site needs a publisher-grade content body. Two levers:
- **Lower the directory ceiling:** raise quality thresholds so only listings with *genuinely original* content index (this also shrinks the synthetic-content surface from Finding 4).
- **Raise the editorial floor:** the blog is your strongest asset and gets no traffic — that's a distribution/internal-linking problem worth fixing, plus continued cadence on high-intent topics (grooming prices by size/coat, mobile grooming by metro, anxious/senior care, breed cadence).

---

## AdSense / Content-Quality Findings

### Finding A — Listing descriptions are programmatically spun (scaled content) — **HIGH / root cause**

**Evidence:** `enrich_descriptions.py` generates each description deterministically from the slug's MD5 hash:

```
h = int(hashlib.md5(slug.encode()).hexdigest(), 16)
opening      = OPENINGS[h % 6]
service_intro= SERVICE_INTROS[(h >> 4) % 4]
price        = PRICE_SENTENCES[pr][(h >> 8) % 3]
rating       = RATING_SENTENCES[(h >> 12) % 3]
hours        = HOURS_SENTENCES[(h >> 20) % 3]
...
```

The entire corpus is recombinations of ~30 fixed template sentences (e.g. *"{name} is a professional dog grooming business serving pet owners in {city}, {state}."* / *"As a full-service salon, they handle everything from baths and haircuts to nail trimming..."*). The docstring even describes the goal as producing *"natural-sounding, diverse descriptions that rebuild identically every time."*

**Why "diverse-looking" doesn't save it.** I checked: no whole sentence repeats more than twice across the 4,483 indexable descriptions, so the 250-char/junk/repetition gate passes them. But Google's spam classifiers don't match on verbatim duplication — they detect **template/pattern at scale**, and a hash-seeded phrase shuffler is exactly the pattern. Surface variation is what spintax was *designed* to produce; it's a known, detectable technique, and Google's March 2024 "scaled content abuse" policy explicitly covers programmatic text generation regardless of how varied it appears.

**This is almost certainly the shared cause of all three sites' failures.** Same generator (the file header notes it's *"Adapted from senior-home-care-directory"*) → same synthetic fingerprint → same "Low Value Content" outcome. It also fits the timing of the Search demotion in Finding 1.

**Recommended (this is the hard one, and the real fix):**
- The honest answer is that **mass auto-generated descriptions cannot be made AdSense-safe by tweaking the templates** — a bigger phrase bank is still spintax.
- Two viable directions: **(a)** Don't synthesize at all — display only genuinely available data (services, hours, map, real Google reviews via permitted API display) and *no* prose description, letting structure rather than fake prose carry the page; or **(b)** invest in genuinely original per-listing content (human-written or research-backed local detail) for a *small, curated* set of listings and index only those, noindexing the long tail.
- Either way, **shrink the indexable synthetic surface dramatically.** 4,483 spun pages is the liability; 200 genuinely useful ones is an asset.

### Finding B — 833 synthetic/thin pages still render to users on direct hit — **MEDIUM**

**Evidence:** Thin listings are `noindex` and orphaned (good — verified), but `build_groomer_pages()` still emits a full page for every groomer. A reviewer or crawler arriving via an old Google-indexed `.html` URL (236 such URLs still drew impressions in this export) lands on a real, rendered low-value page.

**Recommended:** For failing listings, consider serving a genuinely minimal stub (no synthetic prose, no schema) rather than a full detail page, or return them to non-public status. The orphaning is good defense; it isn't complete cover during an active review when legacy URLs are still in Google's index.

### Finding C — Scraped Google Places photos as the only listing imagery — **MEDIUM**

**Evidence:** `download_groomer_images()` pulls each listing's image from the Google Places photo URL and stores it locally. Combined with Google-derived ratings and synthetic text, the entire listing page is **assembled from Google's own data** — reinforcing the "no added value / replicated content" read. (There may also be a licensing question around redistributing Places photos, but the AdSense-relevant point is the added-value one.)

**Recommended:** Original imagery is hard at scale; at minimum don't let scraped photo + scraped rating + spun text be the *whole* page. Whatever unique value you add in Finding 2 should be visually present.

---

## Prioritized Action Plan

**Before any further action — diagnose (no changes):**
1. Pull the GSC **Page Indexing** + **Crawl Stats** + **URL Inspection** data described in Finding 1 to confirm quality-demotion vs. indexing-wound. This determines everything downstream.

**If/when you resume changes (post-review, or if you decide not to wait):**
2. **Replace the description strategy** (Finding A) — stop spinning; index only listings with genuinely original content, or drop synthetic prose entirely. This is the single highest-leverage change and the one that separates DGL from the two failed sites.
3. **Define and ship the directory's added value** (Finding 2) — comparison, verification, aggregated pricing, or curation. Without it, listing pages can't pass.
4. **Shrink the synthetic surface + raise the editorial floor** (Findings 3, A) — fewer, better directory pages; more, better-distributed editorial.
5. **Convert thin pages to stubs or unpublish** (Finding B).

**Do NOT:**
- Add an FAQ/Q&A block to listing pages (the April audit correctly noted this was the *other* sites' mistake — don't import it).
- Expand the spintax phrase bank and call it "more unique."
- Re-open templated city intros.
- Resubmit on the strength of HTML/polish fixes alone.

---

## What to do about the pending review

You asked to avoid changes while the review is outstanding — that's reasonable, and **nothing in this report requires an urgent code change.** But set expectations honestly:

- Given the **active Search demotion** (Finding 1) and the **synthetic-content root cause** (Finding A) that already sank two structurally-identical sites, I think **rejection is the most likely outcome of the pending review.** The May 24 polish improved hygiene but did not change what the site fundamentally *is*.
- There's little downside to letting the review run — a rejection isn't a penalty, just a "not yet." So leaving the freeze in place to see the result is fine.
- The real work is **after** the result: this site needs a *content* answer (original value per page + a genuine editorial body), not another technical pass. Budget for that rather than for a fourth polish-and-resubmit cycle.

**Bottom line:** The build is clean; the *content model* is the problem, and your own traffic data shows Google has already reached that conclusion. The fix is strategic (what these pages are and what value they add), not cosmetic.

---

## Remediation implemented (2026-05-28)

The content-model fix was built and shipped (the decision was made not to wait for the likely rejection):

- **Replaced spun descriptions with fact-grounded ones** (`generate_fact_descriptions.py`). Each listing description is composed only from facts true for that business — Airtable fields joined to the Outscraper `about` attributes by name+city+state (97.1% match). Variation comes from real differing facts, removing the scaled-content-abuse signal (Finding A).
- **Tightened the index gate** — `MIN_DESCRIPTION_LENGTH` raised 250→300. The gate now indexes ~2,272 of 5,316 listings (~43%) and noindexes the rest, shrinking the synthetic surface (Findings 3, B).
- **Added per-listing internal links to editorial content** (breed guide + relevant blog how-tos, varied by listing type) so indexed pages are part of a content ecosystem (Finding 2).
- **Cleaned LocalBusiness JSON-LD** — dropped the invalid freeform `openingHours`, made `priceRange` conditional. Did **not** add `aggregateRating` from scraped Google ratings (structured-data-spam risk).

Prior descriptions backed up to `data/decription_backup_20260528.json`.

**Honest framing:** this removes the spun-content signal and halves the thin-page footprint, but it does not add original value beyond the Google Business Profile data. Better odds than the two failed sites — not likely approval.

## Ongoing maintenance — whenever you refresh data

Two steps keep this remediation intact (also documented in `CLAUDE.md`):

1. **Re-run `scripts/extract_gsc_protected.py` against a fresh GSC Performance export** so newly-ranking pages are added to `data/gsc_protected_urls.txt` and stay grandfathered past the quality gate.
2. **Re-run `generate_fact_descriptions.py` (dry run, then `--apply`)** so new listings get the same fact-grounded treatment. The calibration helpers (`analyze_fact_coverage.py`, `calibrate_gate.py`) are committed for re-checking join coverage and the gate threshold after a data change.
