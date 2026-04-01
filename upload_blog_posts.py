#!/usr/bin/env python3
"""
Dog Groomer Locator — Upload Blog Posts to Airtable

Reads blog post data from blog_posts/ directory (JSON files) or inline definitions
and upserts to the Airtable Blog Posts table. Matches on Slug field.

Usage:
  python3 upload_blog_posts.py           # Dry run
  python3 upload_blog_posts.py --apply   # Upload to Airtable
  python3 upload_blog_posts.py --apply --slug how-to-choose-a-dog-groomer  # Single post
"""
import json
import os
import sys
import time
import math
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_BLOG_TABLE_NAME = os.getenv("AIRTABLE_BLOG_TABLE_NAME", "Blog Posts")

BLOG_POSTS_DIR = Path(__file__).parent / "blog_posts"

SINGLE_SELECT_FIELDS = {"Status"}
MULTI_SELECT_FIELDS = {"Tags"}
CHECKBOX_FIELDS = {"Featured"}
DATE_FIELDS = {"Publish Date"}
URL_FIELDS = {"Featured Image"}


def to_airtable_fields(post):
    """Convert post dict to Airtable-compatible fields."""
    fields = {}
    for key, val in post.items():
        if val is None or val == "":
            continue
        if key in CHECKBOX_FIELDS:
            fields[key] = bool(val)
        elif key in MULTI_SELECT_FIELDS:
            if isinstance(val, list):
                fields[key] = val
            else:
                fields[key] = [v.strip() for v in str(val).split(",") if v.strip()]
        elif key in SINGLE_SELECT_FIELDS:
            fields[key] = str(val)
        elif key in DATE_FIELDS:
            fields[key] = str(val)
        else:
            fields[key] = str(val)
    return fields


def fetch_all_records(base_url, headers):
    """Fetch all existing records, paginating."""
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


def load_blog_posts(slug_filter=None):
    """Load all blog posts from blog_posts/ JSON files."""
    posts = []
    if not BLOG_POSTS_DIR.exists():
        print(f"No blog_posts/ directory found at {BLOG_POSTS_DIR}")
        return posts

    files = sorted(BLOG_POSTS_DIR.glob("*.json"))
    for f in files:
        try:
            post = json.loads(f.read_text())
            if slug_filter and post.get("Slug") != slug_filter:
                continue
            posts.append(post)
        except Exception as e:
            print(f"  Error loading {f.name}: {e}")
    return posts


def main():
    apply_mode = "--apply" in sys.argv
    slug_filter = None
    for i, arg in enumerate(sys.argv):
        if arg == "--slug" and i + 1 < len(sys.argv):
            slug_filter = sys.argv[i + 1]

    if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
        print("ERROR: AIRTABLE_API_KEY and AIRTABLE_BASE_ID must be set in .env")
        sys.exit(1)

    print("=" * 60)
    print("Dog Groomer Locator — Blog Posts Airtable Upload")
    print("=" * 60)

    posts = load_blog_posts(slug_filter)
    if not posts:
        print("No blog posts found to upload.")
        return

    print(f"\nPosts to process: {len(posts)}")
    if slug_filter:
        print(f"Filter: --slug {slug_filter}")

    base_url = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_BLOG_TABLE_NAME.replace(' ', '%20')}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json",
    }

    # Fetch existing records, index by Slug
    print("\nFetching existing Airtable records...")
    existing_records = fetch_all_records(base_url, headers)
    existing_index = {}
    for rec in existing_records:
        slug = rec.get("fields", {}).get("Slug")
        if slug:
            existing_index[slug] = {"id": rec["id"], "fields": rec.get("fields", {})}
    print(f"Existing records: {len(existing_records)} ({len(existing_index)} with Slug)")

    new_posts = []
    update_posts = []
    for post in posts:
        fields = to_airtable_fields(post)
        slug = fields.get("Slug", "")
        existing = existing_index.get(slug)
        if existing:
            # Only update changed fields
            changed = {k: v for k, v in fields.items() if existing["fields"].get(k) != v}
            if changed:
                update_posts.append({"id": existing["id"], "fields": changed})
            else:
                print(f"  Unchanged: {slug}")
        else:
            new_posts.append(fields)

    print(f"\n  New:    {len(new_posts)}")
    print(f"  Update: {len(update_posts)}")

    if not apply_mode:
        for p in new_posts:
            print(f"  [NEW] {p.get('Title', '?')} ({p.get('Slug', '?')})")
        for p in update_posts:
            print(f"  [UPDATE] {p['id']} — fields: {list(p['fields'].keys())}")
        print("\nDry run — use --apply to write to Airtable.")
        return

    batch_size = 10
    created = 0
    updated = 0
    errors = 0
    req_count = 0

    if new_posts:
        print(f"\nCreating {len(new_posts)} new records...")
        for i in range(0, len(new_posts), batch_size):
            batch = new_posts[i:i + batch_size]
            payload = {"records": [{"fields": f} for f in batch], "typecast": True}
            resp = requests.post(base_url, headers=headers, json=payload)
            req_count += 1
            if resp.status_code == 200:
                created += len(batch)
                for rec in resp.json().get("records", []):
                    print(f"  Created: {rec.get('fields', {}).get('Title', '?')} ({rec['id']})")
            else:
                errors += len(batch)
                print(f"  Error: {resp.status_code} {resp.text[:300]}")
                if created == 0:
                    return
            if req_count % 4 == 0:
                time.sleep(1)

    if update_posts:
        print(f"\nUpdating {len(update_posts)} records...")
        for i in range(0, len(update_posts), batch_size):
            batch = update_posts[i:i + batch_size]
            payload = {"records": [{"id": r["id"], "fields": r["fields"]} for r in batch], "typecast": True}
            resp = requests.patch(base_url, headers=headers, json=payload)
            req_count += 1
            if resp.status_code == 200:
                updated += len(batch)
            else:
                errors += len(batch)
                print(f"  Error: {resp.status_code} {resp.text[:300]}")
            if req_count % 4 == 0:
                time.sleep(1)

    print(f"\nDone: {created} created, {updated} updated, {errors} errors")


if __name__ == "__main__":
    main()
