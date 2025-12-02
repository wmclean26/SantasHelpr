from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon, filter_product_data
from chat.gemini import get_similar_gift_ideas
from OutputParser.parse_products import compare  # Import the compare function
import json
import traceback

def standardize_product(product, source):
    """
    Standardize product data format between eBay and Amazon.
    
    Args:
        product: Raw product dict from eBay or Amazon
        source: 'eBay' or 'Amazon'
    
    Returns:
        Standardized product dict with consistent fields
    """
    if source == 'eBay':
        return {
            'source': 'eBay',
            'title': product.get('title'),
            'description': product.get('description'),
            'url': product.get('url'),
            'images': product.get('images', []),
            'price': product.get('price'),
            'condition': product.get('condition'),
            'categories': product.get('categories', []),
            'itemLocation': product.get('itemLocation'),
            'shippingOptions': product.get('shippingOptions', []),
            'seller_feedbackPercentage': product.get('seller_feedbackPercentage'),
            'watchCount': product.get('watchCount'),
            'itemCreationDate': product.get('itemCreationDate'),
            'market_price': product.get('market_price', {})
        }
    elif source == 'Amazon':
        return {
            'source': 'Amazon',
            'product_title': product.get('product_title'),
            'product_url': product.get('product_url'),
            'product_price': product.get('product_price'),
            'product_photo': product.get('product_photo'),
            'product_star_rating': product.get('product_star_rating'),
            'is_prime': product.get('is_prime'),
            'product_original_price': product.get('product_original_price'),
            'product_delivery_info': product.get('product_delivery_info')
        }
    return product

