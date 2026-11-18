
import re
from datetime import date


CAR_BRANDS = [
    "Mercedes-Benz", "Land Rover", "Alfa Romeo",
    "Volkswagen", "Mitsubishi", "Chevrolet",
    "Citroën", "Hyundai", "Peugeot", "Renault",
    "Toyota", "Dacia", "Audi", "BMW", "Porsche",
    "Ford", "Fiat", "Nissan", "Kia", "Honda",
    "Skoda", "Seat", "Opel", "Suzuki", "Jeep",
    "Volvo", "Mazda", "Mini", "Tesla",
]


def clean_number(value):
    """Convert formatted numbers into integers."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        return int(value)

    digits = re.sub(r"[^\d]", "", str(value))
    return int(digits) if digits else None


def extract_brand(title):
    """Identify the brand from the advertisement title."""
    for brand in CAR_BRANDS:
        if re.search(re.escape(brand), title, re.IGNORECASE):
            return brand

    return None


def parse_card_text(text, url):
    """Extract car information from one Avito search-result card."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not lines:
        return None

    title = lines[0]
    full_text = " ".join(lines)

    # Vehicle year
    year = None

    for line in lines:
        match = re.fullmatch(
            r"((?:19|20)\d{2})(?:\s+ou plus ancien)?",
            line,
            re.IGNORECASE
        )

        if match:
            year = int(match.group(1))
            break

    # Mileage
    mileage = None

    mileage_match = re.search(
        r"([\d\s\u202f,]+)\s*km\b",
        full_text,
        re.IGNORECASE
    )

    if mileage_match:
        mileage = clean_number(mileage_match.group(1))

    # Price: exclude monthly financing payments
    price = None

    price_match = re.search(
        r"([\d][\d\s\u202f,]*)\s*DH(?!\s*/\s*mois)",
        full_text,
        re.IGNORECASE
    )

    if price_match:
        price = clean_number(price_match.group(1))

    # City: normally the line immediately before "il y a..."
    city = None

    for index, line in enumerate(lines):
        if re.search(r"\bil y a\b", line, re.IGNORECASE):
            if index > 0:
                city = lines[index - 1]
            break

    return {
        "marque": extract_brand(title),
        "annee": year,
        "ville": city,
        "kilometrage": mileage,
        "prix": price,
        "url_annonce": url,
        "titre_annonce": title,
        "date_collecte": date.today().isoformat(),
    }




def extract_listing_records(page):
    from urllib.parse import urlparse

    # Collect every anchor. Filter URLs in Python instead of CSS.
    links = page.locator("a").evaluate_all("""
        elements => elements.map(a => ({
            url: a.href,
            text: a.innerText || ""
        }))
    """)

    records = []
    seen = set()

    for link in links:
        url = link["url"]
        path = urlparse(url).path

        # Keep only individual vehicle advertisements.
        if "/voitures_d_occasion/" not in path:
            continue

        filename = path.rsplit("/", 1)[-1]
        if not filename.endswith(".htm"):
            continue

        # Avito advertisement IDs are numeric suffixes.
        ad_id = filename[:-4].rsplit("_", 1)[-1]
        if not ad_id.isdigit():
            continue

        if url in seen:
            continue

        seen.add(url)

        record = parse_card_text(link["text"], url)

        if record and record["titre_annonce"]:
            records.append(record)

    return records
