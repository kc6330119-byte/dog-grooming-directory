#!/usr/bin/env python3
"""
Dog Groomer Locator - Static Site Generator

Fetches dog groomer listings from Airtable and generates a static HTML site.
Falls back to sample data if Airtable is not configured.
"""
import json
import os
import shutil
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import openpyxl
import requests
import markdown as md_lib
from jinja2 import Environment, FileSystemLoader
from markupsafe import Markup
from slugify import slugify

import config


def get_sample_data():
    """Return sample groomers for testing without Airtable."""
    return [
        {
            "name": "Pampered Paws Grooming Salon",
            "slug": "pampered-paws-grooming-salon-nashville",
            "description": "A full-service dog grooming salon offering breed-specific haircuts, hand-stripping, "
                           "deshedding treatments, nail grinding, and spa packages. Pampered Paws has served Nashville "
                           "pet owners for over 12 years with a focus on low-stress handling and personalized care for "
                           "every dog. Open six days a week with evening appointments available.",
            "address": "123 Main St",
            "city": "Nashville",
            "state": "Tennessee",
            "state_slug": "tennessee",
            "zip": "37201",
            "phone": "(615) 555-0100",
            "website_url": "",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Sat: 8am - 6pm",
            "services": ["Full Grooming", "Bath & Brush", "Nail Trimming", "Deshedding", "Teeth Brushing"],
            "specialties": ["Breed-Specific Styling", "Show Grooming"],
            "price_range": "$$",
            "type": "Full-Service Salon",
            "status": "Active",
            "date_added": "2025-01-01",
            "rating": 4.8,
            "review_count": 215,
            "last_modified": "2025-06-15",
        },
        {
            "name": "Bark & Clean Mobile Grooming",
            "slug": "bark-and-clean-mobile-grooming-austin",
            "description": "Bark & Clean brings professional grooming directly to your door in a fully equipped, "
                           "climate-controlled mobile grooming van. Specializing in anxious dogs and senior pets, they "
                           "offer one-on-one grooming sessions that reduce stress. Services include full grooming, "
                           "bath-only options, nail care, and puppy first groom introductions.",
            "address": "456 River Rd",
            "city": "Austin",
            "state": "Texas",
            "state_slug": "texas",
            "zip": "78701",
            "phone": "(512) 555-0200",
            "website_url": "",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Tue-Sun: 9am - 5pm",
            "services": ["Full Grooming", "Bath Only", "Nail Trimming", "Puppy First Groom"],
            "specialties": ["Mobile Grooming", "Anxious Dogs"],
            "price_range": "$$$",
            "type": "Mobile Grooming",
            "status": "Active",
            "date_added": "2025-01-02",
            "rating": 4.9,
            "review_count": 143,
            "last_modified": "2025-07-01",
        },
        {
            "name": "Suds & Scissors Pet Spa",
            "slug": "suds-and-scissors-pet-spa-chicago",
            "description": "Suds & Scissors is a neighborhood pet spa offering professional grooming for dogs and cats. "
                           "Their team of certified groomers handles all breeds and sizes, from Chihuahuas to Great Danes. "
                           "Services include spa baths, breed-standard cuts, creative grooming, and a self-service dog wash "
                           "station for DIY owners.",
            "address": "789 Oak Ave",
            "city": "Chicago",
            "state": "Illinois",
            "state_slug": "illinois",
            "zip": "60601",
            "phone": "(312) 555-0300",
            "website_url": "",
            "google_maps_url": "",
            "photo_url": "",
            "hours": "Mon-Fri: 7am - 7pm, Sat: 8am - 5pm",
            "services": ["Full Grooming", "Cat Grooming", "Self-Service Wash", "Creative Grooming"],
            "specialties": ["All Breeds", "Cat Grooming"],
            "price_range": "$$",
            "type": "Full-Service Salon",
            "status": "Active",
            "date_added": "2025-01-03",
            "rating": 4.6,
            "review_count": 89,
            "last_modified": "2025-08-10",
        },
    ]


def fetch_from_airtable():
    """Fetch groomers from Airtable API."""
    if not config.AIRTABLE_API_KEY or not config.AIRTABLE_BASE_ID:
        print("Airtable not configured. Using sample data.")
        return None

    try:
        from pyairtable import Api

        api = Api(config.AIRTABLE_API_KEY)
        table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME)
        records = table.all()

        groomers = []
        for record in records:
            fields = record.get("fields", {})

            if fields.get("Status") == "Draft":
                continue

            state_name = fields.get("State", "")
            groomer = {
                "_airtable_id": record.get("id", ""),
                "name": fields.get("Name", ""),
                "slug": slugify(fields.get("Name", "") + "-" + fields.get("City", "")),
                "description": fields.get("Decription", fields.get("Description", "")),
                "address": fields.get("Address", ""),
                "city": fields.get("City", ""),
                "state": state_name,
                "state_slug": slugify(state_name),
                "zip": fields.get("Zip", ""),
                "phone": fields.get("Phone", ""),
                "website_url": fields.get("Website URL", ""),
                "google_maps_url": fields.get("Google Maps URL", ""),
                "photo_url": fields.get("Photo URL", ""),
                "hours": fields.get("Hours", ""),
                "services": fields.get("Services", []),
                "specialties": fields.get("Specialties", []),
                "price_range": fields.get("Price Range", ""),
                "type": fields.get("Type", "Full-Service Salon"),
                "status": fields.get("Status", "Active"),
                "featured": fields.get("Featured", False),
                "date_added": fields.get("Date Added", ""),
                "rating": fields.get("Rating", 0),
                "review_count": fields.get("Review Count", 0),
                "latitude": fields.get("Latitude", ""),
                "longitude": fields.get("Longitude", ""),
                "last_modified": fields.get("Last Modified", fields.get("Date Added", "")),
            }
            groomers.append(groomer)

        print(f"Fetched {len(groomers)} groomers from Airtable.")

        # Disambiguate duplicate slugs by appending zip code
        slug_groups = {}
        for g in groomers:
            slug_groups.setdefault(g["slug"], []).append(g)
        for slug, group in slug_groups.items():
            if len(group) > 1:
                for g in group:
                    zip_code = g.get("zip", "").strip()
                    if zip_code:
                        g["slug"] = f"{slug}-{slugify(zip_code)}"

        return groomers

    except Exception as e:
        print(f"Error fetching from Airtable: {e}")
        return None


