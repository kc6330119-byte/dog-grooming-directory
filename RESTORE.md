# Restoring Dog Groomer Locator after the Airtable downgrade

**Status as of 2026-08-19:** the Airtable Groomers table was emptied to move the base to the
Free plan. The deployed site at https://doggroomerlocator.com is unchanged and still serves the
full 3,794-page directory from the last successful Netlify build. **Nothing is lost** — but the
site can no longer be rebuilt from Airtable until the data is restored.

## Do not do this

**Do not trigger a Netlify deploy** (push to `main`, "Retry deploy", or "Clear cache and deploy")
while Airtable is empty. The build reads listings from Airtable at build time.

A guard now makes this safe: `get_groomers()` aborts the build if Airtable returns fewer than
`MIN_EXPECTED_LISTINGS` (500). A deploy attempted with an empty table **fails** rather than
publishing an empty directory over the live site. Before that guard existed, such a build would
have succeeded and silently replaced every page.

## What is preserved, and where

| Asset | Location | Notes |
|---|---|---|
| All 5,316 listings incl. Phase 2 descriptions | `data/Groomers-Grid view - 20260819.csv` | 23 columns; `Decription` 100% filled, median 430 chars |
| Pre-Phase-2 descriptions | `data/decription_backup_20260701.json` | keyed by Airtable record id |
| Pre-Phase-1 descriptions | `data/decription_backup_20260528.json` | keyed by Airtable record id |
| 36 blog posts (61,510 words) | `blog_posts/*.json` | committed to git |
| 5,303 listing photos | `static/images/` | committed to git — not dependent on Airtable |
| GSC traffic-protected slugs | `data/gsc_protected_urls.txt` | 396 click-earning pages |
| Sitemap lastmod datestore | `sitemap_lastmod.json` | content hashes; prevents false "updated" signals |
| Breed guide data | `data/dog_grooming_master.xlsx` | + JSON fallback |
| Full policy audit | `audits/` | CONTEXT, 3 iterations, FINAL-REPORT |

## To restore

1. Move the Airtable base back to a paid plan (5,316 records exceeds the Free tier's 1,000/base).
2. Re-import the CSV into the **Groomers** table. Keep the exact column names — note the field
   is misspelled **`Decription`**, and `build.py` reads both spellings.
   `upload_to_airtable.py` upserts by Google Maps URL (100% populated in the backup), so it is
   safe to run repeatedly.
3. Confirm `.env` has `AIRTABLE_API_KEY`, `AIRTABLE_BASE_ID`, `AIRTABLE_TABLE_NAME`,
   `AIRTABLE_BLOG_TABLE_NAME`.
4. Blog posts, if that table was also emptied: `python3 upload_blog_posts.py` (upserts by slug).
5. Build locally first — `python3 build.py` — and confirm it reports ~3,794 groomer pages and
   exits 0 **before** pushing. If it aborts, the restore is incomplete.
6. Only then push to deploy.

## Where the project stood when paused

Rejected by AdSense for "Low value content" three times (May, June, and August 2026). The
remediation history is in `audits/FINAL-REPORT.md`. The unresolved issue is Finding #1: the
per-listing added value is machine-composed, and no code change settles whether that satisfies
the "additional commentary, curation, or otherwise adding value" test. The recommended next step
was never automation — it was human-written depth on 50–150 listings (call or visit the
businesses), plus state licensing research, which is the one thing a reviewer does not argue
with. Search traffic was also suppressed by a site-level quality demotion dating to 2026-05-13.
