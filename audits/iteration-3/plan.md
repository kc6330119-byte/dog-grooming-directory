# Iteration 3 — Plan

## Major: Finding 10 — methodology page understates real curation (P1)
**Files:** `templates/editorial-standards.html`, `build.py::build_static_pages`.
Rewrite the sourcing section to state the real publishing standard and real figures, computed
from the build (`held_count` / `published_count` / `withheld_count`) so they cannot go stale.
Add a "How Listing Descriptions Are Written" section disclosing the actual method.
**Expected delta:** curation figures on the methodology page 0 → 3; description-method
disclosure absent → present.

## Minor: Finding 9 — no state licensing content
**Not doing.** Requires verified legal research across 50 states. Fabrication is barred by
Hard Constraint 2. Routed to the human checklist.

## Explicitly not doing
- **Finding 1** — barred by Hard Constraint 1; needs human editorial input.
- **Finding 4** (481 thin noindexed city hubs) — correctly noindexed, non-duplicative, useful.
- **Finding 8** (orphaned submit-form price field) — cosmetic, no policy urgency.
- **No canonical / robots.txt / sitemap-generation changes** (Constraint 5).
- **No new ad units** (Constraint 6).
