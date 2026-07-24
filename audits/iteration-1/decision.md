# Iteration 1 — Decision

**Closed this iteration:** Findings 2 and 3 (both Blockers). The site no longer claims an
editorial review process it does not perform, and no longer serves 1,522 thirty-word
under-construction screens. B2 (doorways) is closed on measurement, not assertion.

**Still open:** Finding 1 (Major, P1/P2) — the added-value layer on listing pages is
machine-composed. Finding 4 (Minor) — 481 thin noindexed city hubs, deliberately deferred.

**Canonical / robots / sitemap rationale (Constraint 5):** canonical logic and robots.txt
were **not modified**. The sitemap's URL set is **unchanged** (3,963 before and after) because
withdrawn listings were never in it. The only additions are 3,044 `410!` rules in `_redirects`.
410 was chosen over 404 (unambiguous permanent withdrawal, faster de-indexing, which also
serves the live objective of shrinking a 10.6K indexed surface toward ~3.9K), over 301-to-hub
(the hub does not contain that business — "irrelevant or misleading destination" under P2),
and over the status quo (a false claim under P4).

**Why not DONE:** the protocol requires zero open Major findings *and* an APPROVE verdict at
Step 1. This iteration's verdict was REJECT and Finding 1 remains Major and open.

DECISION: CONTINUE
