# Dog Groomer Locator AdSense and SEO Audit - 2026-05-24

## Executive Summary

Dog Groomer Locator is materially better than the April 29 pre-submission audit, but I would not resubmit it to AdSense yet.

The good news: the most obvious city-doorway implementation has been reduced. The live sitemap now has 4,778 URLs instead of the earlier 6,150, city pages in the sitemap are down to 98, old `.html` URLs correctly 301 to extensionless URLs, and the corrupt "Under One Ruff" example is now `noindex, follow`.

The hard news: the site still looks like a very large directory with a small editorial layer. Of the 4,778 live sitemap URLs, about 4,734 are directory pages, leaving roughly 44 editorial/static pages. That is still about 99.1% directory and 0.9% publisher/editorial content. Google Publisher Policies specifically call out screens with low-value publisher content and replicated content without added value as inventory-value risks.

For SEO, there is a sharper issue: the Search Console export shows a visibility collapse beginning around May 13, 2026. From April 25 through May 12 the site averaged thousands of impressions on normal weekdays. From May 13 through May 22 it produced only 1 click and 1,040 impressions total. This should be treated as an urgent SEO triage item before changing the indexation rules again.

Bottom line: DGL is closer to AdSense-ready than the earlier Splash Pad / HVD-style failure mode, but it still needs quality gating at the user-facing level, not just `noindex`, plus an SEO recovery pass focused on the post-May-13 drop.

## Remediation Implemented - 2026-05-24

The following fixes were implemented after this audit:

- Added an AdSense feature flag. `ADSENSE_ENABLED` now defaults to off, the AdSense script only renders when explicitly enabled, and the visible placeholder ad boxes were removed entirely.
- Suppressed ads on noindexed/under-review pages and static utility pages.
- Added `ads.txt` using the publisher ID already present in the template.
- Added a real `/static/images/og-image.png` and routed OG/Twitter image tags through `config.DEFAULT_OG_IMAGE`.
- Removed the misleading `WebSite` `SearchAction` schema until the site has a real query URL endpoint.
- Added a final slug de-dupe pass. The regenerated sitemap has 0 duplicate URLs and 0 `.html` URLs.
- Changed public browse/search/sitemap flows to include only quality-passing listings.
- Changed failing groomer listings into noindex "Listing under review" pages with sanitized metadata, no LocalBusiness schema, and no ads.
- Fixed the broken homepage FAQ link from `/category/mobile` to `/category/mobile-grooming`.
- Added a 301 redirect from `/category/mobile` to `/category/mobile-grooming`.
- Limited category pages to a curated preview of quality-passing listings plus state browse links, reducing `/category/full-service` from about 8.85 MB live HTML to about 356 KB in the regenerated build.
- Updated generated SEO titles and meta descriptions for homepage, state, city, category, and groomer pages so the page hierarchy is more clearly aligned to "dog groomers near me", state/local groomer, and individual business searches without keyword stuffing.
- Empty category pages are now `noindex, follow` and excluded from the sitemap.
- Google-derived ratings/review counts are now labeled as Google ratings in the UI, link to Google Maps on detail pages, and are no longer emitted as `aggregateRating` structured data.
- Regenerated the site with Airtable data: 5,316 total listings, 4,483 public quality-passing listings, 833 under-review listings, 4,668 sitemap URLs, 85 indexed city URLs, 4,483 groomer URLs in the sitemap, and 35 blog posts.

Remaining non-code item: the May 13 Search Console cliff still needs to be reviewed in the GSC UI because the export shows the drop but not the indexing/crawl diagnostics behind it.

## Sources Reviewed

- Live site: https://doggroomerlocator.com/
- Live robots: https://doggroomerlocator.com/robots.txt
- Live sitemap: https://doggroomerlocator.com/sitemap.xml
- Live examples: `/state/california`, `/state/california/anaheim`, `/category/full-service`, `/groomer/under-one-ruff-cleburne`
- Search Console export: `/Users/kevincollins/Downloads/https___doggroomerlocator.com_-Performance-on-Search-2026-05-24.xlsx`
- AdSense rejection screenshot: `/Users/kevincollins/Desktop/Screenshot 2026-05-19 at 5.49.06 PM.png`
- Local project files: `build.py`, `config.py`, `templates/base.html`, `templates/index.html`, `templates/category.html`, `templates/groomer.html`, `data/gsc_protected_urls.txt`, `dist/sitemap.xml`
- Google Publisher Policies: https://support.google.com/adsense/answer/10502938
- Google SEO Starter Guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Google doorway-page guidance: https://developers.google.com/search/blog/2015/03/an-update-on-doorway-pages
- Google Search technical requirements: https://developers.google.com/search/docs/essentials/technical

