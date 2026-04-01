"""
Configuration for Dog Groomer Locator Directory
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "dist"

# Site Configuration
SITE_NAME = "Dog Groomer Locator"
SITE_DESCRIPTION = "Find trusted dog groomers near you. Browse ratings, services, prices, and reviews for professional pet grooming across America."
SITE_URL = os.getenv("SITE_URL", "https://doggroomerlocator.com")
SITE_AUTHOR = "Dog Groomer Locator"

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "Groomers")
AIRTABLE_BLOG_TABLE_NAME = os.getenv("AIRTABLE_BLOG_TABLE_NAME", "Blog Posts")

# Noindex Thresholds
MIN_LISTINGS_FOR_INDEX = 3  # State/city pages with fewer listings get noindex
MIN_DESCRIPTION_LENGTH = 100  # Listing description minimum chars for indexing

# Authors — E-E-A-T: each blog post must have a credited author with credentials
AUTHORS = {
    "sarah-mitchell": {
        "name": "Sarah Mitchell",
        "credentials": "Certified Master Groomer (CMG), International Professional Groomers Inc.",
        "bio": "Sarah Mitchell is a Certified Master Groomer with over 15 years of experience in professional pet grooming. She has worked with all breeds from toy poodles to giant schnauzers and specializes in breed-specific styling and coat health. Sarah writes about grooming techniques, coat care, and choosing the right groomer for your dog.",
        "headshot": "",
    },
    "dog-groomer-locator-staff": {
        "name": "Dog Groomer Locator Staff",
        "credentials": "Pet care research team",
        "bio": "The Dog Groomer Locator editorial team researches and verifies grooming businesses across the United States, helping dog owners find trusted local groomers with transparent pricing, honest reviews, and professional credentials.",
        "headshot": "",
    },
}
DEFAULT_AUTHOR_KEY = "sarah-mitchell"

# US States for state-based pages
US_STATES = [
    {"name": "Alabama", "slug": "alabama", "abbr": "AL",
     "description": "Alabama's warm, humid climate means dogs need regular grooming year-round. The state's mix of hunting dogs, family pets, and show breeds supports a strong network of professional groomers from Birmingham and Huntsville to Mobile and Montgomery. Many Alabama groomers specialize in double-coated breeds that need extra attention during the long shedding season."},
    {"name": "Alaska", "slug": "alaska", "abbr": "AK",
     "description": "Alaska's extreme weather and outdoor lifestyle create unique grooming needs. Dogs here often have thick double coats built for cold, which require professional deshedding and undercoat maintenance. Groomers in Anchorage, Fairbanks, and Juneau are experienced with breeds like Huskies, Malamutes, and other cold-weather working dogs."},
    {"name": "Arizona", "slug": "arizona", "abbr": "AZ",
     "description": "Arizona's dry desert heat means dogs need specialized coat care to stay cool and comfortable. Phoenix, Scottsdale, Tucson, and Mesa have a thriving pet grooming industry with many groomers offering summer clips, paw pad treatments for hot pavement, and hydration-focused grooming for desert dogs."},
    {"name": "Arkansas", "slug": "arkansas", "abbr": "AR",
     "description": "Arkansas dog owners benefit from a growing community of professional groomers across the Natural State. From Little Rock to Fayetteville and the Ozark region, groomers handle everything from family pets to hunting dogs that need post-field cleaning and tick treatments."},
    {"name": "California", "slug": "california", "abbr": "CA",
     "description": "California has one of the largest and most diverse pet grooming industries in the country. From luxury mobile groomers in Los Angeles and San Francisco to neighborhood salons in Sacramento and San Diego, California offers every grooming style and specialty imaginable. The state's year-round mild climate and high pet ownership rate support thousands of professional grooming businesses."},
    {"name": "Colorado", "slug": "colorado", "abbr": "CO",
     "description": "Colorado's active outdoor lifestyle means dogs are frequently on trails, in snow, and in water — all of which demand regular professional grooming. Denver, Colorado Springs, Fort Collins, and Boulder have strong grooming communities, with many groomers experienced in managing thick coats, mud, and the dry mountain air that can cause skin issues."},
    {"name": "Connecticut", "slug": "connecticut", "abbr": "CT",
     "description": "Connecticut's pet owners have access to a dense network of professional groomers, from full-service salons to mobile grooming vans that serve suburban neighborhoods across the state. The seasonal climate means groomers handle everything from winter coat maintenance to summer trimming."},
    {"name": "Delaware", "slug": "delaware", "abbr": "DE",
     "description": "Delaware may be small, but its pet grooming community serves dog owners from Wilmington to the beach towns of Rehoboth and Lewes. The mid-Atlantic climate creates year-round grooming needs, and many Delaware groomers offer full-service packages including baths, clips, nail trimming, and dental care."},
    {"name": "Florida", "slug": "florida", "abbr": "FL",
     "description": "Florida's year-round warmth and one of the highest pet ownership rates in the nation make it a hub for professional dog grooming. Miami, Tampa, Orlando, Jacksonville, and hundreds of smaller communities support a vast network of grooming salons, mobile groomers, and specialty shops. Florida groomers are experts in managing humidity-related coat issues, flea prevention, and keeping dogs comfortable in subtropical heat."},
    {"name": "Georgia", "slug": "georgia", "abbr": "GA",
     "description": "Georgia's warm, humid climate keeps dogs and their groomers busy year-round. The Atlanta metro area has a particularly strong grooming industry, while Savannah, Augusta, and smaller cities throughout the Peach State offer professional grooming for every breed and budget."},
    {"name": "Hawaii", "slug": "hawaii", "abbr": "HI",
     "description": "Hawaii's tropical climate and island lifestyle create unique grooming needs, from managing humidity and salt air exposure to breed-specific tropical coat care. Professional groomers on Oahu, Maui, and the Big Island cater to a community that takes pet care seriously."},
    {"name": "Idaho", "slug": "idaho", "abbr": "ID",
     "description": "Idaho's outdoor-loving dog owners rely on professional groomers to maintain their pets through the state's varied seasons. Boise, Meridian, and other communities along the Treasure Valley have a growing network of grooming salons and mobile services."},
    {"name": "Illinois", "slug": "illinois", "abbr": "IL",
     "description": "Illinois has a robust pet grooming industry anchored by the Chicago metro area, one of the most dog-friendly cities in America. From downtown grooming salons to suburban mobile services and downstate family operations, Illinois groomers handle the state's harsh winters and humid summers with expertise across all breeds."},
    {"name": "Indiana", "slug": "indiana", "abbr": "IN",
     "description": "Indiana's pet grooming community serves dog owners from Indianapolis to Fort Wayne, South Bend, and communities across the state. The Midwest's four distinct seasons create year-round demand for professional coat care, deshedding, and seasonal grooming."},
    {"name": "Iowa", "slug": "iowa", "abbr": "IA",
     "description": "Iowa's dog owners value the personal service of local groomers who know their pets by name. Des Moines, Cedar Rapids, and communities statewide offer professional grooming that handles everything from farm dogs to family companions, with seasonal expertise for Iowa's cold winters and warm summers."},
    {"name": "Kansas", "slug": "kansas", "abbr": "KS",
     "description": "Kansas groomers serve the state's diverse pet population from Wichita, Kansas City suburbs, Topeka, and smaller communities across the plains. The state's windy, variable climate creates regular demand for coat maintenance and skin care year-round."},
    {"name": "Kentucky", "slug": "kentucky", "abbr": "KY",
     "description": "Kentucky's pet grooming industry spans from Louisville and Lexington to smaller Bluegrass communities. The state's moderate climate with four seasons ensures year-round grooming needs, and many Kentucky groomers specialize in both companion breeds and hunting dogs."},
    {"name": "Louisiana", "slug": "louisiana", "abbr": "LA",
     "description": "Louisiana's hot, humid climate creates year-round grooming demand. Baton Rouge, New Orleans, Lafayette, and Shreveport have strong grooming communities that specialize in managing moisture-related coat and skin issues, flea prevention, and keeping dogs comfortable in the Gulf Coast heat."},
    {"name": "Maine", "slug": "maine", "abbr": "ME",
     "description": "Maine's cold winters and outdoor lifestyle mean dogs need regular professional grooming to maintain healthy coats. Groomers across the Pine Tree State are experienced with thick-coated breeds and the challenges of winter ice, salt, and mud on paws and fur."},
    {"name": "Maryland", "slug": "maryland", "abbr": "MD",
     "description": "Maryland's pet grooming industry serves the densely populated Baltimore-Washington corridor and communities statewide. From upscale salons in Bethesda and Annapolis to neighborhood shops across the state, Maryland groomers handle the mid-Atlantic's humidity and seasonal transitions with expertise."},
    {"name": "Massachusetts", "slug": "massachusetts", "abbr": "MA",
     "description": "Massachusetts has a thriving pet grooming industry driven by the Boston metro area's high pet ownership rate. Groomers across the Commonwealth handle New England's harsh winters and humid summers, offering everything from breed-specific styling to low-stress grooming for anxious dogs."},
    {"name": "Michigan", "slug": "michigan", "abbr": "MI",
     "description": "Michigan's four seasons and Great Lakes climate create steady demand for professional dog grooming. Detroit, Grand Rapids, Ann Arbor, and communities across both peninsulas offer grooming services that handle everything from winter coat buildup to summer shave-downs."},
    {"name": "Minnesota", "slug": "minnesota", "abbr": "MN",
     "description": "Minnesota's extreme winters and active summers make regular grooming essential. Minneapolis-St. Paul has one of the strongest pet care industries in the Midwest, with groomers experienced in managing thick winter coats, spring deshedding, and the mud that comes with Minnesota's outdoor lifestyle."},
    {"name": "Mississippi", "slug": "mississippi", "abbr": "MS",
     "description": "Mississippi's warm, humid climate creates year-round grooming needs for dogs of all breeds. Professional groomers from Jackson to the Gulf Coast specialize in managing the skin and coat challenges that come with Southern heat and humidity."},
    {"name": "Missouri", "slug": "missouri", "abbr": "MO",
     "description": "Missouri's pet grooming community serves dog owners from the Kansas City and St. Louis metros to smaller communities across the Show-Me State. The state's variable climate — hot, humid summers and cold winters — keeps groomers busy with seasonal coat management year-round."},
    {"name": "Montana", "slug": "montana", "abbr": "MT",
     "description": "Montana's rugged outdoor lifestyle means dogs often need professional grooming to manage thick coats, trail debris, and the state's dry mountain air. Groomers in Billings, Missoula, and Great Falls serve a community that values both working dogs and family pets."},
    {"name": "Nebraska", "slug": "nebraska", "abbr": "NE",
     "description": "Nebraska's professional groomers serve dog owners from Omaha and Lincoln to communities across the state. The Great Plains climate with its cold winters and warm summers creates consistent demand for coat care, deshedding, and seasonal grooming services."},
    {"name": "Nevada", "slug": "nevada", "abbr": "NV",
     "description": "Nevada's desert climate creates unique grooming challenges, from dry skin and static to paw protection on hot surfaces. Las Vegas, Henderson, Reno, and surrounding communities have a strong grooming industry that understands desert dog care and the importance of hydrating treatments."},
    {"name": "New Hampshire", "slug": "new-hampshire", "abbr": "NH",
     "description": "New Hampshire's outdoor recreation culture and cold New England winters drive demand for professional grooming. Groomers across the Granite State manage thick winter coats, spring blowouts, and the mud and debris that come with trail-loving dogs."},
    {"name": "New Jersey", "slug": "new-jersey", "abbr": "NJ",
     "description": "New Jersey's dense population and high pet ownership rate support one of the most competitive grooming markets on the East Coast. From North Jersey suburbs to Shore communities and everything in between, dog owners have access to professional groomers offering every service from basic baths to show-quality styling."},
    {"name": "New Mexico", "slug": "new-mexico", "abbr": "NM",
     "description": "New Mexico's arid climate and altitude create specific grooming needs, including dry skin management and UV protection for dogs with light-colored coats. Albuquerque, Santa Fe, and Las Cruces have professional groomers experienced with desert dog care."},
    {"name": "New York", "slug": "new-york", "abbr": "NY",
     "description": "New York State has one of the largest pet grooming industries in the country. New York City alone supports thousands of groomers, from luxury Manhattan salons to neighborhood Brooklyn and Queens shops. Upstate communities, Long Island, and the Hudson Valley add depth to a state where dog grooming is both a necessity and a culture."},
    {"name": "North Carolina", "slug": "north-carolina", "abbr": "NC",
     "description": "North Carolina's growing population and strong pet culture support a thriving grooming industry. Charlotte, Raleigh-Durham, Greensboro, and Asheville lead with professional grooming salons and mobile services, while smaller communities across the state offer local grooming for every breed and budget."},
    {"name": "North Dakota", "slug": "north-dakota", "abbr": "ND",
     "description": "North Dakota's harsh winters and short summers make professional grooming essential for managing thick winter coats and spring shedding. Fargo, Bismarck, and communities statewide offer reliable grooming services for the state's dog owners."},
    {"name": "Ohio", "slug": "ohio", "abbr": "OH",
     "description": "Ohio has a deep and established pet grooming industry across its major metros and smaller communities. Columbus, Cleveland, Cincinnati, and Dayton each have strong grooming networks, and Ohio's four-season climate means dogs need regular professional coat maintenance year-round."},
    {"name": "Oklahoma", "slug": "oklahoma", "abbr": "OK",
     "description": "Oklahoma's hot summers and variable weather create year-round grooming demand. Oklahoma City, Tulsa, and communities across the Sooner State have professional groomers experienced with heat management, seasonal shedding, and the state's outdoor-active dog population."},
    {"name": "Oregon", "slug": "oregon", "abbr": "OR",
     "description": "Oregon's famously wet climate means dogs need regular grooming to manage damp coats and prevent skin issues. Portland leads the state's pet-friendly culture with a wide range of grooming options, while Salem, Eugene, and Bend offer strong local grooming communities."},
    {"name": "Pennsylvania", "slug": "pennsylvania", "abbr": "PA",
     "description": "Pennsylvania's pet grooming industry stretches from Philadelphia's urban salons to Pittsburgh's neighborhood shops and every community in between. The state's four seasons ensure consistent grooming demand, and Pennsylvania groomers handle everything from winter coat care to summer cooling clips."},
    {"name": "Rhode Island", "slug": "rhode-island", "abbr": "RI",
     "description": "Rhode Island's compact geography and high pet ownership rate mean dog owners are never far from a professional groomer. The state's coastal climate and New England seasons create regular demand for grooming services year-round."},
    {"name": "South Carolina", "slug": "south-carolina", "abbr": "SC",
     "description": "South Carolina's warm climate and growing population support a vibrant pet grooming industry. Charleston, Columbia, Greenville, and Myrtle Beach all have strong grooming communities, with many specialists in managing the heat and humidity that affect dogs' coats and skin."},
    {"name": "South Dakota", "slug": "south-dakota", "abbr": "SD",
     "description": "South Dakota's professional groomers serve dog owners from Sioux Falls and Rapid City to smaller communities across the state. The Great Plains climate's seasonal extremes make regular grooming important for coat health and comfort."},
    {"name": "Tennessee", "slug": "tennessee", "abbr": "TN",
     "description": "Tennessee's pet grooming industry spans from Nashville and Memphis to Knoxville, Chattanooga, and communities across the Volunteer State. The state's warm, humid climate creates year-round demand for professional grooming, and Tennessee groomers are skilled at managing everything from double-coated breeds to low-maintenance short-hair dogs."},
    {"name": "Texas", "slug": "texas", "abbr": "TX",
     "description": "Texas has one of the largest pet grooming markets in the country. Houston, Dallas-Fort Worth, San Antonio, Austin, and El Paso anchor a statewide network of grooming salons, mobile services, and specialty shops. The Lone Star State's intense heat makes regular grooming essential for dog comfort and health, and many Texas groomers specialize in summer cuts and heat management."},
    {"name": "Utah", "slug": "utah", "abbr": "UT",
     "description": "Utah's outdoor lifestyle and dry climate create steady demand for professional dog grooming. Salt Lake City, Provo, and communities along the Wasatch Front have a growing grooming industry that handles everything from trail-dirty adventure dogs to show-quality breed styling."},
    {"name": "Vermont", "slug": "vermont", "abbr": "VT",
     "description": "Vermont's rural character and cold winters make professional grooming especially important for coat maintenance. Groomers across the Green Mountain State handle the challenges of thick winter coats, spring mud season, and the outdoor lifestyle that Vermont dogs enjoy."},
    {"name": "Virginia", "slug": "virginia", "abbr": "VA",
     "description": "Virginia's pet grooming industry serves a large population of dog owners from Northern Virginia's DC suburbs to Hampton Roads, Richmond, and communities across the Commonwealth. The state's four seasons and humid summers create consistent demand for professional coat care and grooming services."},
    {"name": "Washington", "slug": "washington", "abbr": "WA",
     "description": "Washington's rainy Pacific Northwest climate makes regular grooming essential for managing damp coats and preventing skin problems. Seattle, Tacoma, Spokane, and communities statewide have a strong grooming industry that reflects the state's deep love of dogs and outdoor living."},
    {"name": "West Virginia", "slug": "west-virginia", "abbr": "WV",
     "description": "West Virginia's mountain communities and rural areas are served by dedicated professional groomers who handle the state's seasonal climate. From Charleston to smaller towns across the Mountain State, dog owners have access to grooming services that manage everything from winter coats to summer ticks."},
    {"name": "Wisconsin", "slug": "wisconsin", "abbr": "WI",
     "description": "Wisconsin's cold winters and warm summers create strong year-round demand for professional dog grooming. Milwaukee, Madison, Green Bay, and communities statewide offer grooming services that handle thick winter coat maintenance, spring deshedding, and summer cooling clips."},
    {"name": "Wyoming", "slug": "wyoming", "abbr": "WY",
     "description": "Wyoming's rugged climate and outdoor lifestyle mean dogs need regular professional grooming. While the state's population is smaller, communities like Cheyenne and Casper have dedicated groomers experienced with working dogs, ranch dogs, and family pets that brave Wyoming's winters."},
]

# Service categories (replaces splash pad feature filters)
CATEGORIES = [
    {"name": "Full-Service Grooming", "slug": "full-service", "icon": "✂️",
     "description": "Full-service groomers offering bath, cut, dry, nails, and styling",
     "intro": "Full-service dog groomers handle every aspect of your dog's grooming needs in a single appointment. A typical full-service session includes a bath with breed-appropriate shampoo, blow-dry, haircut or trim, nail clipping, ear cleaning, and sometimes teeth brushing. These groomers are trained to handle all breeds and coat types, from poodle show cuts to golden retriever deshedding. Full-service grooming is the most popular option for dog owners who want a one-stop professional experience."},
    {"name": "Mobile Grooming", "slug": "mobile-grooming", "icon": "🚐",
     "description": "Mobile groomers that come to your home in a fully equipped van",
     "intro": "Mobile dog groomers bring the salon to your doorstep in a fully equipped grooming van. This option is ideal for dogs that get anxious in grooming salons, elderly dogs that struggle with car rides, owners with multiple dogs, or anyone who values the convenience of at-home service. Mobile groomers typically offer the same full-service experience as brick-and-mortar salons — bath, cut, nails, ears — without the stress of a new environment for your pet."},
    {"name": "Breed-Specific Styling", "slug": "breed-specific", "icon": "🏆",
     "description": "Groomers specializing in breed-standard cuts and show grooming",
     "intro": "Breed-specific grooming goes beyond a basic haircut — these groomers are trained in the specific cut patterns, coat textures, and styling standards for individual breeds. Whether you need a proper poodle continental clip, a Schnauzer hand-strip, a Bichon round head, or a Cocker Spaniel skirt trim, breed-specific groomers deliver results that respect your dog's breed heritage. Many of these groomers have show ring experience and certifications."},
    {"name": "Cat Grooming Too", "slug": "cat-grooming", "icon": "🐱",
     "description": "Grooming shops that also handle cats and other pets",
     "intro": "Some grooming businesses specialize in more than just dogs — they also groom cats and occasionally other small pets. Cat grooming requires different handling techniques, specialized equipment, and patience for feline temperaments. If you have both dogs and cats, finding a groomer who handles both can simplify your pet care routine. These groomers are trained in feline coat types, lion cuts, and the unique needs of cat skin and fur."},
    {"name": "Puppy First Groom", "slug": "puppy-first-groom", "icon": "🐶",
     "description": "Groomers experienced with puppy introductions and first-time grooming",
     "intro": "A puppy's first grooming experience sets the tone for a lifetime of grooming visits. Groomers who specialize in puppy introductions use gentle handling, positive reinforcement, and shorter sessions to make the experience stress-free. They introduce puppies gradually to the sounds of clippers, the feel of water, and the grooming table. Starting with a skilled puppy groomer helps prevent grooming anxiety that can last years."},
    {"name": "Senior & Special Needs", "slug": "senior-special-needs", "icon": "🩺",
     "description": "Groomers experienced with elderly dogs and dogs with health conditions",
     "intro": "Senior dogs and dogs with special needs require extra care and patience during grooming. These groomers are experienced with arthritis accommodations, skin sensitivities, mobility challenges, and the gentle handling that older or health-compromised dogs need. They may offer padded tables, shorter sessions, breaks during grooming, and communication with your vet about skin conditions or medication that affects coat health."},
    {"name": "Self-Service Dog Wash", "slug": "self-service-wash", "icon": "🛁",
     "description": "Facilities where you wash your own dog using professional equipment",
     "intro": "Self-service dog wash stations give you access to professional grooming equipment — elevated tubs, warm water, professional shampoo, high-velocity dryers — without the mess at home. These are perfect for owners who enjoy bathing their own dog but don't want to deal with clogged drains and wet bathrooms. Most self-service facilities charge by the session and provide all the supplies you need."},
    {"name": "Affordable Grooming", "slug": "affordable", "icon": "💰",
     "description": "Budget-friendly groomers with transparent pricing",
     "intro": "Professional dog grooming doesn't have to break the bank. These groomers offer competitive pricing with transparent rates — no surprise upcharges for matting, size, or breed. Many offer package deals, loyalty discounts, or bath-only options for owners on a budget. Affordable doesn't mean low quality — these are professional groomers who keep their prices accessible so every dog can be well-groomed."},
]

# Google Analytics
GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "G-GLHVWDC9HQ")

# SEO Settings
DEFAULT_META_TITLE = f"{SITE_NAME} - Find Dog Groomers Near You"
DEFAULT_META_DESCRIPTION = SITE_DESCRIPTION

# Build Settings
ITEMS_PER_PAGE = 24
FEATURED_COUNT = 6
RECENT_COUNT = 8
