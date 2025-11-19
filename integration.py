from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon, filter_product_data
import json


def integrated_API():
    """
    Searches both eBay and Amazon in one unified script with enhanced filters
    """
    print("================== Santas Helper ==================")
    print("\n=== Search Parameters ===\n")
    
    # Basic search parameters
    product_name = input("Enter a product name to search for: ")
    min_price = input("Enter minimum price (or leave blank): ")
    max_price = input("Enter maximum price (or leave blank): ")
    
    # eBay specific filters
    print("\n--- eBay Filters ---")
    condition_filter = input("eBay condition (NEW, USED, NEW|USED, or blank for all): ")
    ebay_sort = input("eBay sort (price, -price, newlyListed, distance, or blank for 'price'): ") or "price"
    
    # Delivery location
    print("\n--- Delivery Location (for accurate shipping) ---")
    delivery_country = input("Delivery country (US, GB, CA, AU, or blank): ")
    delivery_postal = input("ZIP/Postal code (for accurate shipping & delivery, or blank): ")
    
    # Shipping options
    print("\n--- Shipping Options ---")
    free_shipping_only = input("Free shipping only? (y/n, or blank): ").lower()
    if free_shipping_only == 'y':
        max_ship_cost = 0
    else:
        max_ship_input = input("Max shipping cost $ (or blank): ")
        max_ship_cost = float(max_ship_input) if max_ship_input else None
    
    guaranteed_days_input = input("Guaranteed delivery within X days (or blank): ")
    guaranteed_days = int(guaranteed_days_input) if guaranteed_days_input else None
    
    # Amazon sort
    print("\n--- Amazon Filters ---")
    amazon_sort = input("Amazon sort (LOW_HIGH_PRICE, HIGH_LOW_PRICE, REVIEWS, or blank): ")

    results = {
        "product": product_name,
        "filters": {
            "price_range": f"${min_price or 'any'} - ${max_price or 'any'}",
            "ebay_condition": condition_filter or "all",
            "ebay_sort": ebay_sort,
            "delivery_location": f"{delivery_country or 'none'} {delivery_postal or ''}",
            "max_shipping": f"${max_ship_cost}" if max_ship_cost is not None else "any",
            "guaranteed_delivery_days": guaranteed_days or "none"
        },
        "ebay": {},
        "amazon": {}
    }
    
    print("\n" + "="*60)
    print(" Running eBay API")
    print("="*60)
    print(f"   Searching: {product_name}")
    print(f"   Price: ${min_price or 'any'} - ${max_price or 'any'}")
    print(f"   Condition: {condition_filter or 'all'}")
    print(f"   Delivery: {delivery_country or 'generic'} {delivery_postal or ''}")
    print(f"   Max Shipping: ${max_ship_cost if max_ship_cost is not None else 'any'}")
    print(f"   Sort: {ebay_sort}")
    
    try:
        # Build price range
        price_range = None
        if min_price or max_price:
            price_range = f"{min_price or ''}..{max_price or ''}"
        
        ebay_raw = search_ebay(
            query=product_name,
            price_range=price_range,
            condition_filter=condition_filter if condition_filter else None,
            delivery_country=delivery_country if delivery_country else None,
            delivery_postal_code=delivery_postal if delivery_postal else None,
            guaranteed_delivery_days=guaranteed_days,
            max_delivery_cost=max_ship_cost,
            sort_by=ebay_sort
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
        import traceback
        traceback.print_exc()
    
    # Amazon call
    print("="*60)
    print(" Running Amazon API")
    print("="*60)
    print(f"   Searching: {product_name}")
    print(f"   Sort: {amazon_sort or 'RELEVANCE'}")
    
    try:
        amazon_json = search_amazon(
            query=product_name,
            sort_by=amazon_sort if amazon_sort else None,
            min_price=min_price,
            max_price=max_price
        )

        if "error" in amazon_json:
            results["amazon"] = amazon_json
            print(f"   Error: {amazon_json['error']}\n")
    
        else:
            amazon_results = filter_product_data(amazon_json, 5, fields=[
                "product_title",
                "product_url",
                "product_price",
                "product_photo",
                "product_star_rating",
                "is_prime", # tracks exclusivity
                "product_original_price",
                "product_delivery_info"
                ])
        
            if "error" in amazon_results:
                results["amazon"] = amazon_results
                print(f"   Error: {amazon_results['error']}\n")
            else:
                results["amazon"] = amazon_results
                count = len(amazon_results.get("amazon_products", []))
                print(f"   Success! Found {count} items\n")
            
    except Exception as e:
        results["amazon"] = {"error": str(e)}
        print(f"   Error: {e}\n")
    
    # Display Results Summary
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    # eBay Summary
    ebay_data = results["ebay"]
    if "error" in ebay_data:
        print(f"\n eBay: {ebay_data['error']}")
    elif ebay_data.get("found_items_count", 0) > 0:
        count = ebay_data["found_items_count"]
        print(f"\n eBay: {count} items found")
        print("-" * 60)
        for i, item in enumerate(ebay_data["items"][:3], 1):
            print(f"\n  {i}. {item['title'][:65]}")
            print(f"     Price: {item['price']}")
            
            # Show discount if available
            if item.get('market_price', {}).get('discount_percentage'):
                original = item['market_price'].get('original')
                discount = item['market_price'].get('discount_percentage')
                print(f"      DISCOUNT: {discount}% off (was ${original})")
            
            # Show condition and location
            print(f"     Condition: {item['condition']}")
            print(f"     Location: {item.get('itemLocation', 'N/A')}")
            
            # Show shipping
            shipping_opts = item.get('shippingOptions', [])
            if shipping_opts and shipping_opts[0]:
                cost = shipping_opts[0].get('cost', 'N/A')
                if cost == '0.0' or cost == 0:
                    print(f"      Shipping: FREE")
                else:
                    print(f"      Shipping: ${cost}")
                
                # Show delivery estimate if available
                min_del = shipping_opts[0].get('minDelivery', '')
                max_del = shipping_opts[0].get('maxDelivery', '')
                if min_del:
                    print(f"      Estimated Delivery: {min_del[:10]} to {max_del[:10]}")
            
            # Show seller rating
            if item.get('seller_feedbackPercentage') != 'N/A':
                print(f"      Seller Rating: {item['seller_feedbackPercentage']}%")
            
            # Show images count
            images = item.get("images", [])
            img_count = len([i for i in images if i])
            if img_count > 0:
                print(f"       Images: {img_count} available")
                print(f"     First Image: {images[0][:80]}...")
            
            print(f"      URL: {item.get('url', 'N/A')}")
    else:
        print("\n eBay: No items found")
    
    # Amazon Summary
    amazon_data = results["amazon"]
    if "error" in amazon_data:
        print(f"\n Amazon: {amazon_data['error']}")
    elif len(amazon_data.get("amazon_products", [])) > 0:
        count = len(amazon_data["amazon_products"])
        print(f"\n Amazon: {count} items found")
        print("-" * 60)
        for i, item in enumerate(amazon_data["amazon_products"][:3], 1):
            title = item.get("product_title", "N/A")[:65]
            price = item.get("product_price", "N/A")
            print(f"\n  {i}. {title}")
            print(f"     Price: ${price}")
            
            # Show rating if available
            if item.get('product_star_rating'):
                print(f"      Rating: {item['product_star_rating']} stars ({item.get('product_num_ratings', 'N/A')} reviews)")
            
            # Show prime status
            if item.get('is_prime'):
                print(f"      Prime: Yes")
            
            # Show image
            if item.get('product_photo'):
                print(f"       Image: {item['product_photo'][:80]}...")
            
            print(f"      URL: {item.get('product_url', 'N/A')}")
    else:
        print("\n Amazon: No items found")
    
    print("\n" + "="*60)
    print("\n Applied Filters:")
    print(f"   Price Range: {results['filters']['price_range']}")
    print(f"   eBay Condition: {results['filters']['ebay_condition']}")
    print(f"   eBay Sort: {results['filters']['ebay_sort']}")
    print(f"   Delivery Location: {results['filters']['delivery_location']}")
    print(f"   Max Shipping: {results['filters']['max_shipping']}")
    if results['filters']['guaranteed_delivery_days'] != 'none':
        print(f"   Guaranteed Delivery: {results['filters']['guaranteed_delivery_days']} days")
    print("="*60)
    
    # Save results to JSON file
    output_file = "test.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"\nFull results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    integrated_API()