from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon
from chat import get_similar_gift_ideas
import json


def integrated_API():
    """
    Searches both eBay and Amazon for a product + similar AI-generated alternatives.
    """

    print("================== Santa's Helper ==================")
    print("\n=== Search Parameters ===\n")

    # Basic search parameters
    product_name = input("Enter a product name to search for: ")
    min_price = input("Enter minimum price (or leave blank): ")
    max_price = input("Enter maximum price (or leave blank): ")

    # Generate AI-similar gift ideas
    print("\nGenerating similar gift ideas using Phi-3 model...")
    similar_gifts = get_similar_gift_ideas(product_name, num_ideas=5)

    print("\nSimilar items I will also search for:")
    for g in similar_gifts:
        print(" -", g)

    search_terms = [product_name] + similar_gifts

    # eBay filters
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

    # Amazon filter
    print("\n--- Amazon Filters ---")
    amazon_sort = input("Amazon sort (LOW_HIGH_PRICE, HIGH_LOW_PRICE, REVIEWS, or blank): ")

    # Master results object
    results = {
        "product": product_name,
        "similar_gifts": similar_gifts,
        "filters": {
            "price_range": f"${min_price or 'any'} - ${max_price or 'any'}",
            "ebay_condition": condition_filter or "all",
            "ebay_sort": ebay_sort,
            "delivery_location": f"{delivery_country or 'none'} {delivery_postal or ''}",
            "max_shipping": f"${max_ship_cost}" if max_ship_cost is not None else "any",
            "guaranteed_delivery_days": guaranteed_days or "none",
        },
        "ebay": {},
        "amazon": {}
    }

    print("\n" + "=" * 60)
    print(" Running MULTI-SEARCH for eBay")
    print("=" * 60)

    # eBay search for each similar item
    for term in search_terms:
        print(f"\nSearching eBay for: {term}")

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
                sort_by=ebay_sort,
            )

            if ebay_raw:
                formatted = ebay_display_results(ebay_raw)
                results["ebay"][term] = formatted
                print(f"  Found {formatted.get('found_items_count', 0)} items.")
            else:
                results["ebay"][term] = {"error": "No results"}
                print("  No results.")

        except Exception as e:
            results["ebay"][term] = {"error": str(e)}
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print(" Running MULTI-SEARCH for Amazon")
    print("=" * 60)

    # Amazon search for each similar item
    for term in search_terms:
        print(f"\nSearching Amazon for: {term}")
        try:
            amazon_raw = search_amazon(query=term, sort_by=amazon_sort or None)

            if "error" in amazon_raw:
                results["amazon"][term] = amazon_raw
                print(f"  Error: {amazon_raw['error']}")
            else:
                results["amazon"][term] = amazon_raw
                print(f"  Found {len(amazon_raw.get('products', []))} items.")

        except Exception as e:
            results["amazon"][term] = {"error": str(e)}
            print(f"  Error: {e}")

    # Save results to file
    output_file = "results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("All results saved to results.json")
    print("=" * 60)

    return results


if __name__ == "__main__":
    integrated_API()
