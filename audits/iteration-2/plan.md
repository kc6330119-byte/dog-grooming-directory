# Iteration 2 — Plan

## Major: Finding 5 — site-wide false claim in SITE_DESCRIPTION (P4)
**File:** `config.py:20`. Replace the "prices, and reviews" claim with an accurate description
of what the site actually provides: curated listings, Google ratings shown with attribution,
hours, services, and grooming guides.
**Expected delta:** pages claiming prices/reviews 4,449 → 0.

## Major: Finding 6 — About advertises empty fields (P4)
**File:** `templates/about.html:115,117`. Remove the `Price range` tick (0% populated); qualify
`Breed specialties` as "where available" (11.4% populated).
**Expected delta:** false field claims 2 → 0.

## Minor: Finding 7 — undated prices on 127 pages (P2)
**Files:** `templates/groomer.html` + `build.py`. When a listing's description contains a
currency figure, render a dated provenance line beneath it. Uses real data only (the crawl
date), fabricates nothing.
**Expected delta:** priced pages with provenance 0 → 127.

## Also: remove dead price-range code
`_groomer_card_compact.html:11-18` renders a price badge from a field that is empty on every
record. Dead code that encodes a claim; remove it so the promise cannot silently reappear.

## Explicitly not doing
- **Finding 1 (machine-composed value)** — Hard Constraint 1 bars generating replacement prose;
  the real fix needs a human. Carried to FINAL-REPORT.
- **Finding 4 (481 thin noindexed city hubs)** — still correctly noindexed and non-duplicative;
  consolidating them would remove genuinely useful pages to chase a metric.
- **No canonical / robots.txt / sitemap-generation changes** (Constraint 5).
- **No new ad units** (Constraint 6).
