from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon, filter_product_data
from chat.gemini import get_similar_gift_ideas
from OutputParser.parse_products import compare  # Import the compare function
import json
import traceback

def integrated_API(
    product_name,
    min_price=None,
    max_price=None,
    condition_filter=None,
    ebay_sort="price",
    delivery_country=None,
    delivery_postal=None,
    max_ship_cost=None,
    guaranteed_days=None,
    amazon_sort=None,
    comparison_criteria='price'  # New parameter for comparison
):
    """
    Integrated multiple search across eBay + Amazon based on AI similar gift ideas.
    
    Args:
        product_name (str): Product to search for
        min_price (str, optional): Minimum price
        max_price (str, optional): Maximum price
        condition_filter (str, optional): eBay condition (NEW, USED, NEW|USED)
        ebay_sort (str, optional): eBay sort (price, -price, newlyListed, distance). Default: "price"
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
                    "product_delivery_info",
                    "asin",
                    "sales_volume",
                    "product_availability",
                    "product_num_ratings"
                ]
            )
            main_results_amazon = amazon_filtered
            count = len(amazon_filtered.get("amazon_products", []))
            print(f" Found {count} items.")

    except Exception as e:
        main_results_amazon = {"error": str(e)}
        print(f" Error: {e}")
        traceback.print_exc()

    # Get top 3 main products using compare function
    print("\n" + "=" * 60)
    print(f" Selecting TOP 3 products for: {product_name}")
    print("=" * 60)
    
    main_combined = {
        "ebay": main_results_ebay,
        "amazon": main_results_amazon
    }
    
    top_3_main = compare(main_combined, comparison_criteria, top_n=3, ensure_both_sources=True)
    
    print(f"\nTop 3 products selected:")
    for idx, prod in enumerate(top_3_main, 1):
        title = prod.get('title') or prod.get('product_title', 'Unknown')
        price = prod.get('price', 'N/A')
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
                        "product_delivery_info",
                        "asin",
                        "sales_volume",
                        "product_availability",
                        "product_num_ratings"
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
        
        top_1_similar = compare(similar_combined, comparison_criteria, top_n=1, ensure_both_sources=False)
        
        if top_1_similar:
            top_product = top_1_similar[0]
            top_product['search_term'] = term  # Add the search term for reference
            similar_top_products.append(top_product)
            
            title = top_product.get('title') or top_product.get('product_title', 'Unknown')
            price = top_product.get('price', 'N/A')
            source = top_product.get('source', 'Unknown')
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
    
    # Add top 3 main products
    for idx, product in enumerate(top_3_main, 1):
        product['rank'] = idx
        product['product_type'] = 'main'
        final_combined_results["products"].append(product)
    
    # Add top 2 similar products
    for idx, product in enumerate(similar_top_products, 4):
        product['rank'] = idx
        product['product_type'] = 'similar'
        final_combined_results["products"].append(product)

    # Save combined top 5 results
    combined_output_file = "top_5_products.json"
    with open(combined_output_file, "w", encoding="utf-8") as f:
        json.dump(final_combined_results, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Top 5 combined products saved to {combined_output_file}")
    print("=" * 60)
    
    print("\n" + "=" * 60)
    print(" FINAL TOP 5 PRODUCTS")
    print("=" * 60)
    for product in final_combined_results["products"]:
        rank = product.get('rank')
        prod_type = product.get('product_type')
        source = product.get('source')
        title = product.get('title') or product.get('product_title', 'Unknown')
        price = product.get('price', 'N/A')
        search_term = product.get('search_term', product_name)
        print(f"{rank}. [{prod_type.upper()}] [{source}] {title[:50]}...")
        print(f"   Price: ${price} | Search: {search_term}")

    return final_combined_results


if __name__ == "__main__":
    # Example usage
    result = integrated_API(
        product_name="power rangers",
        min_price="10",
        max_price="50",
        condition_filter="NEW",
        delivery_country="US",
        delivery_postal="10001",
        max_ship_cost=0,  # Free shipping only
        amazon_sort="LOW_HIGH_PRICE",
        comparison_criteria="price"  # Can be 'price', 'delivery', or 'quality'
    )