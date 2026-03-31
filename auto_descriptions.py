#!/usr/bin/env python3
"""
auto_descriptions.py — Two-pass description cleanup for Airtable Groomers.

Pass 1 (all records):
  Strips JSON blobs, booking-software feature lists, embedded 'nan' values,
  and normalizes whitespace. Safe and free.

Pass 2 (records still lacking a useful description after Pass 1):
  Generates clean descriptions using Claude Haiku AI.

Usage:
    python3 auto_descriptions.py                 # Dry run — shows what would change
    python3 auto_descriptions.py --apply         # Apply Pass 1 cleanup only (free)
    python3 auto_descriptions.py --apply --ai    # Apply Pass 1 + AI generation

Requirements:
    - For --ai: add ANTHROPIC_API_KEY to your .env file
"""

import sys
import os
import re
import time
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

DRY_RUN = "--apply" not in sys.argv
USE_AI  = "--ai" in sys.argv

MIN_DESC_LENGTH = 60   # Descriptions shorter than this (after cleaning) need replacement
CHUNK_SIZE      = 10   # Airtable batch size

# Patterns that indicate booking-software feature lists
BOOKING_SOFTWARE_PATTERNS = [
    r"Auto Message reminder",
    r"Smart Scheduling",
    r"Employee Management",
    r"Online Booking",
    r"Payment Processing",
    r"Appointment Reminders",
    r"Client Management",
    r"POS System",
]

BOOKING_RE = re.compile("|".join(BOOKING_SOFTWARE_PATTERNS), re.IGNORECASE)


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_description_field_name(fields):
    """Return the actual field name used in this record ('Decription' or 'Description').
    Default to 'Decription' (the actual Airtable column name with the typo)."""
    if "Description" in fields:
        return "Description"
    return "Decription"


def get_description(fields):
    """Get the description value, handling the Airtable typo."""
    return fields.get("Decription", fields.get("Description", ""))


def is_json_blob(text):
    """Detect JSON-like content (service options, accessibility attributes)."""
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return True
    # Partial JSON blobs with nested braces
    if stripped.count("{") >= 2 and stripped.count("}") >= 2:
        return True
    # JSON-like key-value patterns: {"Key": value, ...}
    if re.search(r'\{["\'][\w\s]+["\']:\s*\{', stripped):
        return True
    return False


def is_feature_list(text):
    """Detect booking-software feature lists."""
    if BOOKING_RE.search(text):
        return True
    # Bullet-separated feature names (3+ segments with · or • separators)
    if len(re.split(r'\s*[·•]\s*', text)) >= 3:
        # Check if segments look like feature names (short, capitalized phrases)
        segments = re.split(r'\s*[·•]\s*', text)
        short_segments = sum(1 for s in segments if len(s.strip()) < 40)
        if short_segments >= 3:
            return True
    return False


def clean_description(raw):
    """Strip garbage and normalize. Returns cleaned string."""
    if not raw:
        return ""
    text = str(raw).strip()

    # Remove if entire value is a JSON blob
    if is_json_blob(text):
        return ""

    # Remove if entire value is a feature list
    if is_feature_list(text):
        return ""

    # Line-level cleanup
    lines = text.splitlines()
    kept = []
    for ln in lines:
        ln_stripped = ln.strip()
        if not ln_stripped:
            continue
        if ln_stripped.lower() == "nan":
            continue
        if is_json_blob(ln_stripped):
            continue
        if is_feature_list(ln_stripped):
            continue
        kept.append(ln_stripped)

    return " ".join(kept).strip()


def is_useful(desc):
    """True if description is long enough to display on the site."""
    return len(clean_description(desc)) >= MIN_DESC_LENGTH


# ── AI generation ─────────────────────────────────────────────────────────────

