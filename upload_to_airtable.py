#!/usr/bin/env python3
"""
Dog Groomer Locator — Upload Clean CSV to Airtable

Reads Groomers_VALIDATED.csv and batch-uploads to the Airtable Groomers table.
Clears existing placeholder records first.

Usage:
  python3 upload_to_airtable.py          # Dry run
  python3 upload_to_airtable.py --apply  # Upload to Airtable
"""
import pandas as pd
import requests
import sys
import os
import math
import time
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_FILE = os.path.join(BASE_DIR, "Groomers_VALIDATED.csv")

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Groomers")

# Airtable field type mapping
# multipleSelects fields need arrays of {"name": value}
MULTI_SELECT_FIELDS = {"Services", "Specialties", "Amenities"}
SINGLE_SELECT_FIELDS = {"Type", "Price Range", "Status"}
NUMBER_FIELDS = {"Rating", "Latitude", "Longitude", "Review Count"}
CHECKBOX_FIELDS = {"Featured"}
DATE_FIELDS = {"Date Added"}
URL_FIELDS = {"Website URL", "Google Maps URL", "Photo URL"}

# CSV column -> Airtable field name mapping (handle typo in Airtable)
FIELD_MAP = {
    "Description": "Decription",  # Airtable has a typo
}

# Fields to skip (not in Airtable schema)
SKIP_FIELDS = {"Slug"}


def csv_to_airtable_fields(row):
    """Convert a CSV row to Airtable-compatible field dict."""
    fields = {}
    for col, val in row.items():
        if col in SKIP_FIELDS:
            continue
        if pd.isna(val) or str(val).strip() == "":
            continue

        # Map column name if needed
        airtable_field = FIELD_MAP.get(col, col)
        val_str = str(val).strip()

        if col in NUMBER_FIELDS:
            if col == "Review Count":
                fields[airtable_field] = int(float(val))
            else:
                fields[airtable_field] = float(val)
        elif col in CHECKBOX_FIELDS:
            fields[airtable_field] = val_str.lower() in ("true", "1", "yes")
        elif col in DATE_FIELDS:
            fields[airtable_field] = val_str  # ISO format YYYY-MM-DD
        elif col in MULTI_SELECT_FIELDS:
            # Split comma-separated values into array of select option names
            options = [v.strip() for v in val_str.split(",") if v.strip()]
            if options:
                fields[airtable_field] = options
        elif col in SINGLE_SELECT_FIELDS:
            fields[airtable_field] = val_str
        elif col in URL_FIELDS:
            fields[airtable_field] = val_str
        else:
            fields[airtable_field] = val_str

    return fields


def main():
    apply_mode = "--apply" in sys.argv

    print("=" * 60)
    print("Dog Groomer Locator — Airtable Upload")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"\nRecords to upload: {len(df)}")

    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Check existing records
    resp = requests.get(base_url, headers=headers)
    existing = resp.json().get("records", [])
    print(f"Existing Airtable records: {len(existing)}")

    if not apply_mode:
        sample = csv_to_airtable_fields(df.iloc[0])
        print(f"\nSample record fields: {list(sample.keys())}")
        print(f"\nDry run — would upload {len(df)} records to Airtable.")
        print(f"Use --apply to upload.")
        return

    # Delete existing placeholder records
    if existing:
        print(f"\nDeleting {len(existing)} existing records...")
        record_ids = [r["id"] for r in existing]
        for i in range(0, len(record_ids), 10):
            batch_ids = record_ids[i:i + 10]
            params = "&".join(f"records[]={rid}" for rid in batch_ids)
            requests.delete(f"{base_url}?{params}", headers=headers)
        print(f"  Deleted {len(record_ids)} records")

    # Prepare records for upload
    all_fields = []
    for _, row in df.iterrows():
        all_fields.append(csv_to_airtable_fields(row))

    # Batch upload with typecast (Airtable limit: 10 per batch, 5 requests/sec)
    batch_size = 10
    total_batches = math.ceil(len(all_fields) / batch_size)
    uploaded = 0
    errors = 0

    print(f"\nUploading {len(all_fields)} records in {total_batches} batches...")
    for i in range(0, len(all_fields), batch_size):
        batch = all_fields[i:i + batch_size]
        payload = {
            "records": [{"fields": f} for f in batch],
            "typecast": True,
        }
        resp = requests.post(base_url, headers=headers, json=payload)
        if resp.status_code == 200:
            uploaded += len(batch)
        else:
            errors += len(batch)
            if uploaded == 0:
                print(f"\nFirst batch failed: {resp.status_code} {resp.text[:300]}")
                print(f"Sample record: {batch[0]}")
                return
            print(f"  Batch error at record {i}: {resp.status_code}")

        if uploaded % 500 == 0 or (uploaded + errors) == len(all_fields):
            print(f"  Uploaded {uploaded}/{len(all_fields)} records ({errors} errors)")

        # Rate limit: ~4 batches/sec to stay under Airtable's 5 req/sec
        if (i // batch_size) % 4 == 3:
            time.sleep(1)

    print(f"\nUpload complete: {uploaded} records uploaded, {errors} errors")


if __name__ == "__main__":
    main()
