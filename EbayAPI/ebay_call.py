import requests
import json
import base64
import time
import configparser
import os 


# 1. Load configuration from file
CONFIG_FILE = 'EbayAPI/ebay_config.ini'
config = configparser.ConfigParser()

# Check if the config file exists before trying to read it
if not os.path.exists(CONFIG_FILE):
    print(f"ERROR: Configuration file '{CONFIG_FILE}' not found.")
    print("Please create this file and add your CLIENT_ID and CLIENT_SECRET under the [ebay] section.")
    exit(1)

config.read(CONFIG_FILE)

# extract variables
try:
    CLIENT_ID = config.get('ebay', 'CLIENT_ID')
    CLIENT_SECRET = config.get('ebay', 'CLIENT_SECRET')
    MARKETPLACE_ID = 'EBAY_US'
except configparser.NoSectionError:
    print(f"ERROR: No '[ebay]' section found in '{CONFIG_FILE}'.")
    exit(1)
except configparser.NoOptionError as e:
    print(f"ERROR: Missing required option {e} in the [ebay] section of '{CONFIG_FILE}'.")
    exit(1)

# API Endpoints
TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
EBAY_API_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

# Global Token Variables 
EBAY_ACCESS_TOKEN = None 
TOKEN_EXPIRY_TIME = 0 


# 2. Token generation function to handle authorization

def get_access_token():
    """
    Generates a new Application Access Token (valid for around 2 hours) using the 
    Client Credentials Flow or returns the existing valid token.
    """
    global EBAY_ACCESS_TOKEN, TOKEN_EXPIRY_TIME

    # Check for placeholder values
    if CLIENT_ID == "YCLIENT_ID_HERE" or CLIENT_SECRET == "CLIENT_SECRET_HERE":
        print("\nERROR: Please replace the placeholder values in the 'ebay_config.ini' file.")
        return False
        
    # Check if the current token is still valid
    if EBAY_ACCESS_TOKEN and time.time() < TOKEN_EXPIRY_TIME - 300: 
        print("\nUsing existing, valid access token.")
        return True

    print("\nRequesting new eBay Application Access Token from Production...")
    
    # Base64 encode the Client ID and Client Secret (required for the Authorization header)
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

    try:
        response = requests.post(TOKEN_URL, headers=token_headers, data=token_payload)
        
        if response.status_code != 200:
            print(f"\nTOKEN REQUEST FAILED: HTTP Status Code {response.status_code}")
            print(f"Response body: {response.text}")
            print("\nError: Could not generate a token. Check your Production keys and eBay Exemption status.")
            return False

        # Process successful response
        token_data = response.json()
        
        EBAY_ACCESS_TOKEN = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 7200) 
        TOKEN_EXPIRY_TIME = time.time() + expires_in
        
        print("Successfully generated new access token. It is valid for approximately 2 hours.")
        return True

    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during token request (network/connection error): {e}")
        
    return False

# 3. API Call Function, which handles the search

def search_ebay(query, price_range=None, condition_filter=None):
    """
    Searches eBay's Browse API for items based on the given query,
    applying optional price and condition filters.
    """
    if not get_access_token():
        print("Cannot proceed with search without a valid token.")
        return

    # Set up the required headers for the eBay Browse API
    headers = {
        "Authorization": f"Bearer {EBAY_ACCESS_TOKEN}", 
        "X-EBAY-C-MARKETPLACE-ID": MARKETPLACE_ID,
        "Content-Type": "application/json"
    }

    # Filters
    filter_list = ["buyingOptions:{FIXED_PRICE}"]
 
    if price_range:
        currency = 'USD'
        filter_list.append(f"price:[{price_range}],priceCurrency:{currency}")

    if condition_filter:
        filter_list.append(f"conditions:{{{condition_filter.replace(',', '|')}}}")

    # Set up the query parameters
    params = {
        "q": query,
        "fieldgroups": "EXTENDED", 
        "filter": ",".join(filter_list),
        "limit": 5 
    }

    print(f"\nSearching eBay for: '{query}' with filters: {params['filter']}")

    try:
        response = requests.get(EBAY_API_URL, headers=headers, params=params)
        response.raise_for_status()

        data = response.json()
        return data

    except requests.exceptions.HTTPError as e:
        print(f"\nAPI Error: HTTP status code {response.status_code}")
        print(f"Response body: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"\nAn error occurred during the request: {e}")
    except json.JSONDecodeError:
        print(f"\nError decoding JSON response from API.")
    return None


# 4. Output Function
def display_results(data):
    """
    Parses and returns relevant information from the API response as a structured dictionary.
    """
    if not data or 'itemSummaries' not in data:
        return {"search_status": "No live items found for this query."}

    items_data = []
    
    for item in data['itemSummaries']:
        # Format the price
        price_value = item.get('price', {}).get('value', 'N/A')
        price_currency = item.get('price', {}).get('currency', '')
        
        # Extract item location
        location = item.get('itemLocation', {}).get('city', 'N/A')
        state = item.get('itemLocation', {}).get('stateOrProvince', '')
        country = item.get('itemLocation', {}).get('country', '')
        full_location = ", ".join(filter(None, [location, state, country]))

        item_dict = {
            "title": item.get('title', 'N/A'),
            "price": f"{price_currency} {price_value}",
            "condition": item.get('condition', 'N/A'),
            "location": full_location,
            "description": item.get('shortDescription', 'N/A'),
            "link": item.get('itemWebUrl', '#')
        }
        items_data.append(item_dict)

    return {"found_items_count": len(items_data), "items": items_data}

# 5. Modular Function Call (New Primary User Function)
def run_search(query, min_price=None, max_price=None, condition=None, output_file="output.json"):
    """
    Primary user-facing function to execute a search and return the results as a JSON string.
    
    ================================================================================
    REQUIRED INPUT:
    - query (str): The search keyword (e.g., "spiderman toys").
    
    OPTIONAL INPUTS:
    - min_price (str/float/None): The minimum price for the search.
    - max_price (str/float/None): The maximum price for the search.
    - condition (str/None): Comma-separated list of conditions (e.g., "NEW, USED").
    - output_file (str): The name of the file to save the output JSON (default: "output.json").
    ================================================================================
    """
    print("--- Starting eBay Search ---")
    
    if not query:
        raise ValueError("The 'query' parameter is required.")
    
    # Check for token validity
    if not get_access_token():
        return json.dumps({"status": "error", "message": "Failed to generate eBay access token."}, indent=4)
        
    # Combine min and max into the required 'min..max' format
    price_range = ""
    if min_price or max_price:
        min_val = str(min_price) if min_price is not None else ""
        max_val = str(max_price) if max_price is not None else ""
        price_range = f"{min_val}..{max_val}"
    
    condition_input = str(condition).replace(' ', '').strip().upper() if condition else None
        
    results = search_ebay(query, price_range, condition_input)
    
    if results:
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(results, json_file, indent=4)
        print(f"Search results saved to {output_file}")
    else:
        return json.dumps({"status": "error", "message": "Search failed or returned no data."}, indent=4)