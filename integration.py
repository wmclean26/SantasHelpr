from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon
import json


def integrated_API():
    """
    Searches both eBay and Amazon in one unified script
    """
    print("================== Santas Helper ==================")
    
    #search parameters
    product_name = input("Enter a product name to search for: ")
    min_price = input("Enter minimum price (or leave blank): ")
    max_price = input("Enter maximum price (or leave blank): ")
    sort_by = input("Enter Amazon sort by option (e.g., 'LOW_HIGH_PRICE', or leave blank): ")
    condition_filter = input("Enter eBay condition filter (NEW, USED, or leave blank for all): ")

    results = {
        "product": product_name,
        "ebay": {},
        "amazon": {}
    }
    
    print(" Running eBay API")
    print(f"   Searching for: {product_name} (${min_price}-${max_price})")
    try:
        ebay_raw = search_ebay(
            query=product_name,
            price_range=f"{min_price}..{max_price}",
            condition_filter=condition_filter
        )
        
        if ebay_raw:
            ebay_formatted = ebay_display_results(ebay_raw)
            results["ebay"] = ebay_formatted
            count = ebay_formatted.get("found_items_count", 0)
            print(f"    Success! Found {count} items\n")
        else:
            results["ebay"] = {"error": "No results"}
            print("    No results found\n")
            
    except Exception as e:
        results["ebay"] = {"error": str(e)}
        print(f"    Error: {e}\n")
    
    # Amazon call
    print(" Running Amazon API")
    print(f"   Searching for: {product_name}")
    try:
        amazon_results = search_amazon(
            query=product_name,
            sort_by=sort_by
        )
        
        if "error" in amazon_results:
            results["amazon"] = amazon_results
            print(f"   Error: {amazon_results['error']}\n")
        else:
            results["amazon"] = amazon_results
            count = len(amazon_results.get("results", []))
            print(f"   Success! Found {count} items\n")
            
    except Exception as e:
        results["amazon"] = {"error": str(e)}
        print(f"   Error: {e}\n")
    
    # Display Results Summary
    print("="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    # eBay Summary
    ebay_data = results["ebay"]
    if "error" in ebay_data:
        print(f"\neBay: {ebay_data['error']}")
    elif ebay_data.get("found_items_count", 0) > 0:
        count = ebay_data["found_items_count"]
        print(f"\n eBay: {count} items found")
        print("  First 3 items:")
        for i, item in enumerate(ebay_data["items"][:3], 1):
            print(f"    {i}. {item['title'][:60]}")
            print(f"       Price: {item['price']}, Condition: {item['condition']}")
    else:
        print("\neBay: No items found")
    
    # Amazon Summary
    amazon_data = results["amazon"]
    if "error" in amazon_data:
        print(f"\n Amazon: {amazon_data['error']}")
    elif len(amazon_data.get("products", [])) > 0:
        count = len(amazon_data["products"])
        print(f"\n Amazon: {count} items found")
        print("  First 3 items:")
        for i, item in enumerate(amazon_data["products"][:3], 1):
            title = item.get("product_title", "N/A")[:60]
            price = item.get("product_price", "N/A")
            print(f"    {i}. {title}")
            print(f"       Price: ${price}")
    else:
        print("\nAmazon: No items found")
    
    print("\n" + "="*60)
    
    # Save results to JSON file
    output_file = "results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\nFull results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    integrated_API()
