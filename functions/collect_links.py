"""
Module for asynchronously scraping car auction links from Grays website.
Now with:
- Random User-Agent per page
- Random delays between pages
- Fresh browser context per page
- Safe file paths
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
CSV_FILE = 'CSV_data/car_links.csv'

# List of realistic User-Agents
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:112.0) Gecko/20100101 Firefox/112.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"
]

async def collect_car_links():
    """Collects car auction links and updates the CSV."""
    try:
        existing_links = set(pd.read_csv(CSV_FILE)['Car Links'].tolist())
        print(f"Loaded {len(existing_links)} existing links from CSV.")
    except FileNotFoundError:
        existing_links = set()
        print("No existing CSV found. Starting fresh.")

    new_links = set()
    page_number = 1

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        while True:
            auction_url = AUCTION_URL_TEMPLATE.format(page_number)
            print(f"Scraping page {page_number}...")

            try:
                user_agent = random.choice(USER_AGENTS)
                context = await browser.new_context(user_agent=user_agent)
                page = await context.new_page()

                await page.goto(auction_url)

                car_elements = await page.query_selector_all("//a[contains(@href, '/lot/')]")
                if not car_elements:
                    print(f"No more links found. Stopping at page {page_number}.")
                    await context.close()
                    break

                for element in car_elements:
                    try:
                        link = await element.get_attribute('href')
                        if link and link not in existing_links and link not in new_links:
                            new_links.add(link)
                    except (TypeError, AttributeError) as err:
                        print(f"Error getting link: {err}")

                await context.close()

            except Exception as err:
                print(f"Error loading page {page_number}: {err}")
                break

            delay = random.uniform(3, 6)
            print(f"Waiting {delay:.2f} seconds before next page...")
            await asyncio.sleep(delay)

            page_number += 1

        await browser.close()

    print(f"Found {len(new_links)} new car links.")

    # Update the CSV file with new links only
    if new_links:
        all_links = existing_links.union(new_links)
        links_df = pd.DataFrame(all_links, columns=['Car Links'])
        os.makedirs(os.path.dirname(CSV_FILE), exist_ok=True)  # Ensure folder exists
        links_df.to_csv(CSV_FILE, index=False)
        print(f"CSV updated with {len(all_links)} total links.")
    else:
        print("No new links to add to the CSV.")
