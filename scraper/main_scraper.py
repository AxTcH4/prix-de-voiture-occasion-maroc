
from scraper.browser import launch_browser, close_browser
from scraper.collector import collect_listings, save_to_csv
from scraper.config import HEADLESS, LISTING_URLS


def main():

    if not LISTING_URLS:
        print("No search URLs configured.")
        return

    playwright, browser = launch_browser(
        headless=HEADLESS
    )

    try:
        # for i in range (2,20):
        #      LISTING_URLS.append(f"https://www.avito.ma/fr/maroc/voitures_d_occasion-%C3%A0_vendre?o={i}")

        records = collect_listings(
            browser,
            LISTING_URLS
        )

        save_to_csv(records)

    finally:
        close_browser(playwright, browser)


if __name__ == "__main__":
    main()
