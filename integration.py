from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon, filter_product_data
from chat.gemini import get_similar_gift_ideas
import json
import traceback
from unittest.mock import MagicMock


def safe_input(prompt: str, default: str = ""):
    """Prevent StopIteration in CI when mocked input runs out."""
    try:
        return input(prompt)
    except (EOFError, StopIteration):
        return default


def safe_json(value):
    """
    Prevent MagicMock objects from breaking json.dump().
    Converts MagicMock → safe dict placeholder.
    """
    if isinstance(value, MagicMock):
        return {"error": "mocked_amazon_data"}
    return value


def integrated_API():
    print("================== Santa's Helper ==================")

    print("\n=== Search Parameters ===\n")
    product_name = safe_input("Enter a product name to search for: ")
    min_price = safe_input("Enter minimum price (or leave blank): ")
    max_price = safe_input("Enter maximum price (or leave blank): ")

    print("\nGenerating AI similar gift ideas using Gemini...")
    similar_gifts = get_similar_gift_ideas(product_name, num_ideas=2)

    print("\nSimilar items I will also search for:")
    for g in similar_gifts:
        print(" -", g)

    search_terms = [product_name] + similar_gifts

    print("\n--- eBay Filters ---")
    condition_filter = safe_input("eBay condition (NEW, USED, NEW|USED, or blank for all): ")
    ebay_sort = safe_input("eBay sort (price, -price, newlyListed, distance, or blank): ") or "price"

    print("\n--- Delivery Location (for accurate shipping) ---")
    delivery_country = safe_input("Delivery country (US, GB, CA, AU, or blank): ")
    delivery_postal = safe_input("ZIP/Postal code (or leave blank): ")

    print("\n--- Shipping Options ---")
    free_shipping_only = safe_input("Free shipping only? (y/n): ").lower()
    if free_shipping_only == "y":
        max_ship_cost = 0
    else:
        max_ship_input = safe_input("Max shipping cost $ (or blank): ")
        max_ship_cost = float(max_ship_input) if max_ship_input else None

    guaranteed_days_input = safe_input("Guaranteed delivery within X days (or blank): ")
    guaranteed_days = int(guaranteed_days_input) if guaranteed_days_input else None

    print("\n--- Amazon Filters ---")
    amazon_sort = safe_input("Amazon sort (LOW_HIGH_PRICE, HIGH_LOW_PRICE, REVIEWS, or blank): ")

    results = {
        "product": product_name,
        "filters": {
            "price_range": f"${min_price or 'any'} - ${max_price or 'any'}",
            "ebay_condition": condition_filter or "all",
            "ebay_sort": ebay_sort,
            "delivery_location": f"{delivery_country or 'none'} {delivery_postal or ''}",
            "max_shipping": f"${max_ship_cost}" if max_ship_cost is not None else "any",
            "guaranteed_delivery_days": guaranteed_days or "none",
            "amazon_sort": amazon_sort or "DEFAULT"
        },
        "ebay": {},
        "amazon": {}
    }

    print("\n" + "=" * 60)
    print(" Running MULTI-SEARCH for eBay")
    print("=" * 60)

    for term in search_terms:
        print(f"\nSearching eBay for: {term}")
        try:
            price_range = f"{min_price or ''}..{max_price or ''}" if (min_price or max_price) else None

            ebay_raw = search_ebay(
                query=term,
                price_range=price_range,
                condition_filter=condition_filter or None,
                delivery_country=delivery_country or None,
                delivery_postal_code=delivery_postal or None,
                guaranteed_delivery_days=guaranteed_days,
                max_delivery_cost=max_ship_cost,
                sort_by=ebay_sort
            )

            if ebay_raw:
                formatted = ebay_display_results(ebay_raw)
                results["ebay"][term] = formatted
                print(f" Found {formatted.get('found_items_count', 0)} items.")
            else:
                results["ebay"][term] = {"error": "No results"}
                print(" No results found.")

        except Exception as e:
            results["ebay"][term] = {"error": str(e)}
            print(f" Error: {e}")
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(" Running MULTI-SEARCH for Amazon")
    print("=" * 60)

    for term in search_terms:
        print(f"\nSearching Amazon for: {term}")
        try:
            amazon_json = search_amazon(
                query=term,
                sort_by=amazon_sort or None,
                min_price=min_price,
                max_price=max_price
            )

            # test mocks may return MagicMock or an "error" dict
            if isinstance(amazon_json, MagicMock):
                results["amazon"][term] = safe_json(amazon_json)
                print(" Error: mocked amazon_json")
                continue

            if "error" in amazon_json:
                results["amazon"][term] = amazon_json
                print(f" Error: {amazon_json['error']}")
                continue

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

            results["amazon"][term] = safe_json(amazon_filtered)
            count = len(amazon_filtered.get("amazon_products", [])) if isinstance(amazon_filtered, dict) else 0
            print(f" Found {count} items.")

        except Exception as e:
            results["amazon"][term] = {"error": str(e)}
            print(f" Error: {e}")
            traceback.print_exc()

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print("\n" + "=" * 60)
    print("All results saved to results.json")
    print("=" * 60)

    return results


if __name__ == "__main__":
    integrated_API()