## What Improved Since The April 29 Audit

### 1. City doorway pages were reduced

Current code sets `MIN_CITY_LISTINGS_FOR_INDEX = 10` in `config.py` and removes the templated city intro in `build.py`.

Current live/local sitemap:

| URL type | Count |
|---|---:|
| Groomer detail | 4,578 |
| City | 98 |
| State | 50 |
| Category | 8 |
| Blog posts | 35 |
| Breed guide | 1 |
| Blog index/static/home | 8 |
| Total | 4,778 |

This is a real improvement from 749 indexed city pages. The live Anaheim city page, for example, is `noindex, follow` because it is below the 10-listing threshold.

### 2. Listing quality gate is no longer only data completeness

`description_quality_check()` now requires:

- non-empty description
- at least 250 characters unless protected
- no configured junk terms such as tattoo/piercing scrape markers
- grooming vocabulary
- at least one contact/service signal

This directly addresses the old "phone + hours + junk description still passes" problem.

### 3. State pages are stronger

The April 29 audit found state descriptions around 40-60 words. The current `config.py` has expanded state copy, and live `/state/california` shows substantive state-specific content.

### 4. Canonical and `.html` migration are mostly healthy

Live checks:

- `https://doggroomerlocator.com/groomer/all-4-paws-exeter.html` returns 301 to `/groomer/all-4-paws-exeter`.
- Extensionless URL returns 200.
- Live sitemap contains 0 `.html` URLs.
- Live robots.txt allows crawling and points at the sitemap.

## AdSense Findings

### Finding A: Noindex does not fully solve low-value content

Impact: High

Evidence:

- Local build has 738 noindexed groomer pages and 651 noindexed city pages.
- Those pages are still generated, user-accessible, and internally linked from state/category directory views.
- The corrupt `/groomer/under-one-ruff-cleburne` page is now `noindex, follow`, but the page still renders the junk description to users and in its meta/OG fields.

Why this matters:

AdSense review is about monetizable user-facing inventory, not just the Google Search index. If reviewers or crawlers can navigate to junk/thin pages from normal directory pages, the site can still look like low-value content.

Recommended fix:

- For listings that fail `description_quality_check()`, do one of these:
  - remove them from public state/category/home grids until fixed, or
  - render a limited "unverified listing" page without ads, without LocalBusiness schema, and without a full detail page experience, or
  - fix the description and data before publishing.
- Do not rely on `noindex` alone as the AdSense cleanup layer.

### Finding B: Directory/editorial ratio is still extremely lopsided

Impact: High

Evidence:

- Live sitemap has 4,778 URLs.
- Directory-like pages are about 4,734 URLs: groomer, city, state, and category pages.
- Editorial/static layer is about 44 URLs: 35 blog posts, 1 breed guide, homepage, blog index, and static policy/about pages.
- Directory/editorial ratio is still roughly 99.1% / 0.9%.

Recommended fix:

- Do not simply publish filler articles to chase a ratio.
- Build a real editorial layer around high-intent pet-owner tasks:
  - dog grooming prices by dog size and coat condition
  - mobile grooming by metro area
  - breed-specific grooming costs and cadence
  - anxious/senior/special-needs dog grooming
  - state and climate-specific coat care
- Tie these pages to the directory with useful calls to action and contextual internal links.
- Target a first pass of 25-40 high-quality pages, then reassess AdSense.

### Finding C: Repetitive listing descriptions remain widespread

Impact: High

Evidence from local rendered `dist/groomer` pages:

- 4,575 groomer detail pages are currently indexable in local output.
- Indexed groomer description median is about 350 characters / 54 words.
- 1,016 indexable pages contain "comprehensive grooming services."
- 925 indexable pages contain "professional grooming services."
- 3,079 indexable pages contain "grooming services."
- Chain/location duplicates remain visible. Example repeated starts include "Woof Gang Bakery & Grooming" across 61 indexable pages.

Recommended fix:

- Add duplicate-pattern detection, not only length detection.
- Flag descriptions whose first 8-12 words repeat across more than 3 locations.
- For chains, create a reusable chain profile plus location-specific deltas, rather than repeating the same body copy.
- Prefer locally specific facts: neighborhood served, service model, review count, known specialties, mobile/salon distinction, coat types handled, and whether the listing data was verified.

### Finding D: Empty ad placeholders hurt the review experience

Impact: Medium-High

Evidence:

- `templates/base.html` includes AdSense script on every page.
- It also renders visible "Advertisement" placeholder blocks above and below content.
- `ads.txt` is missing locally and live `/ads.txt` returns 404.

