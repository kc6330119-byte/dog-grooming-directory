#!/usr/bin/env python3
"""
Dog Groomer Locator — Upload Clean CSV to Airtable (Upsert)

Reads Groomers_VALIDATED.csv and upserts to the Airtable Groomers table.
Matches existing records by Google Maps URL:
  - Existing records: updates operational fields, preserves editorial fields
  - New records: creates full record

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

# Match key for upsert
MATCH_KEY = "Google Maps URL"

# Fields to preserve on existing records (never overwrite these on update)
PRESERVE_FIELDS = {"Name", "Decription", "Featured", "Date Added"}


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


def fetch_all_records(base_url, headers):
    """Fetch all existing Airtable records, paginating through all pages."""
    records = []
    params = {}
    while True:
        resp = requests.get(base_url, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json()
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
        params = {"offset": offset}
        time.sleep(0.25)
    return records


def build_existing_index(records):
    """Build a dict of Google Maps URL -> (record_id, fields) from Airtable records."""
    index = {}
    for rec in records:
        fields = rec.get("fields", {})
        gmap_url = fields.get(MATCH_KEY)
        if gmap_url:
            index[gmap_url] = {"id": rec["id"], "fields": fields}
    return index


def compute_update_fields(new_fields, existing_fields):
    """Return only fields that should be updated (excludes preserved fields, unchanged values)."""
    update = {}
    for key, val in new_fields.items():
        if key in PRESERVE_FIELDS:
            continue
        if key == MATCH_KEY:
            continue
        existing_val = existing_fields.get(key)
        if existing_val != val:
            update[key] = val
    return update


def main():
    apply_mode = "--apply" in sys.argv

    print("=" * 60)
    print("Dog Groomer Locator — Airtable Upsert")
    print("=" * 60)

    df = pd.read_csv(INPUT_FILE)
    print(f"\nCSV records: {len(df)}")

    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Fetch all existing records and index by Google Maps URL
    print("Fetching existing Airtable records...")
    existing_records = fetch_all_records(base_url, headers)
    existing_index = build_existing_index(existing_records)
    print(f"Existing Airtable records: {len(existing_records)} ({len(existing_index)} with Google Maps URL)")

    # Classify each CSV row as new, update, or unchanged
    new_records = []
    update_records = []
    unchanged_count = 0

    for _, row in df.iterrows():
        fields = csv_to_airtable_fields(row)
        gmap_url = fields.get(MATCH_KEY)

        if not gmap_url:
            new_records.append(fields)
            continue

        existing = existing_index.get(gmap_url)
        if not existing:
            new_records.append(fields)
        else:
            update_fields = compute_update_fields(fields, existing["fields"])
            if update_fields:
                update_records.append({"id": existing["id"], "fields": update_fields})
            else:
                unchanged_count += 1

    print(f"\n  New:       {len(new_records)}")
    print(f"  Update:    {len(update_records)}")
    print(f"  Unchanged: {unchanged_count}")

    if not apply_mode:
        if new_records:
            print(f"\nSample new record fields: {list(new_records[0].keys())}")
        if update_records:
            print(f"Sample update fields: {list(update_records[0]['fields'].keys())}")
        print(f"\nDry run — use --apply to write changes to Airtable.")
        return

    # Create new records in batches of 10
    batch_size = 10
    req_count = 0
    created = 0
    errors = 0

    if new_records:
        total_batches = math.ceil(len(new_records) / batch_size)
        print(f"\nCreating {len(new_records)} new records in {total_batches} batches...")
        for i in range(0, len(new_records), batch_size):
            batch = new_records[i:i + batch_size]
            payload = {
                "records": [{"fields": f} for f in batch],
                "typecast": True,
            }
            resp = requests.post(base_url, headers=headers, json=payload)
            req_count += 1
            if resp.status_code == 200:
                created += len(batch)
            else:
                errors += len(batch)
                if created == 0:
                    print(f"  First batch failed: {resp.status_code} {resp.text[:300]}")
                    return
                print(f"  Batch error at record {i}: {resp.status_code}")

            if req_count % 4 == 0:
                time.sleep(1)

        print(f"  Created {created} records ({errors} errors)")

    # Update existing records in batches of 10
    updated = 0
    update_errors = 0

    if update_records:
        total_batches = math.ceil(len(update_records) / batch_size)
        print(f"\nUpdating {len(update_records)} records in {total_batches} batches...")
        for i in range(0, len(update_records), batch_size):
            batch = update_records[i:i + batch_size]
            payload = {
                "records": [{"id": r["id"], "fields": r["fields"]} for r in batch],
                "typecast": True,
            }
            resp = requests.patch(base_url, headers=headers, json=payload)
            req_count += 1
            if resp.status_code == 200:
                updated += len(batch)
            else:
                update_errors += len(batch)
                if updated == 0:
                    print(f"  First update batch failed: {resp.status_code} {resp.text[:300]}")
                    return
                print(f"  Batch error at record {i}: {resp.status_code}")

            if req_count % 4 == 0:
                time.sleep(1)

        print(f"  Updated {updated} records ({update_errors} errors)")

    print(f"\nUpsert complete: {created} created, {updated} updated, {unchanged_count} unchanged, {errors + update_errors} errors")


if __name__ == "__main__":
    main()