def integrated_API(
    product_name,
    min_price=None,
    max_price=None,
    condition_filter=None,
    ebay_sort="distance",
    delivery_country=None,
    delivery_postal=None,
    max_ship_cost=None,
    guaranteed_days=None,
    amazon_sort="LOW_HIGH_PRICE",
    comparison_criteria='price'  # New parameter for comparison
):
    """
    Integrated multiple search across eBay + Amazon based on AI similar gift ideas.
    
    Args:
        product_name (str): Product to search for
        min_price (str, optional): Minimum price
        max_price (str, optional): Maximum price
        condition_filter (str, optional): eBay condition (NEW, USED, NEW|USED)
        ebay_sort (str, optional): eBay sort (price, -price, newlyListed, distance). Default: "distance"
        delivery_country (str, optional): Delivery country (US, GB, CA, AU)
        delivery_postal (str, optional): ZIP/Postal code
        max_ship_cost (float, optional): Max shipping cost (0 for free shipping only)
        guaranteed_days (int, optional): Guaranteed delivery within X days
        amazon_sort (str, optional): Amazon sort (LOW_HIGH_PRICE, HIGH_LOW_PRICE, REVIEWS)
        comparison_criteria (str, optional): Comparison criteria ('price', 'delivery', 'quality'). Default: 'price'
    
    Returns:
        dict: Combined results with top 3 main products and top 1 from each similar product
    """
    
    print("================== Santa's Helper ==================")
    print(f"\nSearching for: {product_name}")
    print(f"Comparison criteria: {comparison_criteria}")

    # Similar gift ideas from LLM
    print("\nGenerating AI similar gift ideas using Gemini...")
    similar_gifts = get_similar_gift_ideas(product_name, num_ideas=2)

    print("\nSimilar items I will also search for:")
    for g in similar_gifts:
        print(" -", g)

    # Store all results
    main_results_ebay = {}
    main_results_amazon = {}
    similar_results_ebay = {}
    similar_results_amazon = {}

    print("\n" + "=" * 60)
    print(f" Searching MAIN PRODUCT: {product_name}")
    print("=" * 60)

    # Search main product on eBay
    print(f"\nSearching eBay for: {product_name}")
    try:
        price_range = None
        if min_price or max_price:
            price_range = f"{min_price or ''}..{max_price or ''}"

        ebay_raw = search_ebay(
            query=product_name,
            price_range=price_range,
            condition_filter=condition_filter if condition_filter else None,
            delivery_country=delivery_country or None,
            delivery_postal_code=delivery_postal or None,
            guaranteed_delivery_days=guaranteed_days,
            max_delivery_cost=max_ship_cost,
            sort_by=ebay_sort
        )

        if ebay_raw:
            formatted = ebay_display_results(ebay_raw)
            main_results_ebay = formatted
            print(f" Found {formatted.get('found_items_count', 0)} items.")
        else:
            main_results_ebay = {"error": "No results"}
            print(" No results found.")

    except Exception as e:
        main_results_ebay = {"error": str(e)}
        print(f" Error: {e}")
        traceback.print_exc()

    # Search main product on Amazon
    print(f"\nSearching Amazon for: {product_name}")
    try:
        amazon_json = search_amazon(
            query=product_name,
            sort_by=amazon_sort or None,
            min_price=min_price,
            max_price=max_price
        )

        if "error" in amazon_json:
            main_results_amazon = amazon_json
            print(f" Error: {amazon_json['error']}")
        else:
            amazon_filtered = filter_product_data(
                amazon_json,
                max_products=5,
                fields=[
                    "product_title",
                    "product_url",
                    "product_price",
                    "product_photo",
                    "product_star_rating",
                    "is_prime",
                    "product_original_price",
                    "product_delivery_info"
                ]
            )
            main_results_amazon = amazon_filtered
            count = len(amazon_filtered.get("amazon_products", []))
            print(f" Found {count} items.")

    except Exception as e:
        main_results_amazon = {"error": str(e)}
        print(f" Error: {e}")
        traceback.print_exc()

    # DEBUG: Print what we're sending to compare
    print("\n[DEBUG] eBay items count:", len(main_results_ebay.get('items', [])))
    print("[DEBUG] Amazon items count:", len(main_results_amazon.get('amazon_products', [])))
    
    # Get top 3 main products using compare function
    print("\n" + "=" * 60)
    print(f" Selecting TOP 3 products for: {product_name}")
    print("=" * 60)
    
    main_combined = {
        "ebay": main_results_ebay,
        "amazon": main_results_amazon
    }
    
    top_3_main = compare(main_combined, comparison_criteria, top_n=3, ensure_both_sources=True)
    
    # DEBUG: Print what compare returned
    print(f"\n[DEBUG] Compare returned {len(top_3_main)} products:")
    for prod in top_3_main:
        print(f"  - Source: {prod.get('source')}, Title: {prod.get('title') or prod.get('product_title', 'N/A')}")
    
    # Standardize the top 3 products
    standardized_top_3 = []
    for prod in top_3_main:
        source = prod.get('source')
        # Find the original product with all fields
        if source == 'eBay':
            for item in main_results_ebay.get('items', []):
                if item.get('title') == prod.get('title') or item.get('url') == prod.get('url'):
                    standardized_top_3.append(standardize_product(item, 'eBay'))
                    break
        elif source == 'Amazon':
            for item in main_results_amazon.get('amazon_products', []):
                if (item.get('product_title') == prod.get('product_title') or 
                    item.get('product_url') == prod.get('url')):
                    standardized_top_3.append(standardize_product(item, 'Amazon'))
                    break
    
    print(f"\nTop 3 products selected:")
    for idx, prod in enumerate(standardized_top_3, 1):
        title = prod.get('title') or prod.get('product_title', 'Unknown')
        price = prod.get('price') or prod.get('product_price', 'N/A')
        source = prod.get('source', 'Unknown')
        print(f"  {idx}. [{source}] {title[:50]}... - ${price}")

    print("\n" + "=" * 60)
    print(" Searching SIMILAR PRODUCTS (1 per similar gift)")
    print("=" * 60)

    # Store top 1 from each similar product
    similar_top_products = []

    # Search similar products (1 product each from eBay and Amazon)
    for term in similar_gifts:
        print(f"\n--- Similar Gift: {term} ---")
        
        ebay_similar = {}
        amazon_similar = {}
        
        # eBay - Get just 1 product
        print(f"Searching eBay for: {term}")
        try:
            price_range = None
            if min_price or max_price:
                price_range = f"{min_price or ''}..{max_price or ''}"

            ebay_raw = search_ebay(
                query=term,
                price_range=price_range,
                condition_filter=condition_filter if condition_filter else None,
                delivery_country=delivery_country or None,
                delivery_postal_code=delivery_postal or None,
                guaranteed_delivery_days=guaranteed_days,
                max_delivery_cost=max_ship_cost,
                sort_by=ebay_sort
            )

            if ebay_raw:
                formatted = ebay_display_results(ebay_raw)
                # Take only the first item
                if formatted.get('items') and len(formatted['items']) > 0:
                    ebay_similar = {
                        "found_items_count": 1,
                        "items": [formatted['items'][0]]
                    }
                    print(f" Found 1 item.")
                else:
                    ebay_similar = {"error": "No results"}
                    print(" No results found.")
            else:
                ebay_similar = {"error": "No results"}
                print(" No results found.")

        except Exception as e:
            ebay_similar = {"error": str(e)}
            print(f" Error: {e}")
            traceback.print_exc()

        # Amazon - Get just 1 product
        print(f"Searching Amazon for: {term}")
        try:
            amazon_json = search_amazon(
                query=term,
                sort_by=amazon_sort or None,
                min_price=min_price,
                max_price=max_price
            )

            if "error" in amazon_json:
                amazon_similar = amazon_json
                print(f" Error: {amazon_json['error']}")
            else:
                amazon_filtered = filter_product_data(
                    amazon_json,
                    max_products=1,  # Only get 1 product
                    fields=[
                        "product_title",
                        "product_url",
                        "product_price",
                        "product_photo",
                        "product_star_rating",
                        "is_prime",
                        "product_original_price",
                        "product_delivery_info"
                    ]
                )
                amazon_similar = amazon_filtered
                count = len(amazon_filtered.get("amazon_products", []))
                print(f" Found {count} item(s).")

        except Exception as e:
            amazon_similar = {"error": str(e)}
            print(f" Error: {e}")
            traceback.print_exc()
        
        # Get top 1 from this similar product
        similar_combined = {
            "ebay": ebay_similar,
            "amazon": amazon_similar
        }
        
        top_1_similar = compare(similar_combined, comparison_criteria, top_n=1, ensure_both_sources=True)
        
        if top_1_similar:
            top_product = top_1_similar[0]
            source = top_product.get('source')
            
            # Find and standardize the original product with all fields
            standardized_product = None
            if source == 'eBay':
                items = ebay_similar.get('items', [])
                if items:
                    standardized_product = standardize_product(items[0], 'eBay')
            elif source == 'Amazon':
                items = amazon_similar.get('amazon_products', [])
                if items:
                    standardized_product = standardize_product(items[0], 'Amazon')
            
            if standardized_product:
                standardized_product['search_term'] = term
                similar_top_products.append(standardized_product)
                
                title = standardized_product.get('title') or standardized_product.get('product_title', 'Unknown')
                price = standardized_product.get('price') or standardized_product.get('product_price', 'N/A')
                print(f"\n🏆 Best for {term}: [{source}] {title[:40]}... - ${price}")

    # Combine top 3 main + top 2 similar into final result
    final_combined_results = {
        "search_query": product_name,
        "filters": {
            "price_range": f"${min_price or 'any'} - ${max_price or 'any'}",
            "ebay_condition": condition_filter or "all",
            "ebay_sort": ebay_sort,
            "delivery_location": f"{delivery_country or 'none'} {delivery_postal or ''}",
            "max_shipping": f"${max_ship_cost}" if max_ship_cost is not None else "any",
            "guaranteed_delivery_days": guaranteed_days or "none",
            "amazon_sort": amazon_sort or "DEFAULT",
            "comparison_criteria": comparison_criteria
        },
        "comparison_criteria": comparison_criteria,
        "products": []
    }
    
    # Add top 3 main products with all their original fields
    for idx, product in enumerate(standardized_top_3, 1):
        product['rank'] = idx
        product['product_type'] = 'main'
        final_combined_results["products"].append(product)
    
    # Add top 2 similar products with all their original fields
    for idx, product in enumerate(similar_top_products, 4):
        product['rank'] = idx
        product['product_type'] = 'similar'
        final_combined_results["products"].append(product)

    # Save combined top 5 results
    output_file = "final_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(final_combined_results, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Top 5 combined products saved to {output_file}")
    print("=" * 60)
    
    print("\n" + "=" * 60)
    print(" FINAL TOP 5 PRODUCTS")
    print("=" * 60)
    for product in final_combined_results["products"]:
        rank = product.get('rank')
        prod_type = product.get('product_type')
        source = product.get('source')
        title = product.get('title') or product.get('product_title', 'Unknown')
        price = product.get('price') or product.get('product_price', 'N/A')
        search_term = product.get('search_term', product_name)
        print(f"{rank}. [{prod_type.upper()}] [{source}] {title[:50]}...")
        print(f"   Price: ${price} | Search: {search_term}")

    return final_combined_results


if __name__ == "__main__":
    # Example usage
    result = integrated_API(
        product_name="power rangers",
        min_price=10
    )