
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

OUTPUT_FILE = RAW_DATA_DIR / "used_car_ads.csv"

# Browser settings
HEADLESS = False
TIMEOUT_MS = 30_000

REQUEST_DELAY_SECONDS = 10

# Collection settings
MAX_LISTINGS = 100
MAX_PAGES = 10

# Add listing URLs only after confirming automated access is permitted.
LISTING_URLS = ["https://www.avito.ma/fr/maroc/voitures_d_occasion-%C3%A0_vendre?o=30",]



# Optional CSS selectors, to be filled after inspecting the permitted
# target page's actual HTML.
SELECTORS = {
    "title": "",
    "price": "",
    "city": "",
    "year": "",
    "mileage": "",
    "brand": "",
}

# Agreed dataset schema
CSV_COLUMNS = [
    "marque",
    "annee",
    "ville",
    "kilometrage",
    "prix",
    "url_annonce",
    "titre_annonce",
    "date_collecte",
]
