#!/usr/bin/env python3
"""
Deterministic description enrichment for dog groomers.

Uses MD5 hash of the groomer slug with bit-shifting to select from varied
sentence pools, producing natural-sounding, diverse descriptions that
rebuild identically every time. No AI API calls — $0 cost.

Adapted from senior-home-care-directory/enrich_descriptions.py pattern.

Usage:
    python3 enrich_descriptions.py              # Dry run — preview changes
    python3 enrich_descriptions.py --apply      # Replace thin/irrelevant descriptions in Airtable
"""
import hashlib
import os
import sys

from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Groomers")

# Airtable has a typo: "Decription" (missing 's'). Write to both fields.
DESC_FIELD = "Decription"

MIN_DESC_LENGTH = 100  # Descriptions under this are "thin"
CHUNK_SIZE = 10


# ==============================
# IRRELEVANT DESCRIPTION DETECTION
# ==============================

IRRELEVANT_INDICATORS = [
    '"Service options"',
    '"Accessibility"',
    '"Payments"',
    '"Wheelchair accessible',
    '"Credit cards"',
    '"Debit cards"',
    '"NFC mobile payments"',
    '"Parking"',
    '"From the business"',
    '"Identifies as',
    "official website",
    "sign up for programs",
    "contact information for",
    "demographics, history",
    "visit our website",
    "click here for more",
]


def is_irrelevant(desc):
    """Check if a description is raw Google Maps JSON or generic boilerplate."""
    stripped = desc.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return True
    lower = stripped.lower()
    return any(phrase.lower() in lower for phrase in IRRELEVANT_INDICATORS)


# ==============================
# SENTENCE POOLS
# ==============================

OPENINGS = [
    "{name} is a professional dog grooming business serving pet owners in {city}, {state}.",
    "Located in {city}, {state}, {name} provides expert grooming services for dogs of all breeds and sizes.",
    "{name} offers trusted dog grooming in {city}, {state}, keeping pets clean, comfortable, and looking their best.",
    "Pet owners in {city}, {state} rely on {name} for professional grooming that keeps their dogs healthy and happy.",
    "Serving the {city} area, {name} delivers quality dog grooming with attention to each pet's individual needs.",
    "{name} is a go-to destination for dog grooming in {city}, {state}, known for skilled and caring service.",
]

OPENINGS_NO_LOCATION = [
    "{name} is a professional dog grooming business serving local pet owners.",
    "{name} provides expert grooming services for dogs of all breeds and sizes.",
    "{name} offers trusted dog grooming, keeping pets clean, comfortable, and looking their best.",
    "Pet owners rely on {name} for professional grooming that keeps their dogs healthy and happy.",
    "{name} delivers quality dog grooming with attention to each pet's individual needs.",
    "{name} is known for skilled and caring dog grooming service.",
]

TYPE_SENTENCES = {
    "Full-Service Salon": "As a full-service salon, they handle everything from baths and haircuts to nail trimming and ear cleaning in a single visit.",
    "Mobile Grooming": "Their mobile grooming service brings the salon directly to your door, offering convenience and a low-stress experience for your pet.",
    "Pet Spa": "Their spa-style approach goes beyond basic grooming, offering pampering treatments that leave dogs refreshed and rejuvenated.",
    "Self-Service Wash": "They offer self-service wash stations with professional equipment, letting owners bathe their dogs without the mess at home.",
    "Veterinary Grooming": "Located within a veterinary setting, they combine grooming expertise with medical awareness for dogs with health considerations.",
}
DEFAULT_TYPE_SENTENCE = "Their experienced team provides thorough grooming that keeps dogs looking and feeling great."

SERVICE_INTROS = [
    "Services offered include",
    "Their grooming menu features",
    "Dogs can enjoy",
    "Available services include",
]

SERVICE_DESCRIPTIONS = {
    "Full Grooming": "complete grooming sessions with bath, cut, and styling",
    "Bath & Brush": "bath and brush-out packages",
    "Bath Only": "bath-only options for quick clean-ups",
    "Nail Trimming": "nail trimming and grinding",
    "Teeth Brushing": "teeth brushing for dental hygiene",
    "Deshedding": "deshedding treatments for heavy shedders",
    "Ear Cleaning": "ear cleaning and care",
    "Flea & Tick Treatment": "flea and tick treatments",
    "Creative Grooming": "creative grooming and color styling",
    "Hand Stripping": "hand-stripping for wire-coated breeds",
    "Puppy First Groom": "gentle first-groom introductions for puppies",
    "Cat Grooming": "grooming services for cats",
    "Self-Service Wash": "self-service dog wash stations",
    "Anal Gland Expression": "anal gland expression",
    "De-matting": "de-matting for tangled coats",
    "Sanitary Trim": "sanitary trims",
    "Face Trim": "face and head trimming",
    "Paw Trim": "paw pad and foot trimming",
    "Medicated Bath": "medicated baths for skin conditions",
}

