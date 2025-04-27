# Grays Web Scraper Project v2

This Python project is an **asynchronous Playwright-based web scraper** designed to:

- **Collect car auction links** from Grays website
- **Scrape car auction details** (sold, referred, running vehicles)
- **Save data cleanly** into organized CSV files
- **Avoid IP blocking** using random delays, user-agents, and stealth techniques
- **Modular structure** with professional folder organization

---

## Folder Structure

```bash
GraysWebScraping_v2/
├── main.py                 # Entry point - Collects links + Scrapes data
├── CSV_data/                # Folder containing all CSV files
│   ├── car_links.csv
│   ├── sold_cars.csv
│   ├── referred_cars.csv
│   ├── running_cars.csv
│   └── scraped_links.csv
├── functions/               # All reusable Python modules
│   ├── __init__.py
│   ├── check_status.py
│   ├── columns.py
│   ├── collect_links.py
│   ├── extract_details.py
│   └── status.py
├── logs/                    # Scraping logs
│   └── scraping.log
└── README.md                # This file
```

---

## Project Features

### Link Collection
- Scrapes car auction listing pages.
- Random **User-Agent** for every page.
- Random **delays (3-6s)** to avoid detection.
- Saves all car auction item links into `CSV_data/car_links.csv`.

### Auction Scraping
- Scrapes each car auction page for:
  - Year, Make, Model, Variant
  - VIN, Engine, Transmission, Fuel Type, Body Type
  - Registration Expiry Date
  - **Sold Price**
  - **Current Bid Amount**
  - **Number of Bids**
  - Auction End Date
  - Location (State: VIC, NSW, etc.)
- Detects auction status:
  - **Sold**
  - **Referred (unsold)**
  - **Still Running**
  - **Cancelled**

### Anti-Blocking
- Fresh browser context for each page.
- Random user-agent rotation.
- Randomized human-like waiting times.
- Live console and file logging.

### Data Storage
- CSV files organized under `CSV_data/`:
  - `car_links.csv` for pending scraping links
  - `sold_cars.csv` for sold vehicle details
  - `referred_cars.csv` for referred vehicles
  - `running_cars.csv` for vehicles still under auction
  - `scraped_links.csv` for tracking scraped URLs

### Logging
- All scraping actions are logged live to console **and** saved in `logs/scraping.log`.
- Info, Warnings, and Errors are recorded.

---

## Requirements

- Python 3.10+
- Packages:
  - `playwright`
  - `pandas`
  - `tqdm`

### Install Requirements

```bash
pip install pandas tqdm playwright
python -m playwright install chromium
```

---

## How to Run

### 1. From the project root folder:

```bash
python main.py
```

This will automatically:
- **Collect fresh car links** from Grays
- **Scrape auction data** for collected links
- **Update all CSV files** inside `CSV_data/`
- **Log everything** into `logs/scraping.log`

---

## Important Notes

- Always run `main.py` from the **root folder**.
- Playwright downloads its own Chromium browser automatically.
- Random User-Agent and fresh contexts prevent most basic bot detections.
- If Grays changes website structure, scraping modules might need updates.

---

## Future Improvements (optional)

- Retry logic for failed page loads
- Parallel scraping batches to speed up
- Captcha detection and handling
- Telegram/email notifications on completion

---

## Credits
- Built using [Microsoft Playwright](https://playwright.dev/python/)
- Realistic scraping methods based on best practices for modern web scraping.

---

## License

This project is for **personal learning and educational use only**.
Respect the website's `robots.txt` and terms of service when scraping.

---

# Happy Scraping! 🚀

