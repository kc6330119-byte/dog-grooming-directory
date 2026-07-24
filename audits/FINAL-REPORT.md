# FINAL REPORT — AdSense "Low value content" remediation audit

Three iterations, each audited against the **rendered build** and verified with a passing build
(`python3 build.py`, exit 0). Commits: `014f8a2`, `82b3445`, `2e140e4`.

## Metric trajectory

| Metric | Baseline | Iter 1 | Iter 2 | Iter 3 |
|---|---|---|---|---|
| Rendered groomer pages | 5,316 | 3,794 | 3,794 | 3,794 |
| Pages claiming a review process that doesn't exist (P4) | **1,522** | **0** | 0 | 0 |
| Under-construction screens (P1) | **1,522** | **0** | 0 | 0 |
| Pages claiming "prices, and reviews" (P4) | **4,449 (100%)** | 4,449 | **0** | 0 |
| False data-field claims on About (P4) | 2 | 2 | **0** | 0 |
| Dead price-badge templates | 2 | 2 | **0** | 0 |
| Priced listings without provenance (P2) | 571 | 571 | **0** | 0 |
| Curation figures published (P1 evidence) | 0 | 0 | 0 | **3** |
| Listing-description method disclosed | No | No | No | **Yes** |
| Median body words / listing page | 341 | 356 | 359 | 359 |
| p10 body words / listing page | **30** | **321** | 321 | 321 |
| Indexable listings >90% duplicate | 0.0% | 0.0% | 0.0% | 0.0% |
| Max hub pairwise similarity (city/state/category) | .093/.084/.091 | — | — | unchanged |
| Editorial words / bidirectional linking | 61,510 / 100% | — | — | measured, **Pass** |
| Sitemap URLs | 3,963 | 3,963 | 3,963 | 3,963 |
| GSC click-earning pages preserved | 396/396 | **396/396** | 396/396 | **396/396** |
| Broken internal links | 0 | 0 | 0 | 0 |
| Pages with ad units | 0 | 0 | 0 | 0 |

## Open findings

| # | Sev | Policy | Finding | Why still open |
|---|---|---|---|---|
| 1 | **Major** | P1, P2 | Per-listing added value is machine-composed (2,695 website-sourced, remainder template-composed) | Hard Constraint 1 bars generating replacement prose. Needs human editorial work. |
| 9 | Minor | P2 | No state licensing/regulation content — the highest-value first-party topic not covered | Requires verified legal research across 50 states; fabrication barred by Hard Constraint 2. |
| 4 | Minor | P2 | 481 thin (83-word) city hubs, noindexed | Correctly noindexed, non-duplicative (0.093 max similarity), genuinely useful. Consolidating would remove working pages to chase a metric. |
| 8 | Minor | P2 | Submit form collects a `Price Range` nothing consumes | Cosmetic; a real input, not a false claim. |

**Closed:** Findings 2, 3 (Blockers), 5, 6, 10 (Major), 7 (Minor).
**B2 (doorways): closed on measurement.** **B1 (replicated content): partially closed** — the
duplication half is refuted by measurement; the provenance half is Finding 1.

---

## For an AdSense reconsideration note

### What we removed
- **1,522 listing pages** that displayed roughly thirty words and told the visitor *"This dog
  groomer listing is being reviewed for accuracy before it appears in the public directory."*
  No such review existed — the listings had failed an automated content check. Those URLs now
  return **410 Gone**. This was about 29% of the site's pages.
- **A site-wide claim, on 100% of pages, that we offer "prices, and reviews."** We have neither.
  Ratings shown on a listing are Google's and are labelled as Google's; the price field was
  empty on all 5,316 records. Both the page description and the About page checklist were
  corrected.
- **Two dead template blocks** that would have rendered a "Budget-Friendly / Mid-Range /
  Premium" price badge from a field no record has ever had.

