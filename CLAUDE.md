# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Python static-site generator for **Dog Groomer Locator** (https://doggroomerlocator.com), a national dog grooming directory. The build pulls listing and blog data from Airtable, runs it through a content-quality gate, and emits a fully static HTML site into `dist/`. Netlify builds and deploys it. There is no runtime server or framework — everything is generated at build time.

## Commands

```bash
# Build the site (reads Airtable if .env is configured, else uses sample data)
python build.py

# Preview locally after building
cd dist && python3 -m http.server 8000   # http://localhost:8000

# Install deps
pip install -r requirements.txt
```

Netlify runs `pip install -r requirements.txt && python build.py` and publishes `dist/` (see `netlify.toml`). Python 3.9.

There is **no test suite, linter, or build framework**. `build.py` runs `validate_build()` at build time, which prints warnings (duplicate meta descriptions, thin descriptions, duplicate slugs) but never fails the build.

## Data pipeline (run manually, in order)

Source data flows: Outscraper export → cleaned CSV → Airtable → `build.py`. These scripts are run by hand when refreshing data, not during the Netlify build. Most support `--apply` (default is a dry run).

- `outscraper_to_airtable.py` — ETL: reads Outscraper XLSX, dedupes, maps columns, derives services/type, outputs clean CSV.
- `validate_listings.py` — flags/removes non-groomer records (vets, pet stores, sitters). `--remove` to delete.
- `backfill_services.py` — derives Services/Specialties/Type from text fields where empty.
- `generate_fact_descriptions.py` — **current description generator.** Composes each listing description from facts that are true for that specific business: Airtable structured fields (Type/Rating/Review Count/Hours/Services/Specialties) joined to the Outscraper `about` attribute JSON (ownership identity, service options, planning, accessibility, parking, payments, crowd) by normalized name+city+state. Variation comes from real differing facts — no synonym shuffling — so it avoids the "scaled content abuse" signal. Only updates existing records (never inserts); no length padding, so descriptions below the gate stay short and get noindexed. Dry run by default; `--apply` writes the `Decription` field. Replaces the two generators below.
- `auto_descriptions.py` — *(superseded by `generate_fact_descriptions.py`)* cleans junk descriptions; `--ai` regenerates via Claude Haiku (needs `ANTHROPIC_API_KEY`).
- `enrich_descriptions.py` — *(superseded; do not use)* hash-seeded (MD5) spintax generation. This is the synthetic/spun-content approach that AdSense flags as "scaled content abuse" — the documented root cause of the sister-site failures. Kept only for reference.
- `upload_to_airtable.py` — upserts `Groomers_VALIDATED.csv` to Airtable, matching on Google Maps URL. Preserves editorial fields, updates operational fields.
- `upload_blog_posts.py` — upserts JSON files from `blog_posts/` to the Airtable Blog Posts table, matching on Slug.
- `refresh_photos.py` — fetches fresh Google Places photos for groomers with empty Photo URL (needs `GOOGLE_PLACES_API_KEY`).
- `scripts/extract_gsc_protected.py` — regenerates `data/gsc_protected_urls.txt` from a GSC Performance export (see quality gate below).

## Architecture

**`config.py`** is the single source of truth for site constants: Airtable/AdSense/GA settings (all via env vars with defaults), SEO thresholds, the `CATEGORIES` list, the `US_STATES` list (each with a long editorial `description`), the `AUTHORS` map (E-E-A-T author bios for blog posts), and the quality-gate vocabularies (`JUNK_DESCRIPTION_TERMS`, `GROOMING_VOCAB`).

**`build.py`** is the whole generator. `main()` fetches groomers + blog posts from Airtable (falling back to `get_sample_data()` when unconfigured), annotates each listing with a quality decision, then renders every page type with Jinja2 templates from `templates/`. Output goes to `dist/`.

