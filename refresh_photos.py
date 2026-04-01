#!/usr/bin/env python3
"""
Refresh Photos — Fetch fresh Google Places photos for groomers with empty Photo URL.

Standalone script that:
1. Reads Airtable groomers where Photo URL is blank
2. Looks up each groomer via Google Places API (Text Search) using name + city + state
3. Downloads the best photo to static/images/<slug>.jpg
4. Updates Airtable Photo URL with the local path

Requires env vars: AIRTABLE_API_KEY, AIRTABLE_BASE_ID, GOOGLE_PLACES_API_KEY
Optional: AIRTABLE_TABLE_NAME (defaults to "Groomers")
"""
import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from pyairtable import Api
from slugify import slugify

load_dotenv()

# ── Config ──────────────────────────────────────────────────────────────────

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Groomers")
GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

IMAGES_DIR = Path(__file__).parent / "static" / "images"

# Google Places API endpoints
PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
PLACES_PHOTO_URL_TEMPLATE = "https://places.googleapis.com/v1/{photo_name}/media"

# Rate-limit: small delay between API calls to stay under quota
API_DELAY_SECONDS = 0.3


def check_env():
    """Validate required environment variables are set."""
    missing = []
    if not AIRTABLE_API_KEY:
        missing.append("AIRTABLE_API_KEY")
    if not AIRTABLE_BASE_ID:
        missing.append("AIRTABLE_BASE_ID")
    if not GOOGLE_PLACES_API_KEY:
        missing.append("GOOGLE_PLACES_API_KEY")
    if missing:
        print(f"Error: missing env vars: {', '.join(missing)}")
        print("Set them in .env or export before running.")
        sys.exit(1)


def fetch_groomers_missing_photos():
    """Return Airtable records where Photo URL is empty."""
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)

    formula = "{Photo URL} = ''"
    records = table.all(formula=formula)
    print(f"Found {len(records)} groomers with empty Photo URL.")
    return records


def search_place(name, city, state):
    """Use Google Places Text Search (New) to find a place_id and photo reference.

    Returns (place_id, photo_name) or (None, None) on failure.
    """
    query = f"{name} dog groomer {city} {state}"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.photos",
    }
    body = {"textQuery": query, "maxResultCount": 1}

    try:
        resp = requests.post(PLACES_TEXT_SEARCH_URL, json=body, headers=headers, timeout=15)
        if resp.status_code == 429:
            print("  Rate limited — waiting 5s and retrying once...")
            time.sleep(5)
            resp = requests.post(PLACES_TEXT_SEARCH_URL, json=body, headers=headers, timeout=15)

        if resp.status_code != 200:
            print(f"  Places search {resp.status_code}: {resp.text[:200]}")
            return None, None

        data = resp.json()
        places = data.get("places", [])
        if not places:
            return None, None

        place = places[0]
        place_id = place.get("id")
        photos = place.get("photos", [])
        photo_name = photos[0]["name"] if photos else None
        return place_id, photo_name

    except Exception as e:
        print(f"  Places search error: {e}")
        return None, None


def download_photo(photo_name, dest_path):
    """Download a photo from Google Places Photo (New) API to dest_path.

    Returns True on success.
    """
    url = PLACES_PHOTO_URL_TEMPLATE.format(photo_name=photo_name)
    params = {
        "key": GOOGLE_PLACES_API_KEY,
        "maxWidthPx": 800,
        "skipHttpRedirect": "false",
    }

    try:
        resp = requests.get(url, params=params, timeout=20, stream=True)
        if resp.status_code == 200:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            with open(dest_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        else:
            print(f"  Photo download {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"  Photo download error: {e}")
        return False


def update_airtable_photo_url(record_id, local_path):
    """Write the local image path back to Airtable's Photo URL field."""
    api = Api(AIRTABLE_API_KEY)
    table = api.table(AIRTABLE_BASE_ID, AIRTABLE_TABLE_NAME)
    table.update(record_id, {"Photo URL": local_path})


def main():
    check_env()
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    records = fetch_groomers_missing_photos()
    if not records:
        print("Nothing to do — all groomers have photos.")
        return

    updated = 0
    skipped = 0
    failed = 0

    for record in records:
        fields = record.get("fields", {})
        name = fields.get("Name", "")
        city = fields.get("City", "")
        state = fields.get("State", "")
        slug = slugify(f"{name}-{city}")

        if not name or not city:
            print(f"  Skipping record {record['id']} — missing name or city")
            skipped += 1
            continue

        dest_path = IMAGES_DIR / f"{slug}.jpg"

        # If image already exists locally, just update Airtable
        if dest_path.exists():
            local_url = f"/static/images/{slug}.jpg"
            print(f"  {name} ({city}, {state}) — already cached, updating Airtable")
            update_airtable_photo_url(record["id"], local_url)
            updated += 1
            continue

        print(f"  {name} ({city}, {state}) — searching Google Places...")
        place_id, photo_name = search_place(name, city, state)

        if not photo_name:
            print(f"    No photo found")
            failed += 1
            time.sleep(API_DELAY_SECONDS)
            continue

        if download_photo(photo_name, dest_path):
            local_url = f"/static/images/{slug}.jpg"
            update_airtable_photo_url(record["id"], local_url)
            print(f"    Saved and updated Airtable")
            updated += 1
        else:
            failed += 1

        time.sleep(API_DELAY_SECONDS)

    print(f"\nDone: {updated} updated, {skipped} skipped, {failed} failed")


if __name__ == "__main__":
    main()