SPECIALTY_DESCRIPTIONS = {
    "Breed-Specific Styling": "breed-standard styling and show cuts",
    "Show Grooming": "show-ring grooming preparation",
    "Anxious Dogs": "gentle handling for anxious and nervous dogs",
    "Senior Dogs": "patient care for senior dogs with mobility needs",
    "Large Breeds": "experience with large and giant breed dogs",
    "Small Breeds": "specialized care for small and toy breeds",
    "Mobile Grooming": "convenient mobile grooming at your doorstep",
    "All Breeds": "expertise across all dog breeds",
    "Cat Grooming": "feline grooming services",
    "Doodle Grooming": "doodle and designer breed coat management",
    "Double Coat": "double-coat maintenance and seasonal blowouts",
}

PRICE_SENTENCES = {
    "$": [
        "They offer budget-friendly pricing, making professional grooming accessible for every pet owner.",
        "With affordable rates, {name} keeps quality grooming within reach for all budgets.",
        "Their competitive pricing makes regular professional grooming an easy choice for local dog owners.",
    ],
    "$$": [
        "Their pricing is moderate and reflects the quality of care each dog receives.",
        "{name} offers fair pricing that balances professional results with value.",
        "With mid-range pricing, they deliver professional-quality grooming at a reasonable cost.",
    ],
    "$$$": [
        "As a premium grooming destination, they deliver top-tier results with high-end products and techniques.",
        "{name} provides an elevated grooming experience with premium products and personalized attention.",
        "Their premium pricing reflects the exceptional quality and individualized care each dog receives.",
    ],
}

RATING_SENTENCES = [
    "{name} holds a {rating}-star rating based on {count} reviews from satisfied pet owners.",
    "With a {rating}-star Google rating from {count} reviews, {name} is a well-regarded choice in the area.",
    "Pet owners have given {name} a {rating}-star rating across {count} reviews.",
]

CLOSINGS = [
    "Contact {name} to schedule a grooming appointment for your dog.",
    "Reach out to {name} to book a grooming session and keep your pet looking their best.",
    "Call {name} today to learn more about their grooming services and availability.",
    "Get in touch with {name} to give your dog the professional grooming care they deserve.",
]

HOURS_SENTENCES = [
    "{name} is open {hours}.",
    "Hours of operation: {hours}.",
    "They welcome appointments {hours}.",
]


def format_list(items):
    """Format a list as 'a, b, and c'."""
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def to_list(val):
    """Convert Airtable field value to a list."""
    if isinstance(val, list):
        return val
    if isinstance(val, str) and val.strip():
        return [s.strip() for s in val.split(",") if s.strip()]
    return []


def extract_fields(record):
    """Extract and normalize fields from an Airtable record."""
    fields = record.get("fields", {})
    from slugify import slugify

    name = fields.get("Name", "Groomer")
    city = fields.get("City", "")
    return {
        "slug": fields.get("Slug", slugify(name + "-" + city) if city else slugify(name)),
        "name": name,
        "city": city,
        "state": fields.get("State", ""),
        "type": fields.get("Type", ""),
        "services": to_list(fields.get("Services", [])),
        "specialties": to_list(fields.get("Specialties", [])),
        "price_range": fields.get("Price Range", ""),
        "rating": fields.get("Rating"),
        "review_count": fields.get("Review Count"),
        "hours": fields.get("Hours", ""),
    }