Recommended fix:

- Remove visible ad placeholder blocks until approval.
- Consider removing the AdSense script until resubmission, or gate it by environment/approval status.
- Add `ads.txt` once AdSense provides the exact authorized seller line.
- Keep monetization out of noindexed, unverified, and thin pages even after approval.

### Finding E: Full-service category page is too large and too list-like

Impact: Medium-High

Evidence:

- Live `/category/full-service` is about 8.85 MB HTML.
- Local `dist/category/full-service.html` is about 8.4 MB and 210,262 lines.
- GSC export shows `/category/full-service` with 703 impressions, 0 clicks, and average position 19.01.

Recommended fix:

- Paginate or segment category pages by state/region.
- Add 400-800 words of unique category guidance above the listings.
- Consider noindexing huge all-site category dumps until they are turned into useful hub pages.
- Keep category pages in the sitemap only when they are real editorial/category landing pages, not just massive listing dumps.

## SEO Findings

### Finding 1: Search visibility collapsed after May 13, 2026

Impact: Critical

Evidence from the GSC export:

| Period | Clicks | Impressions | CTR | Weighted avg position |
|---|---:|---:|---:|---:|
| Apr 25-May 22 total | 239 | 89,086 | 0.27% | 16.10 |
| First 7 days, Apr 25-May 1 | 140 | 43,890 | 0.32% | 15.53 |
| Last 7 days, May 16-May 22 | 1 | 763 | 0.13% | 53.14 |
| May 13-May 22 | 1 | 1,040 | 0.10% | mostly 23-64 daily |

Likely contributors:

- Google processed the April 29 quality-gate and sitemap reduction.
- Many low-content pages were noindexed or removed from the sitemap.
- The GSC protected list is stale: `data/gsc_protected_urls.txt` is sourced from April 29 and contains 350 protected slugs. Applying the same clicked-or-impressions threshold to the May 24 export finds 886 unique groomer slugs.
- 697 groomer slugs from the May 24 export are not in the current protected list, while 161 old protected slugs no longer appear in the May 24 protected candidate set.
- 75 groomer rows with Search Console impressions/clicks are currently `noindex` in local output.

Recommended triage:

1. In Search Console, check Page Indexing and Crawl Stats for May 10-May 24.
2. Inspect representative dropped URLs with URL Inspection:
   - one state page
   - one category page
   - one noindexed groomer that had impressions
   - one extensionless groomer URL that still has `.html` history
3. Refresh `data/gsc_protected_urls.txt` from the May 24 export, but do not simply protect every URL with impressions. Segment them:
   - protect clicked URLs temporarily
   - improve descriptions for high-impression/no-click URLs before reindexing
   - keep junk/thin pages noindexed or unpublished
4. Submit the current sitemap again after the cleanup.

### Finding 2: The current traffic is mostly listing/brand intent, not generic discovery

Impact: High

Evidence from the top 1,000 exported page rows:

| Page type | Rows | Clicks | Impressions | CTR | Avg position |
|---|---:|---:|---:|---:|---:|
| Groomer | 923 | 226 | 39,092 | 0.58% | 12.88 |
| State | 43 | 9 | 7,564 | 0.12% | 44.73 |
| Category | 4 | 0 | 1,111 | 0.00% | 27.18 |
| City | 26 | 5 | 1,064 | 0.47% | 31.88 |
| Blog post | 3 | 1 | 65 | 1.54% | 9.29 |

Interpretation:

- Groomer detail pages are doing most of the real work.
- State pages are getting impressions but are not ranking competitively.
- Category pages have search exposure but are not earning clicks.
- Blog posts are barely present in the top 1,000 page rows.

Recommended fix:

- Treat listing pages as the SEO beachhead, but improve only the ones with real demand.
- Build a focused "money pages" list from GSC:
  - top clicked groomer pages
  - high-impression groomer pages ranking 4-20
  - state pages with impressions and average position under 30
  - category pages with impressions
- Improve those pages first instead of making broad sitewide content changes.

### Finding 3: Generic "near me" intent is not being captured well

Impact: High

Evidence from the top 1,000 exported query rows:

- `dog grooming near me`: 417 impressions, 0 clicks, average position 27.64
- `best dog groomers near me`: 321 impressions, 0 clicks, average position 62.70
- `dog groomers near me`: 312 impressions, 3 clicks, average position 21.34
- `groomers near me`: 229 impressions, 1 click, average position 30.26
- `dog groomer near me`: 218 impressions, 1 click, average position 33.86

Interpretation:

DGL is not competitive for broad local discovery yet. That is expected for a young directory, but it means the SEO win will come from long-tail/local/brand queries first, not from broad "near me" terms.

