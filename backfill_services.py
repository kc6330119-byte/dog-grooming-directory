#!/usr/bin/env python3
"""
Dog Groomer Locator — Service & Specialty Backfill

Scans Name, Description, Hours, and About text to derive Services,
Specialties, and Type for records where these fields are empty.

Usage:
  python3 backfill_services.py              # Dry run — preview changes
  python3 backfill_services.py --apply      # Apply changes to CSV
"""
import pandas as pd
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "Groomers_CLEAN.csv")

# Service keywords — map to our category filter pages
SERVICE_KEYWORDS = {
    "Full Grooming": ["full groom", "full-service", "complete groom", "grooming package",
                       "bath and haircut", "bath & haircut", "wash and cut"],
    "Bath & Brush": ["bath and brush", "bath & brush", "bath only", "bathing",
                      "shampoo", "wash only", "dog wash"],
    "Nail Trimming": ["nail trim", "nail clip", "nail grinding", "nail care",
                       "pawdicure", "paw care", "dremel"],
    "Deshedding": ["deshed", "de-shed", "shedding", "furminator", "undercoat removal",
                    "undercoat rake", "blow out"],
    "Teeth Brushing": ["teeth brush", "teeth clean", "dental", "tooth"],
    "Ear Cleaning": ["ear clean", "ear care", "ear wash"],
    "Flea Treatment": ["flea", "tick", "flea bath", "flea dip", "parasite"],
    "Creative Grooming": ["creative groom", "color", "dye", "stencil", "artistic"],
    "Hand Stripping": ["hand strip", "hand-strip", "stripping"],
    "Anal Gland Expression": ["anal gland", "gland expression"],
    "Medicated Bath": ["medicated bath", "medicated shampoo", "therapeutic bath",
                        "oatmeal bath", "hypoallergenic"],
    "Coat Conditioning": ["conditioning", "deep condition", "coat treatment",
                           "hot oil", "moisturizing"],
}

SPECIALTY_KEYWORDS = {
    "Breed-Specific Styling": ["breed specific", "breed-specific", "show groom", "show cut",
                                "breed standard", "hand scissor", "pattern cut", "continental"],
    "Mobile Grooming": ["mobile groom", "mobile pet", "come to you", "we come to",
                         "mobile van", "grooming van", "house call", "on location"],
    "Anxious Dogs": ["anxious", "nervous", "fearful", "gentle handling", "fear-free",
                      "low stress", "low-stress", "calming", "patience"],
    "Senior Dogs": ["senior dog", "elderly", "older dog", "geriatric", "gentle care"],
    "Large Breeds": ["large breed", "giant breed", "big dog", "xl", "great dane",
                      "mastiff", "newfoundland", "st. bernard"],
    "Small Breeds": ["small breed", "toy breed", "small dog", "teacup", "chihuahua",
                      "yorkie", "yorkshire"],
    "Doodle Specialist": ["doodle", "goldendoodle", "labradoodle", "bernedoodle",
                           "cockapoo", "aussiedoodle"],
    "Poodle Specialist": ["poodle", "standard poodle", "miniature poodle", "toy poodle"],
    "Double Coat Expert": ["double coat", "undercoat", "thick coat", "husky",
                            "malamute", "samoyed", "german shepherd", "golden retriever"],
    "Cat Grooming": ["cat groom", "feline", "cat bath", "cats and dogs", "cats & dogs"],
    "Puppy First Groom": ["puppy", "first groom", "puppy introduction", "young dog"],
    "AKC/Show Grooming": ["akc", "show dog", "competition", "conformation",
                            "best in show", "show ring"],
}

TYPE_KEYWORDS = {
    "Mobile Grooming": ["mobile groom", "mobile pet", "mobile van", "grooming van",
                         "we come to", "come to you", "house call"],
    "Self-Service Wash": ["self-service", "self service", "self-wash", "self wash",
                           "diy wash", "u-wash", "you wash"],
    "Pet Spa": ["pet spa", "dog spa", "luxury groom", "spa treatment", "pamper"],
    "Pet Store with Grooming": ["pet store", "pet supply", "pet shop", "petco",
                                 "petsmart", "pet supplies plus"],
}


def get_searchable_text(row):
    """Combine all text fields for keyword analysis."""
    parts = []
    for field in ["Name", "Description", "Hours", "Services", "Specialties"]:
        val = row.get(field, "")
        if pd.notna(val) and str(val).strip():
            parts.append(str(val))
    return " ".join(parts).lower()


def derive_from_text(text, keyword_map):
    """Match keywords against text and return matching categories."""
    matches = []
    for category, keywords in keyword_map.items():
        if any(kw in text for kw in keywords):
            matches.append(category)
    return sorted(matches)


def main():
    apply_mode = "--apply" in sys.argv

    print("=" * 60)
    print("Dog Groomer Locator — Service & Specialty Backfill")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"\nInput records: {len(df)}")

    empty_services = (df["Services"].isna() | (df["Services"].str.strip() == "")).sum()
    empty_specialties = (df["Specialties"].isna() | (df["Specialties"].str.strip() == "")).sum()
    print(f"Empty Services: {empty_services}/{len(df)}")
    print(f"Empty Specialties: {empty_specialties}/{len(df)}")

    services_filled = 0
    specialties_filled = 0
    type_changed = 0

    for idx, row in df.iterrows():
        text = get_searchable_text(row)

        # Backfill Services if empty
        current_services = str(row.get("Services", ""))
        if pd.isna(row.get("Services")) or current_services.strip() == "":
            new_services = derive_from_text(text, SERVICE_KEYWORDS)
            if new_services:
                df.at[idx, "Services"] = ", ".join(new_services)
                services_filled += 1

        # Backfill Specialties if empty
        current_specs = str(row.get("Specialties", ""))
        if pd.isna(row.get("Specialties")) or current_specs.strip() == "":
            new_specs = derive_from_text(text, SPECIALTY_KEYWORDS)
            if new_specs:
                df.at[idx, "Specialties"] = ", ".join(new_specs)
                specialties_filled += 1

        # Refine Type based on deeper keyword analysis
        current_type = str(row.get("Type", ""))
        if current_type == "Full-Service Salon":
            for type_name, keywords in TYPE_KEYWORDS.items():
                if any(kw in text for kw in keywords):
                    df.at[idx, "Type"] = type_name
                    type_changed += 1
                    break

    print(f"\nServices backfilled: {services_filled}")
    print(f"Specialties backfilled: {specialties_filled}")
    print(f"Types refined: {type_changed}")

    # Show sample
    print(f"\nSample enriched records:")
    enriched = df[(df["Services"].notna()) & (df["Services"].str.strip() != "")].head(5)
    for _, row in enriched.iterrows():
        print(f"  {row['Name']} ({row['City']}, {row['State']})")
        print(f"    Services: {row['Services']}")
        print(f"    Specialties: {row.get('Specialties', '')}")
        print(f"    Type: {row['Type']}")
        print()

    if apply_mode:
        df.to_csv(INPUT_FILE, index=False)
        print(f"Changes applied to {INPUT_FILE}")
    else:
        print(f"Dry run — no changes saved. Use --apply to write changes.")


if __name__ == "__main__":
    main()
