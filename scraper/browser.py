
from playwright.sync_api import sync_playwright


def launch_browser(headless=False):
    playwright = sync_playwright().start()

    browser = playwright.chromium.launch(
        headless=headless
    )

    return playwright, browser


def close_browser(playwright, browser):
    browser.close()
    playwright.stop()
