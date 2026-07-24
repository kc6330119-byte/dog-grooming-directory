# Iteration 2 — Audit

Re-audited the **post-iteration-1 build** (3,794 groomer pages, 0 stubs). Because 1,522 pages
were withdrawn, every composition metric was re-measured rather than carried forward.

## Rubric

| Dim | Grade | Policy | Change from iter 1 |
|---|---|---|---|
| A. Added value over source data | **Major** | P1, P2, P3 | unchanged — Finding 1 still open |
| B. Doorway detection | **Pass** | P3, P4 | unchanged (closed) |
| C. Original editorial layer | **Minor** | P2 | unchanged |
| D. Misleading functionality | **Major** | P4 | **new findings 5, 6** |
| E. Navigation quality | **Pass** | P2 | 0 broken links |
| F. Trust & required pages | **Pass** | — | About names a real, identifiable publisher (Kevin Collins) with a verifiable background; Editorial Standards discloses AI-assisted drafting and automated gating honestly |
| G. Ad-to-content ratio | **Pass (vacuous)** | P1 | 0 ad units |
| H. Under construction | **Pass** | P1 | **closed in iter 1** |
| I. Technical | **Pass** | — | unchanged |

## Findings

### Finding 5 — Every page claims the site offers "prices, and reviews" [Major, P4]
**Evidence:** `config.py:20`
```
SITE_DESCRIPTION = "Find trusted dog groomers near you. Browse ratings, services, prices,
and reviews for professional pet grooming across America."
```
Rendered into the meta description and `og:description` of **4,449 of 4,449 pages** — 100%.

**Why a reviewer flags it:** P4 forbids *"claiming content or services the site does not
actually provide."*
- **"reviews"** — the site has no reviews. It displays a Google star rating with attribution
  (*"Google rating (N reviews)"*). There is no first-party review, no review submission, no
  review text anywhere (verified: 0 pages match `write a review|leave a review|rate this`).
- **"prices"** — the `Price Range` field is populated on **0 of 5,316 records**; the template
  branch that renders a `$`/`$$`/`$$$` badge (`_groomer_card_compact.html:11-18`) is therefore
  dead code that never fires. Only 127 of 3,794 listing pages (3.3%) mention any price at all,
  incidentally, inside description prose.

This is the claim Google itself sees in the SERP snippet for every URL on the site. It is the
same *category* of violation as the stub sentence closed in iteration 1: a plainly checkable
false statement, deployed site-wide.

**Fix:** rewrite `SITE_DESCRIPTION` to describe what the site actually has.

---

### Finding 6 — About page advertises data fields that are empty [Major, P4]
**Evidence:** `templates/about.html:115,117` — a checklist of what each listing provides:
> ✓ Price range   ✓ Breed specialties

Actual fill rates: **Price Range 0%** (field absent from every record), **Specialties 11.4%**.

**Why a reviewer flags it:** same clause as Finding 5. A user reading About is told each
listing carries a price range; no listing does.

**Fix:** remove `Price range`; qualify `Breed specialties` as "where available", matching how
the other sparse fields are honestly framed.

---

### Finding 7 — 127 pages publish prices with no date or provenance [Minor, P2]
**Evidence:** e.g. `dist/groomer/fur-the-love-of-pets-oradell.html` — *"pricing starting at $75
for small dogs, $85 for medium/large dogs."* Extracted from the business's own site on
2026-07-01; no capture date or "subject to change" note is shown.

**Why:** not a policy violation — the figure is real and attributed to the business — but
prices go stale, and an out-of-date price on a directory page misleads a user and irritates the
business. P2's navigation clause is about accuracy generally.

**Fix:** a dated provenance line on listings whose description contains a price.

---

## Verdict — reviewer's voice

**REJECT.**

Iteration 1 removed the worst of it — the site no longer tells visitors that a human is
checking listings that no human will ever check. But I ran the same test against the rest of
the site's own claims and it fails again, in the same way and more broadly. Every page I load,
all 4,449 of them, carries a description promising me "prices, and reviews." There are no
reviews on this site — there is a Google star rating with a Google attribution, which is a
different thing and which the site is otherwise scrupulous about labelling. There are no
prices — the price field is empty on all 5,316 records, and the badge that would display it is
code that cannot execute. The About page repeats the promise as a checklist with ticks
next to it.

I want to be fair about what is working: the listing pages are not duplicates, the location
hubs are not doorways, the publisher is a real named person, and the editorial standards page
is unusually candid about AI-assisted drafting. That is a better foundation than most sites I
reject. But a site cannot advertise content it does not have on 100% of its pages.

**Single most damaging reason:** the site-wide description claims "prices, and reviews" —
neither exists (P4).