def clear_airtable_photo_url(airtable_id):
    """Clear the Photo URL field in Airtable for a groomer with an expired URL."""
    if not config.AIRTABLE_API_KEY or not config.AIRTABLE_BASE_ID or not airtable_id:
        return
    try:
        from pyairtable import Api
        api = Api(config.AIRTABLE_API_KEY)
        table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_TABLE_NAME)
        table.update(airtable_id, {"Photo URL": ""})
    except Exception as e:
        print(f"  Warning: could not clear Airtable photo_url for {airtable_id}: {e}")


def get_groomers():
    """Get groomers from Airtable or fall back to sample data."""
    groomers = fetch_from_airtable()
    if groomers is None:
        groomers = get_sample_data()
        print(f"Using {len(groomers)} sample groomers.")
    return groomers


def fetch_blog_posts():
    """Fetch published blog posts from Airtable."""
    if not config.AIRTABLE_API_KEY or not config.AIRTABLE_BASE_ID:
        return []

    try:
        from pyairtable import Api

        api = Api(config.AIRTABLE_API_KEY)
        table = api.table(config.AIRTABLE_BASE_ID, config.AIRTABLE_BLOG_TABLE_NAME)
        records = table.all()

        today = datetime.now().strftime("%Y-%m-%d")
        posts = []
        for record in records:
            fields = record.get("fields", {})

            if fields.get("Status") != "Published":
                continue

            # Skip posts with a future publish date
            publish_date = fields.get("Publish Date", "")
            if publish_date and publish_date > today:
                continue

            title = fields.get("Title", "")

            # Support both "Author Key" (config lookup) and direct "Author"/"Author Bio" fields
            author_key = fields.get("Author Key", "")
            if author_key and author_key in config.AUTHORS:
                author_info = config.AUTHORS[author_key]
                author_name = author_info["name"]
                author_credentials = author_info["credentials"]
                author_bio_text = author_info["bio"]
            else:
                # Use direct fields from Airtable
                author_name = fields.get("Author", "") or config.AUTHORS[config.DEFAULT_AUTHOR_KEY]["name"]
                author_bio_text = fields.get("Author Bio", "") or config.AUTHORS[config.DEFAULT_AUTHOR_KEY]["bio"]
                # Try to match author name back to a config key for credentials
                author_key = config.DEFAULT_AUTHOR_KEY
                for key, info in config.AUTHORS.items():
                    if info["name"].lower() == author_name.lower():
                        author_key = key
                        break
                author_credentials = config.AUTHORS.get(author_key, config.AUTHORS[config.DEFAULT_AUTHOR_KEY])["credentials"]

            post = {
                "title": title,
                "slug": (fields.get("Slug", "") or slugify(title)).strip(),
                "content": fields.get("Content", ""),
                "excerpt": fields.get("Excerpt", ""),
                "author": author_name,
                "author_key": author_key,
                "author_credentials": author_credentials,
                "author_bio": author_bio_text,
                "publish_date": fields.get("Publish Date", ""),
                "modified_date": fields.get("Modified Date", fields.get("Publish Date", "")),
                "featured_image": fields.get("Featured Image", ""),
                "meta_description": fields.get("Meta Description", ""),
                "status": fields.get("Status", "Published"),
                "featured": fields.get("Featured", False),
            }
            posts.append(post)

        posts.sort(key=lambda x: x.get("publish_date", ""), reverse=True)
        print(f"Fetched {len(posts)} blog posts from Airtable.")
        return posts

    except Exception as e:
        print(f"Note: Could not fetch blog posts ({e})")
        return []


def setup_output_directory():
    """Create clean output directory."""
    if config.OUTPUT_DIR.exists():
        shutil.rmtree(config.OUTPUT_DIR)

    config.OUTPUT_DIR.mkdir(parents=True)
    (config.OUTPUT_DIR / "state").mkdir()
    (config.OUTPUT_DIR / "groomer").mkdir()
    (config.OUTPUT_DIR / "category").mkdir()
    (config.OUTPUT_DIR / "blog").mkdir()

    # Copy static files
    if config.STATIC_DIR.exists():
        shutil.copytree(config.STATIC_DIR, config.OUTPUT_DIR / "static")