def generate_ai_description(groomer):
    """Call Claude Haiku to write a 2-3 sentence description for a groomer."""
    import anthropic

    client = anthropic.Anthropic(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        timeout=30.0,
    )

    services    = ", ".join(groomer.get("services", [])) or "not specified"
    specialties = ", ".join(groomer.get("specialties", [])) or "not specified"
    price_range = groomer.get("price_range", "") or "not specified"
    rating      = groomer.get("rating", "")
    review_count = groomer.get("review_count", "")
    groomer_type = groomer.get("type", "") or "not specified"

    rating_line = ""
    if rating and str(rating) not in ("0", ""):
        rating_line = f"Rating: {rating}"
        if review_count and str(review_count) not in ("0", ""):
            rating_line += f" ({review_count} reviews)"
        rating_line += "\n"

    prompt = (
        f"Write a 2-3 sentence description for a dog grooming business listing. "
        f"Be professional, warm, and factual. Do not invent details not provided. "
        f"Focus on the services they offer and what makes them a good choice. "
        f"Do not use filler phrases like 'nestled' or 'boasting' or 'dedicated team'.\n\n"
        f"Business Name: {groomer['name']}\n"
        f"Location: {groomer['city']}, {groomer['state']}\n"
        f"Type: {groomer_type}\n"
        f"Services: {services}\n"
        f"Specialties: {specialties}\n"
        f"Price Range: {price_range}\n"
        f"{rating_line}"
        f"\nWrite only the description text, no quotes or labels."
    )

    msg = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=180,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text.strip()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    api   = Api(os.getenv("AIRTABLE_API_KEY"))
    table = api.table(
        os.getenv("AIRTABLE_BASE_ID"),
        os.getenv("AIRTABLE_TABLE_NAME", "Groomers"),
    )

    mode_label = "DRY RUN" if DRY_RUN else ("APPLY + AI" if USE_AI else "APPLY — Pass 1 only")
    print(f"\n{'='*62}")
    print(f"  Auto-Descriptions for Dog Groomers  [{mode_label}]")
    print(f"{'='*62}\n")

    print("Fetching records from Airtable...")
    records = table.all()
    print(f"Fetched {len(records)} records.\n")

    # ── Categorise every record ───────────────────────────────────────────────
    pass1_changes  = []   # cleaning changes the value (garbage stripped / whitespace)
    still_needs    = []   # even after cleaning, description is too short

    for rec in records:
        fields  = rec["fields"]
        name    = fields.get("Name", "").strip()
        if not name:
            continue

        desc_field = get_description_field_name(fields)
        original   = get_description(fields)
        cleaned    = clean_description(original)

        if cleaned != str(original).strip():
            pass1_changes.append({
                "id":         rec["id"],
                "name":       name,
                "original":   original,
                "cleaned":    cleaned,
                "desc_field": desc_field,
            })

        if not is_useful(cleaned):
            still_needs.append({
                "id":         rec["id"],
                "name":       name,
                "fields":     fields,
                "cleaned":    cleaned,
                "desc_field": desc_field,
            })

    print(f"── Pass 1: garbage/whitespace cleanup ─────────────────────")
    print(f"  Records to clean:                    {len(pass1_changes)}")
    print(f"  Still need a description after clean: {len(still_needs)}\n")

    # ── Pass 2 summary ───────────────────────────────────────────────────────
    est_cost = len(still_needs) * 0.004
    print(f"── Pass 2: AI generation ──────────────────────────────────")
    print(f"  Require AI generation:               {len(still_needs)}")
    print(f"  Estimated AI cost:                   ~${est_cost:.2f}\n")

    # ── Dry run output ────────────────────────────────────────────────────────
    if DRY_RUN:
        print("─" * 62)
        print("PASS 1 SAMPLES (before → after):\n")
        for c in pass1_changes[:5]:
            print(f"  {c['name']}")
            print(f"    Before: {repr(str(c['original']).strip()[:90])}")
            print(f"    After:  {repr(c['cleaned'][:90])}")
            print()

        if still_needs:
            print("─" * 62)
            print(f"PASS 2 AI: {len(still_needs)} records would be sent to Claude Haiku\n")
            print("  Sample records:")
            for r in still_needs[:8]:
                city  = r["fields"].get("City", "")
                state = r["fields"].get("State", "")
                print(f"    - {r['name']} ({city}, {state})")

        print("\n" + "─" * 62)
        print("DRY RUN complete — nothing written to Airtable.")
        print("  --apply         Apply Pass 1 cleanup (free, safe)")
        print("  --apply --ai    Apply Pass 1 + AI generation")
        print("─" * 62)
        return

    # ── Build update map (Pass 1) ────────────────────────────────────────────
    # IDs that will get AI descriptions — don't pre-write a short cleaned value
    ai_ids = {r["id"] for r in still_needs}

    updates = {}
    for c in pass1_changes:
        if c["id"] not in ai_ids:
            updates[c["id"]] = (c["cleaned"], c["desc_field"])

    print(f"Applying {len(updates)} Pass 1 updates...")
    batch = [{"id": rid, "fields": {field: desc}} for rid, (desc, field) in updates.items()]
    for i in range(0, len(batch), CHUNK_SIZE):
        table.batch_update(batch[i:i + CHUNK_SIZE])
        print(f"  Updated {min(i + CHUNK_SIZE, len(batch))}/{len(batch)}...")

    # ── AI generation ─────────────────────────────────────────────────────────
    if not USE_AI:
        if still_needs:
            print(f"\nSkipped AI generation for {len(still_needs)} records.")
            print("Re-run with --apply --ai to generate those descriptions.")
        total = len(updates)
        print(f"\nDone! Updated {total} records.")
        return

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\nError: ANTHROPIC_API_KEY not found in .env — skipping AI generation.")
        print("Add it and re-run with --apply --ai.")
        return

    try:
        import anthropic  # noqa: F401
    except ImportError:
        print("\nError: anthropic package not installed.")
        print("Run: pip install anthropic")
        return

    FLUSH_EVERY = 100   # write to Airtable incrementally to preserve progress on failure

    print(f"\nGenerating AI descriptions for {len(still_needs)} records...")
    ai_batch      = []
    total_written = 0
    errors        = 0

    for i, rec in enumerate(still_needs):
        try:
            groomer_data = {
                "name":         rec["name"],
                "city":         rec["fields"].get("City", ""),
                "state":        rec["fields"].get("State", ""),
                "type":         rec["fields"].get("Type", ""),
                "services":     rec["fields"].get("Services", []),
                "specialties":  rec["fields"].get("Specialties", []),
                "price_range":  rec["fields"].get("Price Range", ""),
                "rating":       rec["fields"].get("Rating", ""),
                "review_count": rec["fields"].get("Review Count", ""),
            }
            new_desc = generate_ai_description(groomer_data)
            ai_batch.append({"id": rec["id"], "fields": {rec["desc_field"]: new_desc}})
            print(f"  [{i+1}/{len(still_needs)}] {rec['name'][:50]}: {new_desc[:70]}...")
            time.sleep(0.25)   # gentle rate limiting
        except Exception as e:
            print(f"  [{i+1}/{len(still_needs)}] Error — {rec['name']}: {e}")
            errors += 1

        # Flush incrementally so progress is preserved if the process is interrupted
        if len(ai_batch) >= FLUSH_EVERY:
            for j in range(0, len(ai_batch), CHUNK_SIZE):
                table.batch_update(ai_batch[j:j + CHUNK_SIZE])
            total_written += len(ai_batch)
            print(f"  ↳ Flushed {total_written}/{len(still_needs)} to Airtable")
            ai_batch = []

    # Final flush for remaining records
    if ai_batch:
        print(f"\nWriting final {len(ai_batch)} AI descriptions to Airtable...")
        for i in range(0, len(ai_batch), CHUNK_SIZE):
            table.batch_update(ai_batch[i:i + CHUNK_SIZE])
            print(f"  Updated {min(i + CHUNK_SIZE, len(ai_batch))}/{len(ai_batch)}...")
        total_written += len(ai_batch)

    total = len(updates) + total_written
    print(f"\nDone! Total records updated: {total}")
    if errors:
        print(f"  ({errors} records skipped due to errors — re-run to retry)")
    print("Run python3 build.py to rebuild the site with updated descriptions.")


if __name__ == "__main__":
    main()
