
import requests
import os 
import json
import configparser

# Load configuration from config file
CONFIG_FILE = 'config.ini'
config = configparser.ConfigParser()

if os.path.exists(CONFIG_FILE):
    config.read(CONFIG_FILE)
    try:
        x_rapidapi_key = config.get('amazon', 'RAPID_API_KEY')
        x_rapidapi_host = config.get('amazon', 'RAPID_API_HOST')
    except (configparser.NoSectionError, configparser.NoOptionError) as e:
        print(f"Amazon credentials not found in config.ini - {e}")
        x_rapidapi_key = None
        x_rapidapi_host = None
else:
    print(f"Configuration file '{CONFIG_FILE}' not found.")
    x_rapidapi_key = None
    x_rapidapi_host = None


def search_amazon(query, min_price=None, max_price=None, sort_by="", page="1", geo="US"):
    """
    Search Amazon products using RapidAPI.
    """
    if not x_rapidapi_key or not x_rapidapi_host:
        return {"error": "Amazon API credentials not configured in .env file"}
    
    url = "https://amazon-online-data-api.p.rapidapi.com/search"
    
    querystring = {
        "query": query,
        "page": page,
        "geo": geo
    }
    
    # Add sort_by only if provided
    if sort_by:
        querystring["sort_by"] = sort_by
    
    # Add price filters if provided
    if min_price is not None:
        querystring["min_price"] = str(min_price)
    if max_price is not None:
        querystring["max_price"] = str(max_price)
    
    headers = {
        "x-rapidapi-key": x_rapidapi_key,
        "x-rapidapi-host": x_rapidapi_host
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        error_detail = f"HTTP {response.status_code}: {response.text[:200]}"
        return {"error": f"API request failed: {error_detail}"}
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}


def run_amazon_search(query, min_price=None, max_price=None, sort_by="", output_file=None):
    """
    Primary user-facing function to execute an Amazon search
    """
    print(f"\n--- Starting Amazon Search for: {query} ---")
    
    if not query:
        raise ValueError("A product search name is required.")
    
    results = search_amazon(query, min_price, max_price, sort_by)
    
    if output_file and "error" not in results:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"Search results saved to {output_file}")
    
    return results