def create_jinja_env():
    """Create Jinja2 environment with custom filters."""
    env = Environment(
        loader=FileSystemLoader(config.TEMPLATES_DIR),
        autoescape=True
    )

    def format_date(date_str):
        if not date_str:
            return ""
        try:
            dt = datetime.strptime(str(date_str)[:10], "%Y-%m-%d")
            return dt.strftime("%B ") + str(dt.day) + dt.strftime(", %Y")
        except (ValueError, TypeError):
            return date_str

    env.filters["slugify"] = slugify
    env.filters["tojson"] = lambda v: json.dumps(v, ensure_ascii=False)
    env.filters["markdown"] = lambda text: Markup(md_lib.markdown(text or "", extensions=["extra", "nl2br"]))
    env.filters["format_date"] = format_date

    env.globals["site_name"] = config.SITE_NAME
    env.globals["site_url"] = config.SITE_URL
    env.globals["site_description"] = config.SITE_DESCRIPTION
    env.globals["categories"] = config.CATEGORIES
    env.globals["us_states"] = config.US_STATES
    env.globals["current_year"] = datetime.now().year
    env.globals["ga_measurement_id"] = config.GA_MEASUREMENT_ID
    env.globals["authors"] = config.AUTHORS

    return env


def group_by_state(groomers):
    """Group groomers by state slug."""
    grouped = {}
    for g in groomers:
        state_slug = g.get("state_slug", "")
        if state_slug:
            grouped.setdefault(state_slug, []).append(g)
    return grouped


def group_by_city(groomers):
    """Group groomers by (state_slug, city) for city pages."""
    grouped = defaultdict(list)
    for g in groomers:
        state_slug = g.get("state_slug", "")
        city = g.get("city", "").strip()
        if state_slug and city:
            city_slug = slugify(city)
            grouped[(state_slug, city, city_slug)].append(g)
    return grouped


def generate_dynamic_meta_description(page_type, context):
    """Generate unique meta description from actual page content — never formulaic.

    Must-have #1: Unique dynamic meta descriptions derived from editorial content.
    """
    if page_type == "groomer":
        name = str(context.get("name", "")).strip()
        city = str(context.get("city", "")).strip()
        state = str(context.get("state", "")).strip()
        desc = str(context.get("description", "")).strip()

        if desc and len(desc) >= 50:
            # Prepend business name to ensure uniqueness even if descriptions overlap
            prefix = f"{name} in {city}, {state}" if name and city else name
            candidate = f"{prefix} — {desc}" if prefix else desc
            return candidate[:155].rsplit(" ", 1)[0] + "..." if len(candidate) > 155 else candidate

        # Fallback: structured meta from business data
        if name and city and state:
            return f"{name} — dog grooming services in {city}, {state}. Browse hours, reviews, and contact info."
        return ""

    elif page_type == "state":
        state_desc = str(context.get("state_description", "")).strip()
        if state_desc:
            return state_desc[:155].rsplit(" ", 1)[0] + "..." if len(state_desc) > 155 else state_desc
        return ""

    elif page_type == "city":
        # Use editorial intro if available
        intro = str(context.get("city_intro", "")).strip()
        if intro and len(intro) >= 50:
            return intro[:155].rsplit(" ", 1)[0] + "..." if len(intro) > 155 else intro
        return ""

    elif page_type == "category":
        intro = str(context.get("intro", "")).strip()
        if intro:
            return intro[:155].rsplit(" ", 1)[0] + "..." if len(intro) > 155 else intro
        return ""

    elif page_type == "post":
        meta = str(context.get("meta_description", "")).strip()
        if meta:
            return meta[:155]
        excerpt = str(context.get("excerpt", "")).strip()
        if excerpt:
            return excerpt[:155].rsplit(" ", 1)[0] + "..." if len(excerpt) > 155 else excerpt
        return ""

    return ""


def load_gsc_protected_slugs():
    """Load groomer slugs that are currently earning Google traffic.

    These are grandfathered through description_quality_check so the new
    strict gate cannot regress any URL that's already ranking. Refresh by
    running scripts/extract_gsc_protected.py against a fresh GSC export.
    """
    path = config.BASE_DIR / "data" / "gsc_protected_urls.txt"
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    }


_GSC_PROTECTED = load_gsc_protected_slugs()


def description_quality_check(groomer):
    """Decide whether a groomer listing has enough genuine content to be indexed.

    Returns (passes, reason). Description is the primary gate — its length and
    content quality matter more than whether other data fields are populated.
    Hours/phone/services are demoted to secondary signals that can rescue a
    borderline listing.

    GSC-protected slugs (currently earning Google traffic) are grandfathered:
    they pass regardless of the new gate, so the rewrite cannot regress
    pages that are already ranking. After the 60-day window the protection
    list should be re-extracted from a fresh GSC report.
    """
    slug = (groomer.get("slug") or "").lower()
    if slug in _GSC_PROTECTED:
        return True, "gsc-protected"

    desc = str(groomer.get("description") or "").strip()
    desc_lower = desc.lower()

    if not desc or desc_lower == "nan":
        return False, "no description"
    if len(desc) < config.MIN_DESCRIPTION_LENGTH:
        return False, f"description too short ({len(desc)} < {config.MIN_DESCRIPTION_LENGTH})"
    for term in config.JUNK_DESCRIPTION_TERMS:
        if term in desc_lower:
            return False, f"junk pattern: {term!r}"
    if not any(v in desc_lower for v in config.GROOMING_VOCAB):
        return False, "no grooming vocabulary"

    # Description passed the primary gate. Require at least one additional
    # signal so we don't index a listing with rich text but no contact info.
    hours_ok = bool(str(groomer.get("hours") or "").strip()) and \
               str(groomer.get("hours") or "").strip().lower() != "nan"
    services = groomer.get("services") or []
    services_ok = isinstance(services, list) and len(services) > 0
    phone_ok = bool(str(groomer.get("phone") or "").strip())
    if not (hours_ok or services_ok or phone_ok):
        return False, "no contact/service signals"

    return True, "ok"


