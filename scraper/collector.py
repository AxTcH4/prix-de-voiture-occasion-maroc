import csv
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
import time
import random

from scraper.config import (
    CSV_COLUMNS,
    MAX_LISTINGS,
    MAX_PAGES,
    OUTPUT_FILE,
    REQUEST_DELAY_SECONDS,
    TIMEOUT_MS,
)
from scraper.parser import extract_listing_records


def build_page_url(base_url, page_number):
    if page_number == 1:
        return base_url

    parts = urlsplit(base_url)
    params = dict(parse_qsl(parts.query))
    params["o"] = str(page_number)

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        parts.path,
        urlencode(params),
        parts.fragment,
    ))



def collect_listings(browser, urls):
    records = []
    seen_urls = set()

    page = browser.new_page()
    page.set_default_timeout(TIMEOUT_MS)

    try:
        for base_url in urls:
            for page_number in range(1, MAX_PAGES + 1):

                if len(records) >= MAX_LISTINGS:
                    break

                search_url = build_page_url(base_url, page_number)

                print(f"\n{'=' * 60}")
                print(f"Opening page {page_number}")
                print(search_url)

                # #Cooldown 
                # delay = REQUEST_DELAY_SECONDS + random.uniform(0, 3)

                # print(f"Cooling down for {delay:.1f} seconds...")
                # time.sleep(delay)

                # response = page.goto(
                #     search_url,
                #     wait_until="domcontentloaded",
                #     timeout=TIMEOUT_MS
                # )

                try:
                    response = page.goto(
                        search_url,
                        wait_until="domcontentloaded",
                        timeout=TIMEOUT_MS
                    )

                    if response is None:
                        print("No HTTP response received. Stopping.")
                        break

                    print(f"HTTP status: {response.status}")
                    if response.status == 403:
                        print("Avito returned HTTP 403. Stopping collection.")
                        break

                    if response.status >= 400:
                        print(f"HTTP error: {response.status}. Stopping collection.")
                        break
                    if response.status >= 400:
                        print(
                            f"Page {page_number} failed "
                            f"with HTTP {response.status}. Stopping."
                        )
                        break

                    page.wait_for_timeout(2000)

                    page_records = extract_listing_records(page)

                    print(f"Extracted {len(page_records)} advertisements.")

                    new_count = 0

                    for record in page_records:
                        url = record["url_annonce"]

                        if url in seen_urls:
                            continue

                        seen_urls.add(url)
                        records.append(record)
                        new_count += 1

                        print(
                            f"[{len(records)}] "
                            f"{record['titre_annonce']} | "
                            f"{record['prix']} DH"
                        )

                        if len(records) >= MAX_LISTINGS:
                            break

                    print(f"New advertisements from this page: {new_count}")

                    if new_count == 0:
                        print("No new advertisements. Stopping pagination.")
                        break

                except Exception as error:
                    print(f"Error on page {page_number}: {error}")
                    break

                # The next iteration navigates to the next page.
                # No concurrent page processing occurs.

    finally:
        page.close()

    print(f"\nTotal collected this run: {len(records)}")
    return records


def save_to_csv(records):
    """Save new records while preserving existing advertisements."""

    if not records:
        print("No new advertisements to save.")
        return

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    existing_records = {}

    # Load previously collected advertisements.
    if OUTPUT_FILE.exists():
        with OUTPUT_FILE.open(
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as file:
            reader = csv.DictReader(file)

            for row in reader:
                existing_records[row["url_annonce"]] = row

    # Add or update advertisements by URL.
    for record in records:
        existing_records[record["url_annonce"]] = record

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=CSV_COLUMNS
        )

        writer.writeheader()
        writer.writerows(existing_records.values())

    print(
        f"\nSaved dataset: {len(existing_records)} unique advertisements."
    )
    print(f"Output: {OUTPUT_FILE}")
