import requests
import json
import base64
import time
import configparser
import os 

# 1. Load configuration from unified config file
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()

if not os.path.exists(CONFIG_FILE):
    print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.")
    exit(1)

config.read(CONFIG_FILE)

try:
    CLIENT_ID = config.get('ebay', 'CLIENT_ID')
    CLIENT_SECRET = config.get('ebay', 'CLIENT_SECRET')
    MARKETPLACE_ID = 'EBAY_US'
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(f"ERROR: {e}")
    exit(1)

# API Endpoints
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

EBAY_ACCESS_TOKEN = None 
TOKEN_EXPIRY_TIME = 0 

# 2. Token generation
def get_access_token():
    global EBAY_ACCESS_TOKEN, TOKEN_EXPIRY_TIME
    if EBAY_ACCESS_TOKEN and time.time() < TOKEN_EXPIRY_TIME - 300:
        return True

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    base64_credentials = base64.b64encode(credentials.encode()).decode()

    token_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {base64_credentials}"
    }
    token_payload = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope"
    }

    response = requests.post(TOKEN_URL, headers=token_headers, data=token_payload)
    if response.status_code != 200:
        print(f"Token request failed: {response.text}")
        return False

    token_data = response.json()
    EBAY_ACCESS_TOKEN = token_data.get("access_token")
    TOKEN_EXPIRY_TIME = time.time() + token_data.get("expires_in", 7200)
    return True

# Condition name to ID mapping
CONDITION_MAP = {
    "NEW": "1000",
    "LIKE_NEW": "1500",
    "NEW_OTHER": "1750",
    "NEW_WITH_DEFECTS": "1500",
    "CERTIFIED_REFURBISHED": "2000",
    "EXCELLENT_REFURBISHED": "2010",
    "VERY_GOOD_REFURBISHED": "2020",
    "GOOD_REFURBISHED": "2030",
    "SELLER_REFURBISHED": "2500",
    "USED": "3000",
    "VERY_GOOD": "4000",
    "GOOD": "5000",
    "ACCEPTABLE": "6000",
    "FOR_PARTS_OR_NOT_WORKING": "7000"
}

