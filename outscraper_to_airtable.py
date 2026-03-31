#!/usr/bin/env python3
"""
Dog Groomer Locator — Outscraper to Airtable ETL Pipeline

Reads the Outscraper XLSX export, deduplicates, cleans, maps columns,
derives services/specialties/type, and outputs a clean CSV ready for
Airtable import.

Adapted from Senior Home Care Directory reference implementation.
"""
import pandas as pd
import re
import json
import os
from datetime import datetime
from slugify import slugify

# ==============================
# CONFIGURATION
# ==============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

OUTSCRAPER_FILE = os.path.join(BASE_DIR, "Outscraper-20260331065259m1d_pet_groomer.xlsx")
OUTPUT_FILE = os.path.join(BASE_DIR, "Groomers_CLEAN.csv")
DUPLICATES_FILE = os.path.join(BASE_DIR, "Groomers_DUPLICATES.csv")

# ==============================
# LOAD DATA
# ==============================

print("=" * 60)
print("Dog Groomer Locator — Outscraper ETL Pipeline")
print("=" * 60)

df = pd.read_excel(OUTSCRAPER_FILE)
print(f"\nOriginal Outscraper rows: {len(df)}")

df.columns = df.columns.str.strip().str.lower()

# ==============================
# FIELD HELPERS
# ==============================

def clean_field(val):
    """Convert a field value to a clean string, returning '' for nan/empty."""
    if pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" or s == "" else s

def normalize(series):
    return series.astype(str).str.strip().str.lower()

STATE_MAP = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "DC": "District of Columbia", "FL": "Florida", "GA": "Georgia", "HI": "Hawaii",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "IA": "Iowa",
    "KS": "Kansas", "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine",
    "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota",
    "MS": "Mississippi", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NY": "New York", "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
    "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas",
    "UT": "Utah", "VT": "Vermont", "VA": "Virginia", "WA": "Washington",
    "WV": "West Virginia", "WI": "Wisconsin", "WY": "Wyoming"
}

STATE_ABBREV = {v: k.lower() for k, v in STATE_MAP.items()}

# Also handle common variations
STATE_NORMALIZE = {
    "washington dc": "District of Columbia",
    "district of columbia": "District of Columbia",
    "d.c.": "District of Columbia",
}

def normalize_state(state):
    """Convert state abbreviations/variants to full names."""
    s = str(state).strip()
    # Check normalized variant map first
    if s.lower() in STATE_NORMALIZE:
        return STATE_NORMALIZE[s.lower()]
    # Check abbreviation map
    if s.upper() in STATE_MAP:
        return STATE_MAP[s.upper()]
    # Title case fallback
    return s.title()

def format_phone(phone):
    """Format phone number as (XXX) XXX-XXXX."""
    if pd.isna(phone):
        return ""
    digits = re.sub(r"\D", "", str(phone))
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    return ""

def format_hours(hours_raw):
    """Format working hours from Outscraper JSON format."""
    if pd.isna(hours_raw):
        return ""
    try:
        if isinstance(hours_raw, str):
            hours_dict = json.loads(hours_raw.replace("'", '"'))
        else:
            hours_dict = hours_raw
    except (json.JSONDecodeError, ValueError):
        return str(hours_raw)

    if not isinstance(hours_dict, dict):
        return str(hours_raw)

    formatted = []
    all_times = set()
    for day, times in hours_dict.items():
        if times:
            time_str = " & ".join(times).replace("-", "\u2013")
            formatted.append(f"{day}: {time_str}")
            all_times.add(time_str)

    if len(all_times) == 1 and len(formatted) == 7:
        return f"Daily: {list(all_times)[0]}"
    return ", ".join(formatted)

def generate_slug(row):
    """Generate a URL-friendly slug from name, city, and state abbreviation."""
    name = clean_field(row.get("name", ""))
    city = clean_field(row.get("city", ""))
    state = normalize_state(str(row.get("state", "")))
    state_abbr = STATE_ABBREV.get(state, "")
    return slugify(f"{name} {city} {state_abbr}")