def is_thin_listing(groomer):
    """Backward-compatible wrapper around description_quality_check."""
    passes, _ = description_quality_check(groomer)
    return not passes


def build_homepage(env, groomers, posts):
    """Build the homepage."""
    template = env.get_template("index.html")

    featured = [g for g in groomers if g.get("featured")][:config.FEATURED_COUNT]
    if not featured:
        featured = groomers[:config.FEATURED_COUNT]

    recent = sorted(groomers, key=lambda x: x.get("date_added", ""), reverse=True)[:config.RECENT_COUNT]

    by_state = group_by_state(groomers)
    state_counts = {s: len(v) for s, v in by_state.items()}

    featured_post = next((p for p in posts if p.get("featured")), None)
    recent_posts = [p for p in posts if p is not featured_post][:3]

    html = template.render(
        featured_groomers=featured,
        recent_groomers=recent,
        all_groomers=groomers,
        state_counts=state_counts,
        total_count=len(groomers),
        posts=posts,
        featured_post=featured_post,
        recent_posts=recent_posts,
        page_title=config.DEFAULT_META_TITLE,
        meta_description=config.DEFAULT_META_DESCRIPTION,
        request_path="/",
    )

    output_path = config.OUTPUT_DIR / "index.html"
    output_path.write_text(html)
    print(f"Built: index.html ({len(groomers)} total groomers)")


def build_state_pages(env, groomers):
    """Build one page per US state."""
    template = env.get_template("state.html")
    grouped = group_by_state(groomers)

    for state in config.US_STATES:
        state_groomers = grouped.get(state["slug"], [])
        state_groomers.sort(key=lambda x: x.get("city", ""))

        thin_state = len(state_groomers) < config.MIN_STATE_LISTINGS_FOR_INDEX

        meta_desc = generate_dynamic_meta_description("state", {
            "state_description": state["description"],
        })

        html = template.render(
            state=state,
            groomers=state_groomers,
            page_title=f"Dog Groomers in {state['name']} - {config.SITE_NAME}",
            meta_description=meta_desc,
            request_path=f"/state/{state['slug']}",
            noindex=thin_state,
        )

        output_path = config.OUTPUT_DIR / "state" / f"{state['slug']}.html"
        output_path.write_text(html)
        print(f"Built: state/{state['slug']}.html ({len(state_groomers)} groomers)")


def build_city_pages(env, groomers):
    """Build city-level pages.

    Pages are still emitted for cities with >= 2 listings so internal links
    from groomer detail pages resolve. Cities below MIN_CITY_LISTINGS_FOR_INDEX
    are noindexed and excluded from the sitemap — this is the audit-D fix:
    the prior implementation injected a templated 30-word intro on every city
    page, producing 749 indexed near-duplicates that AdSense classifies as
    doorway pages. The intro is now removed entirely; per-city editorial can
    be added later via an Airtable field if real local content is written.
    """
    template = env.get_template("city.html")
    city_groups = group_by_city(groomers)

    city_count = 0
    indexed_count = 0
    for (state_slug, city, city_slug), city_groomers in sorted(city_groups.items()):
        if len(city_groomers) < 2:
            continue

        state_dir = config.OUTPUT_DIR / "state" / state_slug
        state_dir.mkdir(parents=True, exist_ok=True)

        state_name = city_groomers[0].get("state", "")
        thin_city = len(city_groomers) < config.MIN_CITY_LISTINGS_FOR_INDEX
        if not thin_city:
            indexed_count += 1

        # Factual meta description from listing count — no marketing boilerplate.
        listing_word = "groomer" if len(city_groomers) == 1 else "groomers"
        meta_desc = (
            f"{len(city_groomers)} dog {listing_word} in {city}, {state_name}. "
            f"View hours, services, and contact info."
        )

        state_info = next((s for s in config.US_STATES if s["slug"] == state_slug), None)

        html = template.render(
            city=city,
            city_slug=city_slug,
            state=state_info or {"name": state_name, "slug": state_slug},
            groomers=city_groomers,
            city_intro="",  # audit-D: no templated intro
            page_title=f"Dog Groomers in {city}, {state_name} - {config.SITE_NAME}",
            meta_description=meta_desc,
            request_path=f"/state/{state_slug}/{city_slug}",
            noindex=thin_city,
        )

        output_path = state_dir / f"{city_slug}.html"
        output_path.write_text(html)
        city_count += 1

    print(f"Built: {city_count} city pages ({indexed_count} indexed, {city_count - indexed_count} noindexed)")


def build_groomer_pages(env, groomers):
    """Build individual groomer detail pages."""
    template = env.get_template("groomer.html")
    noindex_count = 0

    for groomer in groomers:
        related = [g for g in groomers if g["slug"] != groomer["slug"]
                   and g.get("state_slug") == groomer.get("state_slug")][:4]

        thin = is_thin_listing(groomer)
        if thin:
            noindex_count += 1

        meta_desc = generate_dynamic_meta_description("groomer", {
            "description": groomer.get("description", ""),
            "name": groomer.get("name", ""),
            "city": groomer.get("city", ""),
            "state": groomer.get("state", ""),
        })

        html = template.render(
            groomer=groomer,
            related_groomers=related,
            page_title=f"{groomer['name']} - {groomer['city']}, {groomer['state']} - {config.SITE_NAME}",
            meta_description=meta_desc,
            request_path=f"/groomer/{groomer['slug']}",
            noindex=thin,
        )

        output_path = config.OUTPUT_DIR / "groomer" / f"{groomer['slug']}.html"
        output_path.write_text(html)

    print(f"Built: {len(groomers)} groomer pages ({noindex_count} noindexed as thin content)")


