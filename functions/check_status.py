import asyncio
import random
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright  # Playwright async API
from functions.status import still_auctioning, cancelled_auction, auction_referred, auction_sold

async def extract_url_status(url, browser, max_retries=3):
    """
    Use Playwright to retrieve the page at `url` and determine the auction status.
    Returns a tuple (status_code, soup, price, url) where:
      - status_code is one of 'running', 'cancelled', 'referred', 'sold', 'unknown', or 'error'
      - soup is the BeautifulSoup object of the page (for 'referred'/'sold' statuses where details are needed; None otherwise)
      - price is the sold price (float, for 'sold' status only; None otherwise)
      - url is the page URL (echoed back for reference)
    Retries the request up to `max_retries` times using random user agents and delays for stealth.
    """
    # List of user-agent strings to mimic different browsers
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36 Edg/124.0.2478.51",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.4; rv:124.0) Gecko/20100101 Firefox/124.0"
    ]
    for attempt in range(max_retries):
        # Randomize User-Agent and delay each attempt
        user_agent = random.choice(user_agents)
        await asyncio.sleep(random.uniform(5, 8))
        # Create a fresh browser context with the random user agent
        context = await browser.new_context(user_agent=user_agent)
        page = await context.new_page()
        try:
            # Navigate to the URL with a timeout (60 seconds)
            await page.goto(url, timeout=60000)
            # Optionally, wait for network to be idle or a specific element if needed:
            # await page.wait_for_load_state('networkidle')
            # Get page content and parse with BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            # Check for each known status condition
            if still_auctioning(soup):
                # Auction is still ongoing
                return ('running', None, None, url)
            if cancelled_auction(soup):
                # Auction was cancelled
                return ('cancelled', None, None, url)
            if auction_referred(soup):
                # Auction ended as referred (no sale)
                return ('referred', soup, None, url)
            sold_flag, sold_price = auction_sold(soup)
            if sold_flag:
                # Auction ended as sold
                return ('sold', soup, sold_price, url)
            # If none of the conditions matched:
            print(f"Unknown status for URL: {url} (Attempt {attempt+1})")
            # Continue to next attempt (after closing context in finally)
        except Exception as e:
            # Handle network errors, timeouts, etc.
            print(f"Request failed on attempt {attempt+1} for {url}: {e}")
            # (Will retry if attempts remain)
        finally:
            # Close the context (and page) to clean up resources
            await context.close()
    # If all attempts exhausted without a definitive status:
    print(f"Failed to retrieve page after {max_retries} attempts: {url}")
    return ('error', None, None, url)
