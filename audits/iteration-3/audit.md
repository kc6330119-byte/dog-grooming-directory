# Iteration 3 — Audit

Focus: rubric C (original editorial layer) and the P1 curation evidence, the two areas not yet
examined in depth.

## Rubric

| Dim | Grade | Change |
|---|---|---|
| A. Added value over source data | **Major** | Finding 1 still open |
| B. Doorway detection | **Pass** | closed |
| C. Original editorial layer | **Pass** (was Minor) | upgraded on measurement — see below |
| D. Misleading functionality | **Pass** (was Major) | Findings 5–7 closed in iter 2 |
| E. Navigation quality | **Pass** | 0 broken links |
| F. Trust & required pages | **Pass** | strengthened this iteration |
| G. Ad-to-content ratio | **Pass (vacuous)** | 0 ad units |
| H. Under construction | **Pass** | closed iter 1 |
| I. Technical | **Pass** | unchanged |

## C — measured, not asserted

| Measure | Value |
|---|---|
| Blog posts | 36 |
| Total editorial words | **61,510** |
| Median post length | **1,896 words** |
| Breed guide | 1,614 words |
| Listing pages linking to editorial | **300/300 sampled (100%)** |
| Blog posts linking into the directory | **36/36 (100%)** |

Coverage against the topics the protocol names: costs ✅ (1), how to choose ✅ (5),
breed-specific ✅ (6), grooming frequency ✅ (1), mobile vs salon ✅ (2), anxious/senior dogs ✅ (2),
**state licensing rules ❌ (0)**.

This is not a disconnected blog — the linking is bidirectional and complete. C upgrades to Pass.

### Finding 9 — no state licensing/regulation content [Minor, P2]
The one topic from the protocol's list with zero coverage, and the one with the most genuine
first-party research value (grooming licensure varies by state and is not on any Google Maps
result). **Not fixed in code:** licensing facts are legally consequential and I cannot verify
50 states' statutes to publishable accuracy. Fabricating them would violate Hard Constraint 2.
Routed to the human checklist.

### Finding 10 — the methodology page understated the site's own curation [Major, P1] — FIXED
**Evidence (before):** `editorial-standards.html` said listings failing the content standard are
*"excluded from search indexing."* After iteration 1 that was **false in the site's favour** —
they are not published at all. The page also disclosed AI-assisted drafting for *articles* while
saying nothing about how *listing descriptions* are written, which is the site's largest content
surface and the subject of Finding 1.

**Why it matters:** the protocol is right that under P1 this page is the primary evidence of
curation. A reviewer who reads "we exclude some listings from indexing" sees an SEO tactic. A
reviewer who reads "we hold 5,316 businesses and publish 3,794; the other 1,522 don't meet the
standard and are withdrawn" sees an editorial policy being enforced at cost.

**Fix applied:** rewrote the sourcing section to state the real standard and the real numbers
(computed from the build, so they cannot go stale), and added a "How Listing Descriptions Are
Written" section that discloses the method honestly — website-sourced facts, AI-assisted
drafting, no copying, no invention, Google's ratings labelled as Google's, prices dated.

## Verdict — reviewer's voice

**REJECT** — but this is now a close call, and the reason has narrowed to one thing.

Everything I can check mechanically, this site now passes. The listing pages are not
duplicates. The hubs are not doorways. The editorial layer is 61,510 words, is genuinely about
dog grooming, and is wired into the directory in both directions. Nothing claims a service that
does not exist. The publisher is a named, identifiable person, and the methodology page now
tells me plainly that 1,522 businesses are held back from publication for failing a content
standard — that is curation, and disclosing the number is more than most directories do.

What I am left with is Finding 1, and it is the whole question: the added value on a listing
page is a description that a language model wrote. The site now tells me so, which I credit.
The facts inside it come from the business's own website rather than from the scraped record,
which I also credit — that is genuinely additional information, not a paraphrase of the map
result. But P1 asks for the publisher's commentary or curation, and a machine summary of a
third party's marketing copy sits at the edge of that. I cannot resolve it from the page alone.

**Single most damaging reason:** the per-listing added value is machine-composed (P1/P2);
whether that satisfies "additional commentary, curation, or otherwise adding value" is a
judgement call that no further code change will settle.