def build_category_pages(env, groomers):
    """Build service category pages."""
    template = env.get_template("category.html")

    category_filters = {
        "full-service": lambda g: g.get("type") in ["Full-Service Salon", "Full-Service Grooming"],
        "mobile-grooming": lambda g: g.get("type") == "Mobile Grooming" or "Mobile Grooming" in g.get("specialties", []),
        "breed-specific": lambda g: "Breed-Specific Styling" in g.get("specialties", []) or "Show Grooming" in g.get("specialties", []),
        "cat-grooming": lambda g: "Cat Grooming" in g.get("services", []) or "Cat Grooming" in g.get("specialties", []),
        "puppy-first-groom": lambda g: "Puppy First Groom" in g.get("services", []) or "Puppy First Groom" in g.get("specialties", []),
        "senior-special-needs": lambda g: "Senior Dogs" in g.get("specialties", []) or "Special Needs" in g.get("specialties", []),
        "self-service-wash": lambda g: "Self-Service Wash" in g.get("services", []) or g.get("type") == "Self-Service Dog Wash",
        "affordable": lambda g: g.get("price_range") in ["$", "$$"],
    }

    for category in config.CATEGORIES:
        filter_fn = category_filters.get(category["slug"], lambda g: True)
        category_groomers = [g for g in groomers if filter_fn(g)]

        state_counts = {}
        for g in category_groomers:
            s = g.get("state", "")
            if s:
                state_counts[s] = state_counts.get(s, 0) + 1
        state_list = sorted(state_counts.items(), key=lambda x: (-x[1], x[0]))

        meta_desc = generate_dynamic_meta_description("category", {"intro": category["intro"]})

        html = template.render(
            category=category,
            groomers=category_groomers,
            state_list=state_list,
            page_title=f"{category['name']} Dog Groomers - {config.SITE_NAME}",
            meta_description=meta_desc,
            request_path=f"/category/{category['slug']}",
        )

        output_path = config.OUTPUT_DIR / "category" / f"{category['slug']}.html"
        output_path.write_text(html)
        print(f"Built: category/{category['slug']}.html ({len(category_groomers)} groomers)")


def build_blog_page(env, posts):
    """Build the blog listing page."""
    template = env.get_template("blog.html")
    html = template.render(
        posts=posts,
        page_title=f"Blog - {config.SITE_NAME}",
        meta_description="Tips, guides, and expert advice on dog grooming, coat care, and finding the right groomer for your pet.",
        request_path="/blog",
    )
    output_path = config.OUTPUT_DIR / "blog.html"
    output_path.write_text(html)
    print(f"Built: blog.html ({len(posts)} posts)")


def build_post_pages(env, posts):
    """Build individual blog post pages with BlogPosting JSON-LD and author bios."""
    template = env.get_template("post.html")

    for post in posts:
        if not post.get("slug"):
            continue

        meta_desc = generate_dynamic_meta_description("post", {
            "meta_description": post.get("meta_description", ""),
            "excerpt": post.get("excerpt", ""),
        })

        html = template.render(
            post=post,
            all_posts=posts,
            page_title=f"{post['title']} - {config.SITE_NAME}",
            meta_description=meta_desc,
            request_path=f"/blog/{post['slug']}",
        )
        output_path = config.OUTPUT_DIR / "blog" / f"{post['slug']}.html"
        output_path.write_text(html)
        print(f"Built: blog/{post['slug']}.html")


def build_search_index(groomers):
    """Generate search-index.json for client-side search."""
    index = [
        {"name": g["name"], "city": g.get("city", ""), "state": g.get("state", ""), "slug": g["slug"]}
        for g in groomers if g.get("name") and g.get("slug")
    ]
    output_path = config.OUTPUT_DIR / "search-index.json"
    with open(output_path, "w") as f:
        json.dump(index, f, ensure_ascii=False)
    print(f"Built: search-index.json ({len(index)} groomers)")


