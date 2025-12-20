import asyncio
import os
from pathlib import Path
import logging
from colorlog import ColoredFormatter
from playwright.async_api import async_playwright
import pandas as pd
from tqdm import tqdm
from functions.columns import columns_list
from functions.check_status import extract_url_status
from functions.extract_details import extract_vehicle_details
from functions.collect_links import collect_car_links

# Setup logging with color
if not os.path.exists('logs'):
    os.makedirs('logs')

class CustomColorFormatter(ColoredFormatter):
    def format(self, record):
        msg = record.getMessage().lower()
        if 'referred' in msg:
            self.log_colors['INFO'] = 'cyan'
        elif 'sold' in msg:
            self.log_colors['INFO'] = 'green'
        elif 'cancelled' in msg:
            self.log_colors['INFO'] = 'red'
        elif 'auctioning' in msg:
            self.log_colors['INFO'] = 'purple'
        else:
            self.log_colors['INFO'] = 'white'
        return super().format(record)

console_handler = logging.StreamHandler()
console_handler.setFormatter(CustomColorFormatter(
    "%(log_color)s%(asctime)s [%(levelname)s] %(message)s",
    datefmt='%Y-%m-%d %H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'white',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'bold_red',
    }
))

file_handler = logging.FileHandler('logs/scraping.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))

logger = logging.getLogger()
logger.handlers = []
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

async def main():
    await collect_car_links()

    try:
        car_links_df = pd.read_csv('CSV_data/car_links.csv')
        car_links = car_links_df['Car Links'].tolist()
        logging.info(f"Loaded {len(car_links)} car links from CSV.")
    except FileNotFoundError:
        logging.warning("Car links CSV not found. Starting with an empty list.")
        car_links = []
        car_links_df = pd.DataFrame(columns=['Car Links'])

    try:
        sold_cars_df = pd.read_csv('CSV_data/sold_cars.csv')
        existing_vin_dates_sold = set(zip(sold_cars_df['VIN'].fillna(''), sold_cars_df['date'].fillna('')))
        logging.info(f"Loaded {len(existing_vin_dates_sold)} existing sold car records.")
    except FileNotFoundError:
        sold_cars_df = pd.DataFrame(columns=columns_list())
        existing_vin_dates_sold = set()
        logging.warning("No existing sold car records found.")

    try:
        referred_df = pd.read_csv('CSV_data/referred_cars.csv')
        existing_vin_dates_referred = set(zip(referred_df['VIN'].fillna(''), referred_df['date'].fillna('')))
        logging.info(f"Loaded {len(existing_vin_dates_referred)} existing referred car records.")
    except FileNotFoundError:
        referred_df = pd.DataFrame(columns=columns_list())
        existing_vin_dates_referred = set()
        logging.warning("No existing referred car records found.")

    try:
        scraped_links_df = pd.read_csv('CSV_data/scraped_links.csv')
        logging.info(f"Loaded {len(scraped_links_df)} existing scraped links.")
    except FileNotFoundError:
        scraped_links_df = pd.DataFrame(columns=['Referred_URL', 'Sold_URL'])
        logging.warning("No existing scraped links found.")

    if not car_links:
        logging.info("No car links to process. Exiting.")
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        batch_size = 8
        progress = tqdm(total=len(car_links), desc="Processing car links", unit="link")

        car_links_copy = car_links.copy()

        for batch_start in range(0, len(car_links_copy), batch_size):
            batch_links = car_links_copy[batch_start: batch_start + batch_size]
            tasks = [extract_url_status(link, browser) for link in batch_links]
            results = await asyncio.gather(*tasks)

            for status_code, soup, price, url in results:
                if status_code == 'running':
                    logging.info(f"Still auctioning: {url}")

                elif status_code == 'cancelled':
                    logging.info(f"Cancelled auction: {url}")
                    if url in car_links:
                        car_links.remove(url)

                elif status_code == 'referred':
                    logging.info(f"Auction referred (no sale): {url}")
                    details = extract_vehicle_details(soup, {}) or {}
                    details['price'] = 0
                    details['url'] = url
                    row_data = {col: details.get(col, '?') for col in columns_list()}
                    vin_date = (row_data.get('VIN', ''), row_data.get('date', ''))

                    if vin_date not in existing_vin_dates_referred:
                        referred_df = pd.concat([referred_df, pd.DataFrame([row_data])], ignore_index=True)
                        existing_vin_dates_referred.add(vin_date)
                        logging.info("Added new referred vehicle to referred_df.")
                    else:
                        logging.info("Referred vehicle already recorded (duplicate VIN-date).")

                    if url in car_links:
                        car_links.remove(url)
                    new_entry = {'Referred_URL': url, 'Sold_URL': ''}
                    scraped_links_df = pd.concat([scraped_links_df, pd.DataFrame([new_entry])], ignore_index=True)

                elif status_code == 'sold':
                    logging.info(f"Auction sold: {url} for ${price}")
                    details = extract_vehicle_details(soup, {}) or {}
                    details['price'] = price if price is not None else 0
                    details['url'] = url
                    row_data = {col: details.get(col, '?') for col in columns_list()}
                    vin_date = (row_data.get('VIN', ''), row_data.get('date', ''))

                    if vin_date not in existing_vin_dates_sold:
                        sold_cars_df = pd.concat([sold_cars_df, pd.DataFrame([row_data])], ignore_index=True)
                        existing_vin_dates_sold.add(vin_date)
                        logging.info("Added new sold vehicle to sold_cars_df.")
                    else:
                        logging.info("Sold vehicle already recorded (duplicate VIN-date).")

                    if url in car_links:
                        car_links.remove(url)
                    new_entry = {'Referred_URL': '', 'Sold_URL': url}
                    scraped_links_df = pd.concat([scraped_links_df, pd.DataFrame([new_entry])], ignore_index=True)

                else:
                    if status_code == 'unknown':
                        logging.warning(f"Status unknown for URL (will retry later): {url}")
                    elif status_code == 'error':
                        logging.error(f"Failed to retrieve URL (will retry later): {url}")

            out_dir = Path("../soldcartracker.github.io/JSON_data")
            out_dir.mkdir(parents=True, exist_ok=True)

            car_links_df = pd.DataFrame(car_links, columns=['Car Links'])
            car_links_df.to_csv('CSV_data/car_links.csv', index=False)
            referred_df.to_csv('CSV_data/referred_cars.csv', index=False)
            sold_cars_df.to_csv('CSV_data/sold_cars.csv', index=False)
            sold_cars_df.to_json('../soldcartracker.github.io/JSON_data/sold_cars.json', orient='records', lines=True)
            referred_df.to_json('../soldcartracker.github.io/JSON_data/referred_cars.json', orient='records', lines=True)   
            scraped_links_df.to_csv('CSV_data/scraped_links.csv', index=False)

            progress.update(len(batch_links))

        await browser.close()
        progress.close()

if __name__ == "__main__":
    asyncio.run(main())
