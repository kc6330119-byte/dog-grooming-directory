# Iteration 2 — Verification

Re-measured against the new build (`python3 build.py`, **exit 0**).

## Before / after

| Metric | Before | After | Δ |
|---|---|---|---|
| Pages claiming "prices, and reviews" (P4) | **4,449 (100%)** | **0** | ✅ closed |
| Sources of that claim | 2 (`SITE_DESCRIPTION`, `DEFAULT_META_DESCRIPTION`) | 0 | ✅ |
| About page claiming an empty `Price range` field | 1 | **0** | ✅ closed |
| About page qualifying sparse fields ("where available") | 0 | **1** | ✅ |
| Dead price-range badge templates | 2 | **0** | ✅ removed |
| Listing pages publishing a price *without* provenance | 571 | **0** | ✅ |
| Listing pages with dated price provenance | 0 | **571** | new |
| Groomer pages | 3,794 | 3,794 | unchanged |
| Median body words | 356 | **359** | +3 |
| Sitemap URLs | 3,963 | 3,963 | unchanged |
| 410 rules | 3,044 | 3,044 | unchanged |
| GSC-protected pages rendered | 396/396 | **396/396** | ✅ no traffic loss |
| Pages claiming a review process | 0 | 0 | still closed |
| Broken internal links | 0 | 0 | unchanged |
| Pages with `adsbygoogle` | 0 | 0 | unchanged |

*Note:* the price-provenance count is 571, not the 127 estimated in the audit. The audit
sampled 600 listing pages; the build applies `PRICE_RE` to all 3,794. 571/3,794 = 15% of
listing pages contain a currency figure. Higher than estimated, which makes the disclosure
more valuable, not less.

## Regressions

**None.** Page count, sitemap, redirect rules, protected-page coverage and link integrity all
held; median body words rose slightly (the provenance line adds words to 571 pages).

## New findings this iteration

**Finding 8 [Minor, P2] — orphaned "Price Range" field in the submission form.**
`templates/submit.html:90-96` still asks a submitting business for a price range. The field is
real (it is an input, not a claim), but nothing consumes it — the Airtable `Price Range` field
is empty on all 5,316 records and no template renders it now. Collecting data the site never
uses is untidy rather than a violation. Deferred, not fixed: removing a form field is a
user-facing change with no policy urgency.

## Status of the two assumed blockers

- **B1: OPEN as Major** — unchanged. Machine-composed added value; not closable in code.
- **B2: CLOSED** — unchanged.
