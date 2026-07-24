# Iteration 1 — Plan

Ordered Blocker → Major → Minor.

## Blocker: Findings 2 + 3 — the 1,522 stub pages (P4 false claim, P1 under construction)

Both findings share one root cause and one fix: the build emits a placeholder page for every
listing that fails the quality gate.

**Change:** `build.py::build_groomer_pages` stops writing HTML for gate-failing listings.
Those URLs get an explicit **HTTP 410 Gone** rule in `dist/_redirects`.
`templates/groomer.html` loses the `thin_listing` stub block; `build.py` loses the
"being reviewed for accuracy" meta description branch.

**Why 410 and not 404, 301, or noindex-as-is:**
- *Not status quo* — the claim is false (P4) and the screen is under-construction (P1).
- *Not 301 to the state hub* — that hub does not contain the business, so it is an
  "irrelevant or misleading" destination under P2's navigation clause.
- *Not padding the page* — Services is 17.2% filled and Specialties 11.4%; there is no data
  to expand these from, and padding with generated prose is barred by Hard Constraint 1.
- *410 over 404* — 410 is the unambiguous "permanently gone" signal; Google drops 410s from
  the index faster, which is also the site's live SEO objective (10.6K indexed → ~3.9K).
- *Reversible* — the rule set is regenerated every build. If a listing's data later passes
  the gate, the page returns and its 410 rule disappears automatically.

**Safety verified before implementing:** stubs ∩ GSC-protected click-earners = **0**.

**Files:** `build.py` (`build_groomer_pages`, `build_netlify_redirects`), `templates/groomer.html`.

**Expected measurable delta:**
| Metric | Before | Expected after |
|---|---|---|
| Rendered groomer HTML files | 5,316 | 3,794 |
| Pages claiming a review process | 1,522 | 0 |
| Under-construction screens | 1,522 | 0 |
| Median body words, all groomer pages | 341 | ~355 |
| Sitemap URLs | 2,873 | unchanged (stubs were never in it) |
| GSC-protected pages affected | — | 0 |

## Major: Finding 1 — machine-composed added value

**Deliberately NOT changing this iteration.** Operator decision is to keep Phase 2 live and
grade it. Hard Constraint 1 bars generating replacement prose. The genuine remedy is
first-party curation, which requires a human — it is carried to FINAL-REPORT's human checklist,
not faked in code.

## Minor: Finding 4 — 481 thin noindexed city hubs

**NOT changing this iteration.** They are correctly noindexed, non-duplicative (0.093 max
similarity), and genuinely useful to a visitor. Removing them would be consolidation for its
own sake. Re-evaluate in iteration 2 once the blocker's effect is measured.

## Explicitly not doing

- **No canonical, robots.txt, or sitemap-generation changes** (Constraint 5). The 410 rules
  are additive redirect entries; canonical logic and the sitemap's URL set are untouched —
  the stubs were never in the sitemap (verified: 1 incidental substring match, not a real entry).
- **No new ad units** (Constraint 6) — and none exist to add to.
- **No structured-data or CWV work** while a blocker is open (protocol instruction).
