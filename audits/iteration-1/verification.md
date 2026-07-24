# Iteration 1 — Verification

Re-measured against the new build (`python3 build.py`, **exit 0**).

## Before / after

| Metric | Before | After | Δ |
|---|---|---|---|
| Rendered groomer HTML files | 5,316 | **3,794** | −1,522 |
| Pages claiming a review process (P4) | 1,522 | **0** | ✅ closed |
| Under-construction screens (P1) | 1,522 | **0** | ✅ closed |
| Noindexed groomer pages | 1,522 | **0** | all rendered pages are now indexable |
| Median body words (all groomer pages) | 341 | **356** | +15 |
| p10 body words | 30 | **321** | +291 (thin tail eliminated) |
| Indexable listings >90% duplicate | 0.0% | **0.0%** | unchanged |
| 410 rules emitted | 0 | **3,044** (1,522 × 2 forms) | as planned |
| Sitemap URLs | 3,963 | **3,963** | unchanged |
| Withdrawn slugs appearing in sitemap | — | **0** | ✅ |
| GSC-protected pages withdrawn | — | **0** | ✅ |
| GSC-protected pages still rendered | 396 | **396/396** | ✅ no traffic loss |
| Broken internal links | 0 | **0** | unchanged |
| Pages containing `adsbygoogle` | 0 | 0 | unchanged |
| Editorial word count (state hubs, median) | 1,324 | 1,324 | untouched |

*Correction to CONTEXT.md:* the "2,873 sitemap URLs" recorded during discovery came from a
**stale `dist/`** left by a previous session (the first build attempt silently no-opped —
`python` does not exist locally, only `python3`). The true pre-change figure is 3,963, matching
the live sitemap. No sitemap regression occurred; the number was never 2,873 for this commit.

## Regressions

**None.** Every metric held or improved. Specifically checked for the three ways this change
could have gone wrong:
1. *Withdrawing a page that earns traffic* — 0 overlap with the 396 GSC-protected slugs; all 396 still render.
2. *Sitemap referencing withdrawn URLs* — 0.
3. *Orphaning the site's own internal links* — stubs were never linked from hubs (verified pre-change: 0 of 400 sampled), and post-change link check is still 0 broken.

## New findings this iteration

**None.** The Jinja `NameError` introduced mid-implementation (`thin` referenced after its
assignment was removed) was caught by the build failing loudly and fixed before verification;
it never reached a passing build.

## Status of the two assumed blockers

- **B1 (replicated content): OPEN as Major.** Measurements refute the *duplication* half of the
  charge (0% >90% duplicates, median 356 unique words, max pairwise similarity 0.59). The
  unresolved half is provenance: the added layer is machine-composed. Not closable in code —
  see FINAL-REPORT human checklist.
- **B2 (doorways): CLOSED.** Max pairwise similarity — city 0.093, state 0.084, category 0.091.
  Only 68 of 549 city pages are indexable; state hubs carry a median 1,324 words of
  hand-written editorial. This is not a doorway pattern by any measure applied.