# 3. API Call Function
def search_ebay(query, price_range=None, condition_filter=None, 
                delivery_country=None, delivery_postal_code=None,
                guaranteed_delivery_days=None, max_delivery_cost=None,
                sort_by="price"):
    """
    Search eBay with various filters.
    
    Args:
        query (str): Search keyword
        price_range (str): Price range in format "min..max" (e.g., "10..50")
        condition_filter (str): Condition names or IDs separated by | (e.g., "NEW|USED" or "1000|3000")
        delivery_country (str): 2-letter country code (e.g., "US", "GB")
        delivery_postal_code (str): Postal/ZIP code for delivery location
        guaranteed_delivery_days (int): Filter by guaranteed delivery within N days
        max_delivery_cost (float): Maximum shipping cost (use 0 for free shipping)
        sort_by (str): Sort option - "price", "-price" (desc), "distance", "newlyListed"
    
    Returns:
        dict: eBay API response JSON
    """
    if not get_access_token():
        return

    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}", 
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE_ID,
        "Content-Type": "application/json"
    }
    
    # Add contextual location header if delivery info provided
    if delivery_country and delivery_postal_code:
        encoded_location = f"contextualLocation=country%3D{delivery_country}%2Czip%3D{delivery_postal_code}"
        headers["X-EBAY-C-ENDUSERCTX"] = encoded_location

    # Filters - FIXED_PRICE only (no auctions)
    filter_list = ["buyingOptions:{FIXED_PRICE}"]
    
    if price_range:
        # Add currency to price filter
        filter_list.append(f"price:[{price_range}],priceCurrency:USD")
    
    if condition_filter:
        # Convert condition names to IDs if needed
        conditions = condition_filter.split('|')
        condition_ids = []
        for cond in conditions:
            cond = cond.strip().upper()
            # Check if it's already an ID (numeric) or a name
            if cond.isdigit():
                condition_ids.append(cond)
            elif cond in CONDITION_MAP:
                condition_ids.append(CONDITION_MAP[cond])
            else:
                print(f"Warning: Unknown condition '{cond}', skipping.")
        
        if condition_ids:
            filter_list.append(f"conditionIds:{{{('|'.join(condition_ids))}}}")
    
    # Delivery location filters
    if delivery_country:
        filter_list.append(f"deliveryCountry:{delivery_country}")
    
    if delivery_postal_code and delivery_country:
        filter_list.append(f"deliveryPostalCode:{delivery_postal_code}")
    
    # Guaranteed delivery filter
    if guaranteed_delivery_days is not None:
        if delivery_country and delivery_postal_code:
            filter_list.append(f"guaranteedDeliveryInDays:{guaranteed_delivery_days}")
        else:
            print("Warning: guaranteedDeliveryInDays requires deliveryCountry and deliveryPostalCode")
    
    # Max delivery cost filter
    if max_delivery_cost is not None:
        filter_list.append(f"maxDeliveryCost:{max_delivery_cost}")

    params = {
        "q": query,
        "fieldgroups": "EXTENDED",  # Use EXTENDED to get shortDescription
        "filter": ",".join(filter_list),
        "sort": sort_by,
        "limit": 5
    }

    response = requests.get(EBAY_API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# 4. Output Function
def display_results(data):
    if not data or 'itemSummaries' not in data:
        return {"search_status": "No items found."}

    items_data = []
    for item in data['itemSummaries']:
        price = item.get('price', {})
        marketing_price = item.get('marketingPrice', {})
        location = item.get('itemLocation', {})
        seller = item.get('seller', {})
        
        item_dict = {
            "title": item.get('title', 'N/A'),
            "description": item.get('shortDescription', 'N/A'),
            "url": item.get('itemWebUrl', '#'),
            "images": [img.get('imageUrl') for img in item.get('additionalImages', [])] + 
                      [item.get('image', {}).get('imageUrl')],
            "price": f"{price.get('currency', '')} {price.get('value', 'N/A')}",
            "market_price": {
                "original": marketing_price.get('originalPrice', {}).get('value'),
                "discount": marketing_price.get('discountAmount', {}).get('value'),
                "discount_percentage": marketing_price.get('discountPercentage')
            },
            "condition": item.get('condition', 'N/A'),
            "categories": [c.get('categoryName') for c in item.get('categories', [])],
            "itemLocation": ", ".join(filter(None, [location.get('city'), location.get('stateOrProvince'), location.get('country')])),
            "shippingOptions": [
                {
                    "cost": opt.get('shippingCost', {}).get('value'),
                    "currency": opt.get('shippingCost', {}).get('currency'),
                    "minDelivery": opt.get('minEstimatedDeliveryDate'),
                    "maxDelivery": opt.get('maxEstimatedDeliveryDate')
                } for opt in item.get('shippingOptions', [])
            ],
            "seller_feedbackPercentage": seller.get('feedbackPercentage', 'N/A'),
            "watchCount": item.get('watchCount', 'N/A'),
            "itemCreationDate": item.get('itemCreationDate', 'N/A')
        }
        items_data.append(item_dict)

    return {"found_items_count": len(items_data), "items": items_data}

# 5. User-facing function
def run_search(query, min_price=None, max_price=None, condition=None, 
               delivery_country=None, delivery_postal_code=None,
               guaranteed_delivery_days=None, max_delivery_cost=None,
               sort_by="price", output_file="output.json"):
    """
    User-facing search function with all available filters.
    
    Args:
        query (str): Search keyword
        min_price (float): Minimum price
        max_price (float): Maximum price
        condition (str): Condition names separated by | (e.g., "NEW|USED")
        delivery_country (str): 2-letter country code (e.g., "US")
        delivery_postal_code (str): ZIP/postal code
        guaranteed_delivery_days (int): Filter by guaranteed delivery days
        max_delivery_cost (float): Maximum shipping cost (0 for free shipping)
        sort_by (str): Sort option - "price", "-price", "distance", "newlyListed"
        output_file (str): Output JSON file name
    
    Returns:
        str: JSON formatted results
    """
    print("--- Starting eBay Search ---")
    if not get_access_token():
        return json.dumps({"status": "error", "message": "Failed to generate token."}, indent=4)

    price_range = f"{min_price or ''}..{max_price or ''}" if (min_price or max_price) else None
    condition_input = str(condition).strip().upper() if condition else None

    results = search_ebay(
        query=query, 
        price_range=price_range, 
        condition_filter=condition_input,
        delivery_country=delivery_country,
        delivery_postal_code=delivery_postal_code,
        guaranteed_delivery_days=guaranteed_delivery_days,
        max_delivery_cost=max_delivery_cost,
        sort_by=sort_by
    )
    
    if results:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4)
        formatted_output = display_results(results)
        return json.dumps(formatted_output, indent=4)
    else:
        return json.dumps({"status": "error", "message": "Search failed."}, indent=4)
