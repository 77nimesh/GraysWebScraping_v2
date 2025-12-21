"""
Module for asynchronously scraping car auction links from Grays website.

Changes (fixes):
- No more wait_for_selector timeout spam
- If a page genuinely has 0 lot links, prints: "No more links found..." and stops
- Accepts BOTH URL patterns:
    motor-vehicles-motor-cycles
    motor-vehiclesmotor-cycles
- Keeps the same href format as before (relative /lot/... links)
"""

import asyncio
import random
import pandas as pd
import os
from playwright.async_api import async_playwright

# Base URL and auction page template
BASE_URL = "https://www.grays.com"
AUCTION_URL_TEMPLATE = (
    "https://www.grays.com/search/automotive-trucks-and-marine/"
    "motor-vehiclesmotor-cycles?tab=items&sort=close-time-asc&page={}"
)

# Path for storing links CSV
CSV_FILE = "CSV_data/car_links.csv"

# Realistic desktop User-Agents (removed iPhone UA to avoid mobile markup mismatch)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

# If you want a safety cap (optional)
MAX_PAGES = 200

def is_vehicle_lot_link(href: str) -> bool:
    """True if href looks like a vehicle lot link we care about."""
    if not href or "/lot/" not in href:
        return False

    # Accept both patterns (Grays has used both)
    return ("motor-vehicles-motor-cycles" in href) or ("motor-vehiclesmotor-cycles" in href)

async def collect_car_links():
    """Collects car auction links and updates the CSV."""
    try:
        existing_links = set(pd.read_csv(CSV_FILE)["Car Links"].dropna().astype(str).tolist())
        print(f"Loaded {len(existing_links)} existing links from CSV.")
    except FileNotFoundError:
        existing_links = set()
        print("No existing CSV found. Starting fresh.")

    new_links = set()
    page_number = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        while page_number <= MAX_PAGES:
            auction_url = AUCTION_URL_TEMPLATE.format(page_number)
            print(f"Scraping page {page_number}...")

            context = None
            try:
                user_agent = random.choice(USER_AGENTS)
                context = await browser.new_context(user_agent=user_agent)
                page = await context.new_page()

                # Load page
                await page.goto(auction_url, wait_until="domcontentloaded", timeout=60_000)

                # Let JS finish (don’t fail if it never reaches networkidle)
                try:
                    await page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception:
                    pass

                # Small jitter so it behaves like your old “working” version
                await asyncio.sleep(random.uniform(1.5, 3.0))

                # Collect lot links
                car_elements = await page.query_selector_all("a[href*='/lot/']")

                # If there are genuinely no lot links, stop cleanly
                if not car_elements:
                    print(f"No more links found. Stopping at page {page_number}.")
                    break

                for element in car_elements:
                    try:
                        href = await element.get_attribute("href")
                        if href and is_vehicle_lot_link(href):
                            if href not in existing_links and href not in new_links:
                                new_links.add(href)
                    except (TypeError, AttributeError) as err:
                        print(f"Error getting link: {err}")

            except Exception as err:
                print(f"Error loading page {page_number}: {err}")
                break
            finally:
                if context:
                    await context.close()

            delay = random.uniform(3, 6)
            print(f"Waiting {delay:.2f} seconds before next page...")
            await asyncio.sleep(delay)

            page_number += 1

        await browser.close()

    print(f"Found {len(new_links)} new car links.")

    # Update the CSV file with new links only
    if new_links:
        all_links = existing_links.union(new_links)

        # Keep only relevant vehicle lot links (both patterns)
        all_links = {link for link in all_links if is_vehicle_lot_link(link)}

        links_df = pd.DataFrame(sorted(all_links), columns=["Car Links"])
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)
        links_df.to_csv(CSV_FILE, index=False)
        print(f"CSV updated with {len(all_links)} total links.")
    else:
        print("No new links to add to the CSV.")


if __name__ == "__main__":
    asyncio.run(collect_car_links())
