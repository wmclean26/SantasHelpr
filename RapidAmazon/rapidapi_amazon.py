import json 
from configparser import ConfigParser, ExtendedInterpolation
import dateparser
import re 
import requests

# SETUP API KEYS AND HOSTS 
config = ConfigParser(interpolation=ExtendedInterpolation())
config.read('config.ini')

x_rapidapi_key = config['amazon']['rapid_api_key']
x_rapidapi_host = config['amazon']['rapid_api_host']

url = "https://amazon-online-data-api.p.rapidapi.com/search"

def search_amazon(query, min_price, max_price, sort_by):

    querystring = {
        "query": query,
        "page": 1,
        "geo": "US"
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

    response = requests.get(url, headers=headers, params=querystring)

    response_json = response.json()

    return response_json

def filter_product_data(json_input, max_products, fields):
    """
    Filter product data from a JSON object to include only specified fields and limit the number of products.
    
    Args:
        json_input: The JSON object from the API response, expected to contain product data.
        max_products: Maximum number of products to return (default: 5)
        fields: List of field names to include. If None, includes ALL fields.
    
    Returns:
        A dictionary containing the list of filtered product dictionaries.
    """
    # Extract products - handle both nested and direct product lists
    if 'products' in json_input:
        products = json_input['products']
    else:
        products = json_input.get('data', {}).get('products', [])
    
    filtered_products = []
    
    for product in products[:max_products]:
        if fields is None:
            # If no fields specified, include all fields
            filtered_products.append(product)
        else:
            # Only include specified fields
            filtered_product = {}
            for field in fields:
                if field in product:
                    # Special handling for product_title - extract from URL
                    if field == 'product_title' and 'product_url' in product:
                        extracted_title = extract_title_from_url(product['product_url'])
                        if extracted_title:
                            filtered_product[field] = extracted_title
                        else:
                            # Fallback to original title if extraction fails
                            filtered_product[field] = product[field]
                    elif field == 'product_delivery_info':
                        # function for delivery info simplification 
                        filtered_product[field] = extract_delivery_date(product[field], "", "")
                    else:
                        filtered_product[field] = product[field]
            filtered_products.append(filtered_product)
    
    return {"amazon_products": filtered_products}

def extract_title_from_url(url):
    """
    Extract and format product title from Amazon URL.
    Extracts the part between 'amazon.com/' and '/dp' and removes dashes.
    
    Example: 
    https://www.amazon.com/LEGO-Star-Wars-Princess-Hologram/dp/B0DM6QJRZM
    Returns: "LEGO Star Wars Princess Hologram"
    """
    try:
        # Find the part between amazon.com/ and /dp
        start = url.find('amazon.com/') + len('amazon.com/')
        end = url.find('/dp')
        
        if start > len('amazon.com/') - 1 and end > start:
            # Extract the slug
            slug = url[start:end]
            # Replace dashes with spaces
            title = slug.replace('-', ' ')
            return title
        else:
            return None
    except:
        return None
    
def extract_delivery_date(delivery_info, info, sort_by):
    """
    Extract estimated delivery date from delivery info string.
    Example input: "FREE deliverySat, Nov 22on $35 of items shipped by AmazonOr fastest deliveryTomorrow, Nov 18"
    Returns a datetime object or None if parsing fails.
    """

    if not delivery_info:
        return []
    
    if not delivery_info:
        return []
    
    # Extract text between "FREE delivery" and "on"
    free_delivery_pattern = r'FREE delivery(.*?)on'
    free_delivery_matches = re.findall(free_delivery_pattern, delivery_info)
    
    # Extract everything after "fastest delivery"
    fastest_delivery_pattern = r'fastest delivery(.+?)(?=$|Or |FREE )'
    fastest_delivery_matches = re.findall(fastest_delivery_pattern, delivery_info)
    
    # Combine all matches
    all_dates = free_delivery_matches + fastest_delivery_matches
    
    # Clean up and process the matches
    cleaned_dates = []
    for match in all_dates:
        match = match.strip()
        
        # Remove "Tomorrow, " if present
        match = re.sub(r'^Tomorrow,\s*', '', match)
        
        # Check if it's a date range (e.g., "Dec 1 - 10")
        if ' - ' in match:
            # Split the range into two separate dates
            parts = match.split(' - ')
            if len(parts) == 2:
                # Extract month from the first part
                month_match = re.match(r'([A-Za-z]+)\s+(\d{1,2})', parts[0].strip())
                if month_match:
                    month = month_match.group(1)
                    start_day = month_match.group(2)
                    end_day = parts[1].strip()
                    
                    # Add both dates separately
                    cleaned_dates.append(f"{month} {start_day}")
                    cleaned_dates.append(f"{month} {end_day}")
                else:
                    cleaned_dates.append(match)
            else:
                cleaned_dates.append(match)
        else:
            cleaned_dates.append(match)
    
    # Parse date into ISO format (YYYY-MM-DD)
    if not cleaned_dates:
        return {"minDelivery": None, "maxDelivery": None}
    parsed_dates = []
    for date_str in cleaned_dates:
        new_date = dateparser.parse(date_str)
        if new_date:
            parsed_dates.append(new_date.strftime("%Y-%m-%d"))

    if not parsed_dates:
        return {"minDelivery": None, "maxDelivery": None}

    # Find the min and max dates to return to the func
    max_date = parsed_dates[0]
    for date in parsed_dates[1:]:
        if date > max_date:
            max_date = date

    min_date = parsed_dates[0]
    for date in parsed_dates[1:]:
        if date < min_date:
            min_date = date
        
    return {"minDelivery": min_date, "maxDelivery": max_date}

def main():
    # print(extract_delivery_date("FREE deliverySat, Nov 22on $35 of items shipped by AmazonOr fastest deliveryTomorrow, Nov 18", "", ""))
    # print(extract_delivery_date("FREE deliveryDec 1 - 10on $35 of items shipped by AmazonOr fastest deliveryDec 1 - 7", "", ""))
    # TEST INPUTS 
    product = "mario bros pushie"
    min_price = "10"
    max_price = "20"

    # INPUTS FOR THE QUERY ITSELF 
    querystring = {
        "query":product,
        "page":"1",
        "geo":"US",
        "min_price":min_price,
        "max_price":max_price,
        "sort_by":""
    }

    """
    "Sort By" options for the Amazon api 

    RELEVANCE - Most relevant results (usually default)
    PRICE_LOW_TO_HIGH - Cheapest products first
    PRICE_HIGH_TO_LOW - Most expensive products first
    BEST_SELLING - Best sellers/most popular
    NEWEST - Newest products first
    AVG_CUSTOMER_REVIEW - Highest rated products first
    """
    search_results_json = search_amazon(query=product, min_price=min_price, max_price=max_price, sort_by="")

    if search_results_json:
        filtered_data = filter_product_data(search_results_json, 5, fields=[
            "product_title",
            "product_url",
            "product_price",
            "product_photo",
            "product_star_rating",
            "is_prime", # tracks exclusivity
            "product_original_price",
            "product_delivery_info"
            ])
        
        print("\nFiltered Product Data (first 5 products):")
        print(json.dumps(filtered_data, indent=4))

        # Example of saving the filtered data
        with open(f"jsons/filtered_{product}.json", 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4, ensure_ascii=False)
        print(f"\nFiltered JSON data saved to jsons/filtered_{product}.json")

if __name__ == '__main__':
    main()