### What we added
- **A published, enforced content standard.** Our Editorial Standards page now states the real
  figures, generated at build time so they cannot drift: we hold **5,316** grooming businesses
  and publish **3,794**. The other **1,522** do not meet the standard and are not published.
- **A plain description of how listing text is written** — for businesses with their own
  website we summarise the concrete details that business publishes about itself (services,
  hours, ownership, stated pricing, booking and deposit policies), drafted with AI assistance
  from those extracted facts, in our own words, copying nothing and inventing nothing. Where
  there is no usable website, the description uses only the structured facts we hold.
- **Source and date on every published price** — 571 listing pages now carry: *"Pricing shown is
  as published by the business on its own website (checked July 2026) and is subject to change."*
- **61,510 words of grooming editorial** (36 articles, median 1,896 words) covering costs,
  choosing a groomer, grooming frequency by breed, mobile vs salon, and anxious/senior dogs —
  linked from every listing page, and linking back into the directory.

### What we can show holds up
Zero indexable listing pages are more than 90% similar to another (max measured similarity
0.59). Location hubs share less than 10% of their text with each other, so they are not
templated doorways. Every internal link resolves. No page carries an ad unit.

---

## Requires a human — cannot be done in code

1. **First-party editorial on listings (closes Finding 1).** The credible fix is depth on a
   subset, not prose everywhere: pick 50–150 groomers, call or visit, and write genuinely
   first-hand notes — what the shop is like, how they handle an anxious dog, what a groom
   actually costs there. A hundred pages a human can vouch for beats 3,794 a model wrote.
2. **State licensing and regulation content (closes Finding 9).** Genuinely useful, genuinely
   absent from Google Maps, and legally consequential enough that it must be researched and
   sourced by a person.
3. **Real photography.** Listing images are Google Places photos. Original photos of businesses
   you have actually visited are strong, checkable evidence of first-hand experience.
4. **Airtable data entry.** `Services` is filled on 17.2% of records and `Specialties` on 11.4%.
   These are the only structured fields that can differentiate listings; populating them raises
   the ceiling on what any description can say.
5. **Search Console after this deploy.** 1,522 URLs now return 410. Expect "Not found (404)"
   and related buckets to rise — that is the withdrawal registering, not a regression. The
   indexed count should fall from ~10.6K toward ~3.9K. Do not resubmit to AdSense until it does.
6. **Decide on the price disclosures.** 571 pages show prices captured in July 2026. Either
   re-crawl on a schedule or remove them; a stale price is worse than no price.

---

## Honest verdict

**Not yet approvable — but the reason is now a single, well-defined judgement call rather than a
list of violations.**

Everything mechanically checkable passes. Listing pages are not duplicates; hubs are not
doorways; navigation is intact; the publisher is a real named person; the policy pages are
complete and the methodology page is candid to the point of publishing how many listings it
refuses to publish. Three iterations removed two blockers and three major findings, and the
worst of them — 1,522 pages asserting a human review that never happened — was the kind of
plainly false statement that justifies rejection on its own.

What remains is P1's actual test, and I do not think code can settle it. The value a listing
page adds over the Google Maps result is a description a language model wrote by summarising
the business's own website. That is meaningfully better than the spun text that caused the
original rejection — the facts are real, they come from a source Google Maps does not show, and
the site now discloses the method. But P1 asks for *the publisher's* commentary or curation,
and a machine summary of a third party's marketing copy is at the boundary of that phrase.
A reviewer could reasonably read 3,794 model-written descriptions as scaled content regardless
of how good the sourcing is.

The strongest remaining move is not more automation — it is depth on a subset that a human can
personally vouch for, plus the licensing research. That converts "we summarised their website"
into "we went and found out," which is the only version of this that no reviewer argues with.

One caveat on my own role: I audited a content layer I generated earlier the same day. I have
tried to grade it as an adversary would, and I have kept it listed as an open Major finding
rather than talking myself into closing it — but a genuinely independent reviewer would be
better placed to make that call than I am.