Page types and their URLs:
- Homepage `/`, static pages (`/about`, `/contact`, etc.)
- State pages `/state/<slug>` (one per US state)
- City pages `/state/<state>/<city>` (only emitted when ≥2 listings)
- Groomer detail pages `/groomer/<slug>` — these get LocalBusiness JSON-LD
- Category pages `/category/<slug>` (filtered by `CATEGORY_FILTERS`)
- Blog `/blog`, blog posts `/blog/<slug>` (BlogPosting JSON-LD + author bios)
- Breed guide `/dog-grooming-guide` (data from `data/dog_grooming_master.xlsx`, JSON fallback for CI)

### The content-quality gate (the most important concept)

This is an AdSense/SEO-driven site, and the central design constraint is **not indexing thin or duplicate content**. Understand this before changing build logic:

- `description_quality_check()` / `annotate_listing_quality()` decide whether each listing is "public". A listing must have a description ≥ `MIN_DESCRIPTION_LENGTH` (300 chars), contain grooming vocabulary, avoid junk patterns, and have at least one contact/service signal. Repetitive description openings are also rejected (this catches chain locations like Petco/PetSmart whose fact descriptions share an identical opening). With the fact-grounded descriptions, this gate currently indexes ~2,270 of 5,316 listings (~43%) and noindexes the rest, deliberately shrinking the synthetic indexed surface.
- `public_groomers()` filters to passing listings. **Browse/search surfaces (homepage, state, city, category, sitemap, search index) are built from this filtered pool**, while `build_groomer_pages()` still emits a page for *every* groomer — failing ones get `noindex` + ads suppressed rather than being deleted, so existing URLs don't 404.
- **GSC protection**: slugs listed in `data/gsc_protected_urls.txt` are grandfathered past the gate so pages already earning Google traffic can't regress. Refresh this list from a fresh GSC export via `scripts/extract_gsc_protected.py`.
- State pages noindex below `MIN_STATE_LISTINGS_FOR_INDEX` (3); city pages noindex below `MIN_CITY_LISTINGS_FOR_INDEX` (10). City pages deliberately carry **no templated intro** — a prior templated intro created ~749 doorway-page near-duplicates that AdSense flagged.

### SEO/template conventions

Every `template.render()` passes `request_path` (drives the canonical + og:url in `base.html`), and pages that should not be indexed pass `noindex=True`. Ad rendering is gated by `show_ads = adsense_enabled and not noindex and not suppress_ads`. Meta descriptions are generated per-page by `generate_dynamic_meta_description()` from real content (never formulaic) to keep them unique. Page titles use `seo_title()` / `groomer_page_title()` for keyword-first, length-capped titles.

**URLs are extensionless.** `build_netlify_redirects()` generates `dist/_redirects` with one explicit `/x.html → /x 301!` rule per page (placeholder interpolation in Netlify redirects was unreliable, so rules are emitted literally). `netlify.toml` adds extensionless→`.html` 200 rewrites for static pages plus legacy 301s. If you add a new page type, add its redirect rules in both `build_netlify_redirects()` and (if it's a top-level static page) `netlify.toml`.

## Important notes

- The Airtable field for description is misspelled `Decription` in the base; `fetch_from_airtable()` reads both spellings.
- Groomer slugs must be stable and unique — `dedupe_slugs()` handles collisions by appending zip, then a record-id fragment, then a counter. Don't change slug generation casually; it affects existing indexed URLs.
- Google Places photo URLs expire, so `download_groomer_images()` downloads them locally to `static/images/<slug>.jpg` at build time and clears dead URLs back in Airtable.
- `.env` holds `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME`, `AIRTABLE_BLOG_TABLE_NAME`, `ANTHROPIC_API_KEY`, `GOOGLE_PLACES_API_KEY`. It is gitignored.
- The newsletter feature was removed (Mailchimp cancelled); `/newsletter/*` 301s to home in `netlify.toml`. Don't reintroduce it.
- The dated `*_AUDIT_*.md` files at the repo root are point-in-time AdSense/SEO audit reports — useful context for *why* the quality gate exists, but not active documentation.