def generate_description(record):
    """Generate a deterministic, varied description for a groomer."""
    f = extract_fields(record)
    slug = f["slug"]

    h = int(hashlib.md5(slug.encode()).hexdigest(), 16)

    parts = []

    # Opening (h % 6)
    if f["city"] and f["state"]:
        opening = OPENINGS[h % 6].format(name=f["name"], city=f["city"], state=f["state"])
    else:
        opening = OPENINGS_NO_LOCATION[h % 6].format(name=f["name"])
    parts.append(opening)

    # Type sentence
    type_sentence = TYPE_SENTENCES.get(f["type"], DEFAULT_TYPE_SENTENCE)
    parts.append(type_sentence)

    # Services + specialties ((h >> 4) % 4)
    service_items = []
    for svc in f["services"][:4]:
        desc = SERVICE_DESCRIPTIONS.get(svc)
        if desc:
            service_items.append(desc)
    for spec in f["specialties"][:3]:
        desc = SPECIALTY_DESCRIPTIONS.get(spec)
        if desc and desc not in service_items:
            service_items.append(desc)

    if service_items:
        intro = SERVICE_INTROS[(h >> 4) % len(SERVICE_INTROS)]
        parts.append(f"{intro} {format_list(service_items)}.")

    # Price range ((h >> 8) % 3)
    pr = f["price_range"]
    if pr and pr in PRICE_SENTENCES:
        pool = PRICE_SENTENCES[pr]
        price_sentence = pool[(h >> 8) % len(pool)]
        parts.append(price_sentence.format(name=f["name"]))

    # Rating ((h >> 12) % 3)
    if f["rating"] and f["review_count"]:
        try:
            r = float(f["rating"])
            c = int(float(f["review_count"]))
            if r >= 4.0 and c > 0:
                rating_sentence = RATING_SENTENCES[(h >> 12) % len(RATING_SENTENCES)].format(
                    rating=f["rating"], count=c, name=f["name"]
                )
                parts.append(rating_sentence)
        except (ValueError, TypeError):
            pass

    # Hours ((h >> 20) % 3)
    if f["hours"] and len(f["hours"]) < 80:
        hours_sentence = HOURS_SENTENCES[(h >> 20) % len(HOURS_SENTENCES)].format(
            name=f["name"], hours=f["hours"]
        )
        parts.append(hours_sentence)

    # Closing ((h >> 16) % 4)
    closing = CLOSINGS[(h >> 16) % len(CLOSINGS)].format(name=f["name"])
    parts.append(closing)

    return " ".join(parts)


def main():
    from pyairtable import Api

    apply_mode = "--apply" in sys.argv

    mode_label = "APPLY" if apply_mode else "DRY RUN"
    print(f"\n{'='*62}")
    print(f"  Description Enrichment for Dog Groomers  [{mode_label}]")
    print(f"{'='*62}\n")

    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, TABLE_NAME)

    print("Fetching records from Airtable...")
    records = table.all()
    print(f"Fetched {len(records)} records.\n")

    # Find records that need enrichment
    enriched_thin = 0
    replaced_irrelevant = 0
    updates = []

    for r in records:
        fields = r.get("fields", {})
        # Handle typo field name
        desc = (fields.get(DESC_FIELD) or fields.get("Description") or "").strip()
        desc_clean = desc.replace("nan", "").strip()

        label = None
        if len(desc_clean) < MIN_DESC_LENGTH:
            label = "ENRICH (thin)"
            enriched_thin += 1
        elif is_irrelevant(desc):
            label = "REPLACE (irrelevant)"
            replaced_irrelevant += 1

        if label:
            new_desc = generate_description(r)
            updates.append({
                "id": r["id"],
                "fields": {DESC_FIELD: new_desc},
                "_label": label,
                "_name": fields.get("Name", ""),
            })

    print(f"Thin descriptions (< {MIN_DESC_LENGTH} chars): {enriched_thin}")
    print(f"Irrelevant descriptions (JSON/boilerplate): {replaced_irrelevant}")

    if not updates:
        print("\nNothing to enrich.")
        return

    print(f"\nTotal updates: {len(updates)}")
    print(f"\n{'─'*60}")
    print("Preview (first 5):")
    print(f"{'─'*60}")
    for u in updates[:5]:
        print(f"\n  [{u['_label']}] {u['_name']}")
        desc = u["fields"][DESC_FIELD]
        if len(desc) > 120:
            print(f"  {desc[:120]}...")
        else:
            print(f"  {desc}")
    print(f"{'─'*60}")

    if not apply_mode:
        print("\nDry run complete. Use --apply to update Airtable.")
        return

    # Clean internal fields before sending to Airtable
    airtable_updates = [{"id": u["id"], "fields": u["fields"]} for u in updates]

    print(f"\nApplying {len(airtable_updates)} updates to Airtable...")
    for i in range(0, len(airtable_updates), CHUNK_SIZE):
        batch = airtable_updates[i:i + CHUNK_SIZE]
        table.batch_update(batch)
        print(f"  Updated {min(i + CHUNK_SIZE, len(airtable_updates))}/{len(airtable_updates)}...")

    print(f"\nDone! {len(airtable_updates)} descriptions enriched.")


if __name__ == "__main__":
    main()
