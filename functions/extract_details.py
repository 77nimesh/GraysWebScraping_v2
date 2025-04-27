import re

def extract_vehicle_details(soup, details=None):
    """
    Extract vehicle details from the auction page soup.
    Returns a dictionary of vehicle attributes (year, make, model, variant, etc.).
    """
    # Start with a new details dict to avoid stale data
    if details is None:
        details = {}
    else:
        details.clear()
    try:
        main_title = soup.find('h1', class_='dls-heading-3 lotPageTitle')
        description_div = soup.find('div', class_='sanitised-markup')
        date_tag = soup.find('abbr', class_='endtime text-decoration-none')
        if main_title and description_div:
            title_parts = main_title.text.strip().split()
            # Parse year, make, model, variant from the title
            year_match = re.search(r'\d{4}', title_parts[0])
            try:
                if year_match:
                    # Title begins with a year
                    details['year'] = str(year_match.group(0))
                    details['make'] = title_parts[1] if len(title_parts) > 1 else ''
                    details['model'] = title_parts[2] if len(title_parts) > 2 else ''
                    details['variant'] = ' '.join(title_parts[3:]) if len(title_parts) > 3 else ''
                else:
                    # No year at start of title
                    details['year'] = 0
                    details['make'] = title_parts[0] if len(title_parts) > 0 else ''
                    details['model'] = title_parts[1] if len(title_parts) > 1 else ''
                    details['variant'] = ' '.join(title_parts[2:]) if len(title_parts) > 2 else ''
            except Exception as e:
                print(f"Error extracting title details: {e}")
                return None
            # Extract all key: value items from the description list
            for item in description_div.find_all('li'):
                try:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = map(str.strip, text.split(':', 1))
                        # If value is empty or indicates missing info, use '?'
                        if not value or value.lower() == 'unable to locate':
                            details[key] = '?'
                        else:
                            details[key] = value
                except Exception as e:
                    print(f"Error processing item '{item.text}': {e}")

            bid_amount = soup.find('div', class_='dls-text-medium position-relative').find('a').text.split(' ')[0]
            try:
                if int(bid_amount):  # Attempting to convert 'd' to an integer
                    details['bids'] = int(bid_amount)
                else:
                    details['bids'] = None  # If conversion fails, set to None
            except ValueError:
                details['bids'] = None  # If conversion fails, set to None
                print("Invalid input: 'd' cannot be converted to an integer.")

            # Normalize specific fields
            try:
                # Registration Expiry Date: ensure it’s just a date string
                if 'Registration Expiry Date' in details and details['Registration Expiry Date']:
                    match = re.search(r'\b\d{2}/\d{2}/\d{4}\b', details['Registration Expiry Date'])
                    details['Registration Expiry Date'] = match.group(0) if match else '?'
            except Exception as e:
                print(f"Error parsing Registration Expiry Date: {e}")
            try:
                # Find the <tr> that contains 'Location'
                location_text = soup.find('td', string=re.compile('Location', re.IGNORECASE)).next_sibling.next_sibling.text.strip()

                if location_text:
                    location_text = location_text.split(',')[-2].strip().upper()
                    if location_text in ['NSW', 'VIC', 'QLD', 'SA', 'WA', 'TAS', 'NT']:
                        details['Location'] = location_text
                    else:
                        details['Location'] = '?'
                else:
                    details['Location'] = '?'
            except Exception as e:
                print(f"Error extracting Location: {e}")
                details['Location'] = '?'
                
            # Remove unwanted keys
            if 'Key No' in details:
                try:
                    details.pop('Key No', None)
                except Exception as e:
                    print(f"Error removing 'Key No': {e}")
            # Auction end date
            try:
                if date_tag and date_tag.has_attr('title'):
                    # date_tag['title'] example: "2023-05-12T14:30:00"
                    details['date'] = date_tag['title'].split('T')[0]
                else:
                    details['date'] = None
            except Exception as e:
                print(f"Error extracting date: {e}")
            return details
        else:
            # Essential elements not found
            print("Main title or description section not found in page.")
            return None
    except Exception as e:
        print(f"Unexpected error in extract_vehicle_details: {e}")
        return None