Recommended fix:

- Create high-quality city pages only for cities with enough listings and search demand.
- Do not re-open the old templated city doorway pattern.
- Build 25-50 manually enhanced city landing pages for top markets first, each with:
  - 250-500 words of real local context
  - neighborhood/service notes
  - top service filters
  - a compact map/listing experience
  - clear "last reviewed" and verification language

### Finding 4: Stale `lastmod` weakens recrawl signals

Impact: Medium

Evidence:

- Live/current sitemap has only 24 unique `lastmod` dates across 4,778 URLs.
- 4,319 URLs have `lastmod` of `2026-03-31`.
- 408 URLs have `lastmod` of `2026-04-01`.

Recommended fix:

- Derive `lastmod` from actual content changes, not bulk import dates.
- When a page moves from noindex to index after a quality fix, update that page's `lastmod`.
- Do not bump every page every build. Bump only pages with meaningful content/data changes.

### Finding 5: Internal broken link in homepage FAQ

Impact: Low-Medium

Evidence:

- `templates/index.html` links "Mobile Groomers" to `/category/mobile`.
- Live `/category/mobile` returns 404.
- Correct URL is `/category/mobile-grooming`.

Recommended fix:

- Change `/category/mobile` to `/category/mobile-grooming`.
- Add a 301 from `/category/mobile` to `/category/mobile-grooming` because the broken URL is live.

### Finding 6: Missing Open Graph image

Impact: Low

Evidence:

- `templates/base.html` references `/static/images/og-image.png`.
- Live `/static/images/og-image.png` returns 404.

Recommended fix:

- Add a real OG image, or remove the tag until it exists.
- This is not the cause of the organic search collapse, but it is a quality polish issue.

### Finding 7: Structured data is valid JSON, but WebSite SearchAction is misleading

Impact: Low-Medium

Evidence:

- Home, groomer, city, and post JSON-LD parse as valid JSON.
- Base template emits a `WebSite` `SearchAction` pointing to `/state/{slug}`.
- The site does not have a normal query search endpoint that matches the schema pattern.

Recommended fix:

- Remove `SearchAction`, or replace it with a real search URL if a server-rendered search results page is added.
- Keep BreadcrumbList and LocalBusiness schema, but normalize `openingHours` later if you want cleaner rich-results validation.

### Finding 8: Duplicate sitemap URLs exist

Impact: Low

Evidence:

Current local/live sitemap has 3 duplicate groomer URLs:

- `/groomer/groomingdales-new-york-10028`
- `/groomer/doggy-stylez-grooming-new-york-10128`
- `/groomer/the-bark-factory-albuquerque-87122`

Recommended fix:

- Add a final slug de-dupe pass after zip-code disambiguation.
- Fail the build if duplicate sitemap locations remain.

## Prioritized Action Plan

### Phase 1: Do before AdSense resubmission

1. Remove visible ad placeholders and gate AdSense script until approval.
2. Remove, suppress, or repair noindexed thin listing pages from user-facing grids.
3. Fix the worst 100-200 listing descriptions by GSC priority:
   - clicked pages first
   - pages ranking 4-20
   - high-impression pages with no clicks
4. Add a duplicate/repetitive-description detector to the build.
5. Fix `/category/mobile` broken link and add a redirect.
6. Add `ads.txt` when the authorized seller line is available.

### Phase 2: SEO recovery triage

1. Investigate the May 13 visibility cliff in Search Console.
2. Refresh GSC protected data from the May 24 export, but split "protect" from "needs rewrite."
3. Re-submit sitemap after cleanup.
4. Track impressions daily for 10-14 days before making another broad indexation change.

### Phase 3: Build durable organic growth

1. Turn 25-50 top city pages into real local landing pages.
2. Convert giant category pages into useful hubs with pagination or state segmentation.
3. Build editorial clusters around prices, coat types, mobile grooming, anxious dogs, seniors, puppies, and breed-specific grooming.
4. Add "last reviewed" and verification signals to listings and editorial pages.
5. Continue expanding editorial content, but only where it answers a real dog-owner task.

## Resubmission Recommendation

Do not resubmit to AdSense yet.

Resubmit after:

- noindexed/junk listings are no longer exposed as normal detail pages,
- ad placeholders are removed,
- the broken internal link and missing OG asset are fixed,
- at least the highest-risk repetitive descriptions are rewritten,
- the May 13 Search Console cliff is understood,
- and the sitemap reflects the cleaned page set.

With those fixed, DGL has a plausible path to approval. Without those fixes, the most likely rejection reason remains "low value content," especially because the site is still mostly programmatic directory pages with only a small editorial layer.
