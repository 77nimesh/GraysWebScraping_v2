# status.py

def still_auctioning(soup):
    """Return True if the auction is still running (e.g., a current bid is shown)."""
    try:
        current_bid_div = soup.find('div', class_='dls-text-medium position-relative')
        if current_bid_div:
            text_parts = current_bid_div.text.split()
            if len(text_parts) >= 2 and text_parts[0] == "Current" and text_parts[1] == "Bid":
                return True
    except Exception as e:
        print(f"Error in still_auctioning: {e}")
    return False

def cancelled_auction(soup):
    """Return True if the auction has been cancelled."""
    try:
        title_tag = soup.find('title')
        salepage_title = soup.find('div', class_='salepagetitle')
        if title_tag and salepage_title:
            salepage_heading = salepage_title.find('h1')
            title_text = title_tag.string if title_tag else ''
            salepage_text = salepage_heading.text if salepage_heading else ''
            if "Cancelled" in title_text and salepage_text:
                return True
    except Exception as e:
        print(f"Error in cancelled_auction: {e}")
    return False

def auction_referred(soup):
    """Return True if the auction ended as referred (reserve not met)."""
    try:
        heading_div = soup.find('div', class_='dls-heading-3')
        if heading_div and ('referred' in heading_div.text.lower() or 'closed' in heading_div.text.lower()):
            return True
    except Exception as e:
        print(f"Error in auction_referred: {e}")
    return False

def auction_sold(soup):
    """Return (True, price) if the auction ended as sold, otherwise (False, None)."""
    try:
        sold_div = soup.find('div', class_='dls-heading-3 currentbid_price')
        if sold_div and 'sold for' in sold_div.text.lower():
            price_elem = soup.find('span', itemprop='price')
            if price_elem:
                price_text = price_elem.text.strip()
                # Remove currency symbol and commas for conversion
                price_value = price_text.replace('$', '').replace(',', '')
                price = float(price_value) if price_value else None
            else:
                price = None
            return True, price
    except Exception as e:
        print(f"Error in auction_sold: {e}")
    return False, None