def combine_description(row):
    """Get the best description from available fields."""
    parts = [
        clean_field(row.get("website_description", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("company_insights.description", "")),
        clean_field(row.get("about", "")),
    ]
    parts = [p for p in parts if p]
    if not parts:
        return ""
    return max(parts, key=len)

def get_text_blob(row):
    """Combine all text fields for keyword analysis."""
    return " ".join([
        clean_field(row.get("about", "")),
        clean_field(row.get("description", "")),
        clean_field(row.get("website_description", "")),
        clean_field(row.get("subtypes", "")),
        clean_field(row.get("company_insights.description", "")),
        clean_field(row.get("category", "")),
        clean_field(row.get("name", "")),
    ]).lower()

def derive_services(row):
    """Derive grooming services from listing text."""
    SERVICE_KEYWORDS = {
        "Full Grooming": ["full groom", "full-service groom", "full service groom", "complete groom",
                          "bath and haircut", "bath & haircut", "grooming package"],
        "Bath & Brush": ["bath and brush", "bath & brush", "bath only", "bathing", "shampoo"],
        "Nail Trimming": ["nail trim", "nail clip", "nail grinding", "nail care", "pawdicure"],
        "Deshedding": ["deshed", "de-shed", "shedding treatment", "furminator"],
        "Teeth Brushing": ["teeth brush", "teeth clean", "dental", "tooth brush"],
        "Ear Cleaning": ["ear clean", "ear care"],
        "Flea Treatment": ["flea", "tick treatment", "flea bath", "flea dip"],
        "Creative Grooming": ["creative groom", "color", "dye", "stencil"],
        "Hand Stripping": ["hand strip", "hand-strip"],
        "Puppy First Groom": ["puppy", "first groom", "puppy introduction"],
        "Cat Grooming": ["cat groom", "feline groom", "cat bath"],
    }

    text = get_text_blob(row)
    services = set()
    for service, keywords in SERVICE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            services.add(service)
    return ", ".join(sorted(services))

def derive_specialties(row):
    """Derive grooming specialties from listing text."""
    SPECIALTY_KEYWORDS = {
        "Breed-Specific Styling": ["breed specific", "breed-specific", "show groom", "show cut",
                                    "breed standard", "hand scissor"],
        "Mobile Grooming": ["mobile groom", "mobile pet", "come to you", "we come to",
                            "mobile van", "grooming van", "house call"],
        "Anxious Dogs": ["anxious", "nervous", "fearful", "gentle handling", "fear-free",
                         "low stress", "low-stress", "calming"],
        "Senior Dogs": ["senior dog", "elderly dog", "older dog", "geriatric"],
        "Large Breeds": ["large breed", "giant breed", "big dog", "xl dog", "great dane",
                         "st. bernard", "mastiff"],
        "Small Breeds": ["small breed", "toy breed", "small dog", "teacup"],
        "Doodle Specialist": ["doodle", "goldendoodle", "labradoodle", "bernedoodle"],
        "Poodle Specialist": ["poodle", "standard poodle", "miniature poodle"],
        "Double Coat Expert": ["double coat", "undercoat", "thick coat", "husky", "malamute"],
        "Medicated Baths": ["medicated bath", "medicated shampoo", "skin condition",
                            "dermatitis", "allergy"],
    }

    text = get_text_blob(row)
    specialties = set()
    for specialty, keywords in SPECIALTY_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            specialties.add(specialty)
    return ", ".join(sorted(specialties))

def derive_type(row):
    """Derive business type from listing text."""
    text = get_text_blob(row)

    if any(kw in text for kw in ["mobile groom", "mobile pet", "mobile van",
                                  "grooming van", "we come to", "come to you",
                                  "house call"]):
        return "Mobile Grooming"
    if any(kw in text for kw in ["self-service", "self service", "self-wash",
                                  "self wash", "diy wash", "u-wash", "you wash"]):
        return "Self-Service Wash"
    if any(kw in text for kw in ["pet spa", "dog spa", "luxury groom", "spa treatment"]):
        return "Pet Spa"
    if any(kw in text for kw in ["pet store", "pet supply", "pet shop"]):
        return "Pet Store with Grooming"

    return "Full-Service Salon"

def col(name):
    """Get column from dataframe or return empty series."""
    return df[name] if name in df.columns else pd.Series([""] * len(df))

# ==============================
# INTERNAL DEDUPE
# ==============================

print("\nDeduplicating...")

# Normalize key fields
df["name_clean"] = normalize(df.get("name", pd.Series()))
df["city_clean"] = normalize(df.get("city", pd.Series()))
df["state_clean"] = normalize(df.get("state", pd.Series()))
df["location_link_clean"] = normalize(df.get("location_link", pd.Series()))
df["street_clean"] = normalize(df.get("street", pd.Series()))

before = len(df)

# Primary dedup: by Google Maps location_link
df = df.drop_duplicates(subset=["location_link_clean"])
after_link = len(df)
print(f"  Removed by duplicate location_link: {before - after_link}")

# Secondary dedup: by name + street
df = df.drop_duplicates(subset=["name_clean", "street_clean"])
after_street = len(df)
print(f"  Removed by duplicate name+street: {after_link - after_street}")

# Tertiary dedup: by name + city + state
df = df.drop_duplicates(subset=["name_clean", "city_clean", "state_clean"])
after_city = len(df)
print(f"  Removed by duplicate name+city+state: {after_street - after_city}")

total_removed = before - after_city
print(f"  Total duplicates removed: {total_removed}")
print(f"  Records after dedupe: {len(df)}")

df = df.reset_index(drop=True)

# ==============================
# BUILD OUTPUT
# ==============================

print("\nMapping columns and deriving fields...")

output = pd.DataFrame()

output["Name"] = col("name").apply(clean_field)
output["Slug"] = df.apply(generate_slug, axis=1)

# Disambiguate duplicate slugs by appending zip code
dup_slugs = output["Slug"][output["Slug"].duplicated(keep=False)]
for slug_val in dup_slugs.unique():
    mask = output["Slug"] == slug_val
    zips = col("postal_code")[mask].apply(clean_field)
    output.loc[mask, "Slug"] = output.loc[mask, "Slug"] + "-" + zips.apply(slugify)
output["Description"] = df.apply(combine_description, axis=1)
output["Address"] = col("street").apply(clean_field)
output["City"] = col("city").apply(clean_field)
output["State"] = col("state").apply(normalize_state)
output["Zip"] = col("postal_code").apply(clean_field)
output["Phone"] = col("phone").apply(format_phone)
output["Website URL"] = col("website").apply(clean_field)
output["Google Maps URL"] = col("location_link").apply(clean_field)
output["Photo URL"] = col("photo").apply(clean_field)
output["Hours"] = col("working_hours").apply(format_hours)
output["Services"] = df.apply(derive_services, axis=1)
output["Specialties"] = df.apply(derive_specialties, axis=1)
output["Type"] = df.apply(derive_type, axis=1)
output["Price Range"] = col("prices").apply(clean_field)
output["Rating"] = col("rating")
output["Review Count"] = col("reviews")
output["Status"] = "Active"
output["Featured"] = False
output["Date Added"] = datetime.today().strftime("%Y-%m-%d")
output["Latitude"] = col("latitude")
output["Longitude"] = col("longitude")

# Final column order matching Airtable schema
FINAL_COLUMNS = [
    "Name", "Slug", "Description", "Address", "City", "State", "Zip",
    "Phone", "Website URL", "Google Maps URL", "Photo URL", "Hours",
    "Services", "Specialties", "Type", "Price Range",
    "Rating", "Review Count", "Status", "Featured", "Date Added",
    "Latitude", "Longitude",
]

for col_name in FINAL_COLUMNS:
    if col_name not in output.columns:
        output[col_name] = ""

output = output[FINAL_COLUMNS]

# Remove rows with no name or no city
output = output[output["Name"].str.strip() != ""]
output = output[output["City"].str.strip() != ""]

# ==============================
# STATS
# ==============================

print(f"\nFinal output: {len(output)} records")
print(f"\nState distribution:")
state_counts = output["State"].value_counts().sort_index()
for state, count in state_counts.items():
    print(f"  {state}: {count}")

print(f"\nType distribution:")
type_counts = output["Type"].value_counts()
for t, count in type_counts.items():
    print(f"  {t}: {count}")

has_desc = (output["Description"].str.strip() != "").sum()
has_phone = (output["Phone"].str.strip() != "").sum()
has_website = (output["Website URL"].str.strip() != "").sum()
has_services = (output["Services"].str.strip() != "").sum()
has_specialties = (output["Specialties"].str.strip() != "").sum()

print(f"\nField coverage:")
print(f"  Has description: {has_desc}/{len(output)} ({100*has_desc//len(output)}%)")
print(f"  Has phone: {has_phone}/{len(output)} ({100*has_phone//len(output)}%)")
print(f"  Has website: {has_website}/{len(output)} ({100*has_website//len(output)}%)")
print(f"  Has services: {has_services}/{len(output)} ({100*has_services//len(output)}%)")
print(f"  Has specialties: {has_specialties}/{len(output)} ({100*has_specialties//len(output)}%)")

# ==============================
# SAVE OUTPUT
# ==============================

output.to_csv(OUTPUT_FILE, index=False)
print(f"\n{'=' * 60}")
print(f"Clean CSV saved: {OUTPUT_FILE}")
print(f"{'=' * 60}")
print(f"\nNext steps:")
print(f"1. Run validate_websites.py to check/clear bad URLs")
print(f"2. Run auto_descriptions.py to enrich thin descriptions")
print(f"3. Run backfill_services.py to populate Services/Specialties")
print(f"4. Run validate_listings.py to remove off-topic records")
print(f"5. Import final CSV to Airtable")
