
import requests
from dotenv import load_dotenv
import os 
import json 

load_dotenv()

x_rapidapi_key = os.getenv("RAPID_API_KEY")
x_rapidapi_host = os.getenv("RAPID_API_HOST")

url = "https://amazon-online-data-api.p.rapidapi.com/search"

product = "power rangers action figure"
min_price = "10"
max_price = "20"

querystring = {
    "query":product,
    "page":"1",
    "geo":"US",
    "min_price":min_price,
    "max_price":max_price,
    "sort_by":""
}

"""
"Sort By" options for the Amaazon api 

RELEVANCE - Most relevant results (usually default)
PRICE_LOW_TO_HIGH - Cheapest products first
PRICE_HIGH_TO_LOW - Most expensive products first
BEST_SELLING - Best sellers/most popular
NEWEST - Newest products first
AVG_CUSTOMER_REVIEW - Highest rated products first
"""

headers = {
	"x-rapidapi-key": x_rapidapi_key,
	"x-rapidapi-host": x_rapidapi_host
}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())

filename = f"{product}.json"

with open(filename, 'w', encoding='utf-8') as f:
    json.dump(response.json(), f, indent=4, ensure_ascii=False)
    
print()
print(f"JSON data saved to {filename}")