def build_sitemap(groomers, posts, breeds=None):
    """Generate sitemap.xml with per-page lastmod dates.

    Must-have #8: Sitemap with actual lastmod dates, not just today's build date.
    """
    today = datetime.now().strftime("%Y-%m-%d")

    entries = [
        (f"{config.SITE_URL}/", "1.0", today),
        (f"{config.SITE_URL}/blog", "0.8", today),
        (f"{config.SITE_URL}/about", "0.5", today),
        (f"{config.SITE_URL}/contact", "0.4", today),
        (f"{config.SITE_URL}/disclaimer", "0.3", today),
        (f"{config.SITE_URL}/editorial-standards", "0.3", today),
        (f"{config.SITE_URL}/privacy", "0.3", today),
        (f"{config.SITE_URL}/terms", "0.3", today),
    ]

    if breeds:
        entries.append((f"{config.SITE_URL}/dog-grooming-guide", "0.8", today))

    grouped = group_by_state(groomers)
    for state in config.US_STATES:
        state_groomers = grouped.get(state["slug"], [])
        if len(state_groomers) >= config.MIN_STATE_LISTINGS_FOR_INDEX:
            # Use most recent listing modification date for state page lastmod
            state_lastmod = max(
                (g.get("last_modified", g.get("date_added", today)) or today for g in state_groomers),
                default=today,
            )
            entries.append((f"{config.SITE_URL}/state/{state['slug']}", "0.8", state_lastmod))

    # City pages — only include if above the noindex threshold. The page itself
    # is still served (so internal links work), but Google should not be told
    # about a noindexed URL via sitemap.
    city_groups = group_by_city(groomers)
    for (state_slug, city, city_slug), city_groomers in sorted(city_groups.items()):
        if len(city_groomers) >= config.MIN_CITY_LISTINGS_FOR_INDEX:
            city_lastmod = max(
                (g.get("last_modified", g.get("date_added", today)) or today for g in city_groomers),
                default=today,
            )
            entries.append((f"{config.SITE_URL}/state/{state_slug}/{city_slug}", "0.7", city_lastmod))

    for category in config.CATEGORIES:
        entries.append((f"{config.SITE_URL}/category/{category['slug']}", "0.7", today))

    for groomer in groomers:
        if not is_thin_listing(groomer):
            lastmod = groomer.get("last_modified", groomer.get("date_added", today)) or today
            entries.append((f"{config.SITE_URL}/groomer/{groomer['slug']}", "0.6", lastmod))

    for post in posts:
        if post.get("slug"):
            post_lastmod = post.get("modified_date", post.get("publish_date", today)) or today
            if post_lastmod > today:
                post_lastmod = today
            entries.append((f"{config.SITE_URL}/blog/{post['slug']}", "0.8", post_lastmod))

    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url, priority, lastmod in entries:
        sitemap += f"  <url><loc>{url}</loc><lastmod>{lastmod}</lastmod><priority>{priority}</priority></url>\n"
    sitemap += "</urlset>"

    output_path = config.OUTPUT_DIR / "sitemap.xml"
    output_path.write_text(sitemap)
    print("Built: sitemap.xml")


def build_robots():
    """Generate robots.txt."""
    robots = f"""User-agent: *
Allow: /

Sitemap: {config.SITE_URL}/sitemap.xml
"""
    output_path = config.OUTPUT_DIR / "robots.txt"
    output_path.write_text(robots)
    print("Built: robots.txt")


def build_netlify_redirects(groomers, posts, breeds=None):
    """Generate dist/_redirects with one literal 301 per .html page.

    Placeholder interpolation in Netlify redirects (both netlify.toml and
    _redirects file) was producing literal `:slug` strings instead of the
    captured value. Generating one explicit rule per page sidesteps the
    issue entirely. Netlify's documented limit is 100,000 rules per file;
    we're well under that.

    The trailing `!` is the force flag (redirect even if the file exists).
    """
    lines = [
        "# .html → extensionless 301 redirects (canonical URL cleanup)",
        "# Generated by build.py — do not edit by hand.",
        "",
        "# Static pages",
    ]

    static_pages = [
        "about", "contact", "privacy", "terms", "disclaimer",
        "editorial-standards", "submit", "blog", "newsletter",
    ]
    if breeds:
        static_pages.append("dog-grooming-guide")

    for name in static_pages:
        lines.append(f"/{name}.html  /{name}  301!")

    lines += ["", "# State pages"]
    for state in config.US_STATES:
        slug = state["slug"]
        lines.append(f"/state/{slug}.html  /state/{slug}  301!")

    lines += ["", "# City pages"]
    city_groups = group_by_city(groomers)
    for (state_slug, _city, city_slug), city_groomers in sorted(city_groups.items()):
        if len(city_groomers) >= 2:
            lines.append(
                f"/state/{state_slug}/{city_slug}.html  /state/{state_slug}/{city_slug}  301!"
            )

    lines += ["", "# Category pages"]
    for category in config.CATEGORIES:
        slug = category["slug"]
        lines.append(f"/category/{slug}.html  /category/{slug}  301!")

    lines += ["", "# Groomer pages"]
    for groomer in groomers:
        slug = groomer.get("slug")
        if slug:
            lines.append(f"/groomer/{slug}.html  /groomer/{slug}  301!")

    lines += ["", "# Blog posts"]
    for post in posts:
        slug = post.get("slug")
        if slug:
            lines.append(f"/blog/{slug}.html  /blog/{slug}  301!")

    output_path = config.OUTPUT_DIR / "_redirects"
    output_path.write_text("\n".join(lines) + "\n")
    print(f"Built: _redirects ({len(lines)} lines)")


def copy_ads_txt():
    """Copy ads.txt to output directory."""
    ads_txt_path = Path("ads.txt")
    if ads_txt_path.exists():
        shutil.copy(ads_txt_path, config.OUTPUT_DIR / "ads.txt")
        print("Built: ads.txt")


# Static pages
STATIC_PAGES = [
    {
        "template": "about.html",
        "output": "about.html",
        "title": "About Us",
        "description": "Learn about Dog Groomer Locator and our mission to help dog owners find trusted professional groomers.",
    },
    {
        "template": "privacy.html",
        "output": "privacy.html",
        "title": "Privacy Policy",
        "description": "Our privacy policy explains how we collect, use, and protect your information.",
    },
    {
        "template": "contact.html",
        "output": "contact.html",
        "title": "Contact Us",
        "description": "Get in touch with Dog Groomer Locator for questions, suggestions, or to submit a new listing.",
    },
    {
        "template": "terms.html",
        "output": "terms.html",
        "title": "Terms of Service",
        "description": "Terms and conditions for using Dog Groomer Locator.",
    },
    {
        "template": "success.html",
        "output": "success/index.html",
        "title": "Message Sent",
        "description": "Thank you for contacting us.",
    },
    {
        "template": "submit.html",
        "output": "submit.html",
        "title": "Submit a Dog Groomer",
        "description": "Submit a dog groomer or grooming salon to be added to our directory.",
    },
    {
        "template": "disclaimer.html",
        "output": "disclaimer.html",
        "title": "Disclaimer",
        "description": "Important disclaimers about the information provided on Dog Groomer Locator.",
    },
    {
        "template": "editorial-standards.html",
        "output": "editorial-standards.html",
        "title": "Editorial Standards",
        "description": "How we research, verify, and maintain the quality of information on Dog Groomer Locator.",
    },
]


