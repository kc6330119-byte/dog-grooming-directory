#!/usr/bin/env python3
"""
Dog Groomer Locator — Off-Topic Record Validator

Scans the clean CSV and flags/removes records that are NOT dog groomers
(pet stores without grooming, vets, pet sitters, etc.).

Usage:
  python3 validate_listings.py          # Scan and report only
  python3 validate_listings.py --remove # Remove flagged records from CSV
"""
import pandas as pd
import re
import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "Groomers_CLEAN.csv")
OUTPUT_FILE = os.path.join(BASE_DIR, "Groomers_VALIDATED.csv")
FLAGGED_FILE = os.path.join(BASE_DIR, "Groomers_FLAGGED.csv")

# Strong positive signals — this IS a groomer
POSITIVE_KEYWORDS = [
    "grooming", "groomer", "groom", "pet spa", "dog spa",
    "bath", "haircut", "deshed", "de-shed", "nail trim",
    "puppy cut", "breed cut", "hand strip", "blow dry",
    "dog wash", "pet wash", "mobile groom", "grooming salon",
    "shampoo", "coat care", "fur care", "paw", "pawz",
    "clipper", "scissor", "styling", "dematting",
]

# Strong negative signals — likely NOT a groomer
NEGATIVE_KEYWORDS = [
    "veterinarian", "veterinary", "vet clinic", "animal hospital",
    "emergency vet", "spay", "neuter", "surgery",
    "pet cemetery", "cremation", "memorial",
    "pest control", "exterminator",
    "car wash", "auto", "laundromat",
    "restaurant", "cafe", "bar & grill",
    "dentist", "dental", "orthodont",
    "hair salon", "beauty salon", "barber shop",
    "tattoo", "piercing",
    "lawn care", "landscaping",
    "plumbing", "electrical", "hvac",
]

# Medium negative — could go either way
MEDIUM_NEGATIVE = [
    "pet sitting", "dog walking", "dog walker",
    "kennel", "boarding only",
    "pet food", "pet supply", "feed store",
    "dog training", "obedience",
    "animal shelter", "rescue", "adoption",
    "aquarium", "fish", "reptile",
]


def word_match(keyword, text):
    """Word-boundary match for stronger signal."""
    pattern = r'(?<![a-zA-Z])' + re.escape(keyword) + r'(?![a-zA-Z])'
    return bool(re.search(pattern, text, re.IGNORECASE))


def score_record(name, description, services, specialties):
    """Score a record for grooming relevance."""
    name_lower = str(name).lower() if pd.notna(name) else ""
    desc_lower = str(description).lower() if pd.notna(description) else ""
    svc_lower = str(services).lower() if pd.notna(services) else ""
    spec_lower = str(specialties).lower() if pd.notna(specialties) else ""

    text = f"{name_lower} {desc_lower} {svc_lower} {spec_lower}"

    pos_score = 0
    neg_score = 0
    flags = []

    # Positive scoring
    for kw in POSITIVE_KEYWORDS:
        if kw in text:
            pos_score += 2
    pos_score = min(pos_score, 6)  # Cap

    # Negative scoring — name has stronger weight
    for kw in NEGATIVE_KEYWORDS:
        if word_match(kw, name_lower):
            neg_score += 5
            flags.append(f"NAME:{kw}")
        elif kw in desc_lower:
            neg_score += 1
            flags.append(f"desc:{kw}")

    for kw in MEDIUM_NEGATIVE:
        if word_match(kw, name_lower):
            neg_score += 2
            flags.append(f"NAME_MED:{kw}")
        elif kw in desc_lower:
            neg_score += 0.5
            flags.append(f"desc_med:{kw}")

    # Classification
    has_name_flag = any(f.startswith("NAME:") for f in flags)

    if has_name_flag and neg_score >= 5:
        classification = "LIKELY NOT GROOMER"
    elif neg_score >= 5 and pos_score < 4:
        classification = "LIKELY NOT GROOMER"
    elif has_name_flag and neg_score >= 2:
        classification = "REVIEW NEEDED"
    elif neg_score >= 2 and pos_score < 3:
        classification = "REVIEW NEEDED"
    else:
        classification = "LIKELY GROOMER"

    return classification, neg_score, pos_score, "; ".join(flags)


def main():
    remove_mode = "--remove" in sys.argv

    print("=" * 60)
    print("Dog Groomer Locator — Listing Validator")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"\nInput records: {len(df)}")

    results = df.apply(
        lambda row: score_record(
            row.get("Name", ""),
            row.get("Description", ""),
            row.get("Services", ""),
            row.get("Specialties", ""),
        ),
        axis=1,
        result_type="expand",
    )
    results.columns = ["classification", "neg_score", "pos_score", "flags"]

    df["classification"] = results["classification"]
    df["neg_score"] = results["neg_score"]
    df["pos_score"] = results["pos_score"]
    df["flags"] = results["flags"]

    # Stats
    counts = df["classification"].value_counts()
    print(f"\nClassification results:")
    for cls, count in counts.items():
        print(f"  {cls}: {count}")

    # Flagged records
    flagged = df[df["classification"] != "LIKELY GROOMER"].sort_values("neg_score", ascending=False)

    if len(flagged) > 0:
        print(f"\nTop 25 flagged records:")
        for _, row in flagged.head(25).iterrows():
            print(f"  [{row['classification']}] {row['Name']} ({row['City']}, {row['State']}) — {row['flags']}")

        flagged[["Name", "City", "State", "classification", "neg_score", "pos_score", "flags"]].to_csv(
            FLAGGED_FILE, index=False
        )
        print(f"\nFlagged records saved: {FLAGGED_FILE}")

    if remove_mode:
        not_groomer = df["classification"] == "LIKELY NOT GROOMER"
        removed_count = not_groomer.sum()
        clean = df[~not_groomer].drop(columns=["classification", "neg_score", "pos_score", "flags"])
        clean.to_csv(OUTPUT_FILE, index=False)
        print(f"\nRemoved {removed_count} non-groomer records")
        print(f"Validated CSV saved: {OUTPUT_FILE} ({len(clean)} records)")
    else:
        # Save without removing, just report
        clean = df.drop(columns=["classification", "neg_score", "pos_score", "flags"])
        clean.to_csv(OUTPUT_FILE, index=False)
        print(f"\nNo records removed (use --remove to remove flagged records)")
        print(f"Output saved: {OUTPUT_FILE} ({len(clean)} records)")


if __name__ == "__main__":
    main()
