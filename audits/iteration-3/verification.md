# Iteration 3 — Verification

Re-measured against the new build (`python3 build.py`, **exit 0**).

| Metric | Before | After | Δ |
|---|---|---|---|
| Curation figures on methodology page | 0 | **3** (5,316 held / 3,794 published / 1,522 withheld) | ✅ |
| Figures hard-coded (can go stale) | — | **No** — computed per build | ✅ |
| Listing-description method disclosed | **No** | **Yes** | ✅ |
| "excluded from search indexing" (inaccurate) | 1 | **0** | ✅ |
| editorial-standards word count | 767 | **970** | +203 |
| Editorial layer grade | Minor | **Pass** | measured, not changed |
| Groomer pages | 3,794 | 3,794 | unchanged |
| Sitemap URLs | 3,963 | 3,963 | unchanged |
| Pages claiming "prices, and reviews" | 0 | 0 | still closed |
| Pages claiming a review process | 0 | 0 | still closed |
| GSC-protected pages rendered | 396/396 | **396/396** | ✅ |
| Broken internal links | 0 | 0 | unchanged |

## Regressions
**None.** One implementation defect was caught and fixed before verification: the counts
initially rendered blank because `build_static_pages` receives the *published* pool, making
`withheld_count` zero. The function now takes `all_groomers` separately.

## Blockers
- **B1: OPEN as Major.** Mitigated by disclosure this iteration, not closed. Requires human editorial input.
- **B2: CLOSED.**