def build_static_pages(env, groomers=None):
    """Build static informational pages."""
    total_count = len(groomers) if groomers else 0
    for page in STATIC_PAGES:
        template = env.get_template(page["template"])
        # Canonical path is extensionless (e.g. /about instead of /about.html).
        # success/index.html → /success/ for the canonical.
        output = page["output"]
        if output.endswith("/index.html"):
            canonical_path = "/" + output[: -len("index.html")]
        elif output.endswith(".html"):
            canonical_path = "/" + output[: -len(".html")]
        else:
            canonical_path = "/" + output
        html = template.render(
            page_title=f"{page['title']} - {config.SITE_NAME}",
            meta_description=page["description"],
            request_path=canonical_path,
            total_count=total_count,
        )
        output_path = config.OUTPUT_DIR / page["output"]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html)
        print(f"Built: {page['output']}")


def build_newsletter_pages(env):
    """Build newsletter landing page, archive page, and sample issue."""
    output_dir = config.OUTPUT_DIR / "newsletter"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Newsletter landing page (/newsletter/index.html)
    template = env.get_template("newsletter.html")
    html = template.render(
        page_title=f"Newsletter - {config.SITE_NAME}",
        meta_description="Subscribe to the Dog Groomer Locator newsletter for monthly grooming tips, new listings, and seasonal coat care guides.",
        request_path="/newsletter",
    )
    (output_dir / "index.html").write_text(html)
    print("Built: newsletter/index.html")

    # Newsletter archive page (/newsletter/archive.html)
    template = env.get_template("newsletter-archive.html")
    html = template.render(
        page_title=f"Newsletter Archive - {config.SITE_NAME}",
        meta_description="Browse past issues of the Dog Groomer Locator newsletter.",
        request_path="/newsletter/archive",
    )
    (output_dir / "archive.html").write_text(html)
    print("Built: newsletter/archive.html")

    # Newsletter sample issue (/newsletter/sample.html)
    draft_path = Path("newsletter/issue-01-draft.md")
    if not draft_path.exists():
        print("Skipped: newsletter/sample (draft not found)")
    else:
        raw_md = draft_path.read_text(encoding="utf-8")
        # Strip the HTML comment metadata block at the top
        if raw_md.startswith("<!--"):
            end = raw_md.find("-->")
            if end != -1:
                raw_md = raw_md[end + 3:].lstrip("\n")

        newsletter_html = Markup(md_lib.markdown(raw_md, extensions=["extra", "nl2br"]))

        template = env.get_template("newsletter-sample.html")
        html = template.render(
            page_title=f"Newsletter Issue #1 Preview - {config.SITE_NAME}",
            meta_description="Preview of the Dog Groomer Locator newsletter — grooming tips, new listings, and seasonal guides.",
            request_path="/newsletter/sample",
            noindex=True,
            newsletter_html=newsletter_html,
        )
        (output_dir / "sample.html").write_text(html)
        print("Built: newsletter/sample.html")

    # Copy newsletter assets (logo, images) to output
    logo_path = Path("newsletter/NewsletterLogo.png")
    if logo_path.exists():
        shutil.copy(logo_path, output_dir / "NewsletterLogo.png")

    images_dir = Path("newsletter/images")
    if images_dir.is_dir():
        dest_images = output_dir / "images"
        dest_images.mkdir(parents=True, exist_ok=True)
        for img in images_dir.iterdir():
            if img.is_file():
                shutil.copy(img, dest_images / img.name)


def load_breed_guide():
    """Load breed grooming guide data from xlsx, falling back to JSON for CI/Netlify."""
    import json as _json
    xlsx_path = config.DATA_DIR / "dog_grooming_master.xlsx"
    json_path = config.DATA_DIR / "breed_grooming_guide.json"
    if not xlsx_path.exists():
        if json_path.exists():
            with open(json_path) as f:
                breeds = _json.load(f)
            breeds.sort(key=lambda b: b.get("name", ""))
            print(f"Loaded {len(breeds)} breeds from breed_grooming_guide.json (xlsx not found).")
            return breeds
        print("  Breed guide data not found, skipping.")
        return []

    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    wb.close()

    if len(rows) < 2:
        return []

    breeds = []
    for row in rows[1:]:
        breed = {
            "name": (row[0] or "").strip(),
            "coat_type": (row[1] or "").strip(),
            "shedding_level": (row[2] or "").strip(),
            "grooming_frequency": (row[3] or "").strip(),
            "best_grooming": (row[4] or "").strip(),
            "why": (row[5] or "").strip(),
            "special_care": (row[6] or "").strip(),
            "professional_grooming": (row[7] or "").strip(),
            "bathing_frequency": (row[8] or "").strip(),
            "hypoallergenic": (row[9] or "").strip(),
        }
        if breed["name"]:
            breeds.append(breed)

    breeds.sort(key=lambda b: b["name"])
    print(f"Loaded {len(breeds)} breeds from grooming guide.")
    return breeds


def build_breed_guide(env, breeds):
    """Build the breed grooming guide page."""
    if not breeds:
        print("Skipped: breed guide (no data)")
        return

    template = env.get_template("breed-guide.html")

    # Group by coat type and shedding level for the template
    coat_types = sorted(set(b["coat_type"] for b in breeds))
    shedding_levels = sorted(set(b["shedding_level"] for b in breeds if b["shedding_level"]))

    html = template.render(
        breeds=breeds,
        coat_types=coat_types,
        shedding_levels=shedding_levels,
        page_title=f"Dog Breed Grooming Guide - {config.SITE_NAME}",
        meta_description=f"Complete grooming guide for {len(breeds)} dog breeds organized by coat type. Learn grooming routines, shedding levels, bathing frequency, and special care needs for every coat type.",
        request_path="/dog-grooming-guide",
    )

    output_path = config.OUTPUT_DIR / "dog-grooming-guide.html"
    output_path.write_text(html)
    print(f"Built: dog-grooming-guide.html ({len(breeds)} breeds)")


def download_groomer_images(groomers):
    """Download external photo URLs locally to avoid Google Places URL expiry."""
    images_dir = config.OUTPUT_DIR / "static" / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    source_images_dir = config.STATIC_DIR / "images"
    source_images_dir.mkdir(parents=True, exist_ok=True)

    downloaded = 0
    skipped = 0
    failed = 0

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/",
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    for groomer in groomers:
        url = groomer.get("photo_url", "").strip()
        slug = groomer.get("slug", "").strip()

        if not url or not slug:
            skipped += 1
            continue

        if url.startswith("/static/"):
            skipped += 1
            continue

        local_path = images_dir / f"{slug}.jpg"

        if local_path.exists():
            groomer["photo_url"] = f"/static/images/{slug}.jpg"
            skipped += 1
            continue

        try:
            response = requests.get(url, headers=headers, timeout=15, stream=True)
            if response.status_code == 200:
                with open(local_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                source_path = source_images_dir / f"{slug}.jpg"
                if not source_path.exists():
                    shutil.copy2(local_path, source_path)
                groomer["photo_url"] = f"/static/images/{slug}.jpg"
                downloaded += 1
            else:
                print(f"  Image {response.status_code}: {groomer.get('name', slug)} — clearing photo_url in Airtable")
                groomer["photo_url"] = ""
                clear_airtable_photo_url(groomer.get("_airtable_id", ""))
                failed += 1
        except Exception as e:
            print(f"  Image error for {groomer.get('name', slug)}: {e} — clearing photo_url")
            groomer["photo_url"] = ""
            failed += 1

    print(f"Images: {downloaded} downloaded, {skipped} skipped/cached, {failed} failed")


def validate_build(groomers):
    """Build-time content validation — warn on data quality issues."""
    warnings = 0

    # Check for duplicate meta descriptions (using generated meta descriptions)
    descriptions = {}
    for g in groomers:
        meta_desc = generate_dynamic_meta_description("groomer", {
            "description": g.get("description", ""),
            "name": g.get("name", ""),
            "city": g.get("city", ""),
            "state": g.get("state", ""),
        })
        if meta_desc and meta_desc in descriptions:
            print(f"  WARNING: Duplicate meta description between '{g['name']}' and '{descriptions[meta_desc]}'")
            warnings += 1
        elif meta_desc:
            descriptions[meta_desc] = g["name"]

    # Check for thin descriptions
    thin_count = sum(1 for g in groomers if len(str(g.get("description", "")).strip()) < config.MIN_DESCRIPTION_LENGTH)
    if thin_count:
        print(f"  WARNING: {thin_count} groomers have descriptions under {config.MIN_DESCRIPTION_LENGTH} chars")

    # Check for duplicate slugs
    slugs = {}
    for g in groomers:
        s = g.get("slug", "")
        if s in slugs:
            print(f"  WARNING: Duplicate slug '{s}' between '{g['name']}' and '{slugs[s]}'")
            warnings += 1
        else:
            slugs[s] = g["name"]

    if warnings == 0:
        print("  Content validation passed — no issues found.")
    else:
        print(f"  Content validation completed with {warnings} warning(s).")


def main():
    """Main build process."""
    print(f"\n{'='*50}")
    print(f"Building {config.SITE_NAME}")
    print(f"{'='*50}\n")

    print("Setting up output directory...")
    setup_output_directory()

    print("\nFetching groomers...")
    groomers = get_groomers()

    print("\nDownloading groomer images...")
    download_groomer_images(groomers)

    print("\nValidating content...")
    validate_build(groomers)

    print("\nFetching blog posts...")
    posts = fetch_blog_posts()

    print("\nLoading breed guide...")
    breeds = load_breed_guide()

    env = create_jinja_env()

    print("\nBuilding pages...")
    build_homepage(env, groomers, posts)
    build_state_pages(env, groomers)
    build_city_pages(env, groomers)
    build_groomer_pages(env, groomers)
    build_category_pages(env, groomers)
    build_static_pages(env, groomers)
    build_blog_page(env, posts)
    build_post_pages(env, posts)
    build_newsletter_pages(env)
    build_breed_guide(env, breeds)

    print("\nBuilding SEO files...")
    build_sitemap(groomers, posts, breeds)
    build_robots()
    build_netlify_redirects(groomers, posts, breeds)
    copy_ads_txt()
    build_search_index(groomers)

    print(f"\n{'='*50}")
    print(f"Build complete! Output in: {config.OUTPUT_DIR}")
    print(f"{'='*50}")
    print(f"\nTo preview locally:")
    print(f"  cd {config.OUTPUT_DIR}")
    print(f"  python3 -m http.server 8000")
    print(f"  Open http://localhost:8000")


if __name__ == "__main__":
    main()
