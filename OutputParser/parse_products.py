
import json
import argparse

def parse_price(price_str):
    """Cleans and converts a price string to a float."""
    if isinstance(price_str, str):
        price_str = price_str.replace('USD', '').replace('$', '').replace(',', '').strip()
        try:
            return float(price_str)
        except (ValueError, TypeError):
            return 0.0
    elif isinstance(price_str, (int, float)):
        return float(price_str)
    return 0.0

def calculate_quality_score(item):
    """Calculates a normalized quality score for an item."""
    if item['source'] == 'eBay':
        # eBay: 'New' is 1.0, 'Used' is 0.5, otherwise 0.0
        condition = item.get('condition', '').lower()
        if 'new' in condition:
            return 1.0
        elif 'used' in condition:
            return 0.5
        return 0.0
    elif item['source'] == 'Amazon':
        # Amazon: Normalize star rating (assuming 5-star max)
        rating_str = item.get('star_rating')
        if rating_str:
            try:
                rating = float(rating_str)
                return rating / 5.0
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    return 0.0

def get_top_products(file_path, sort_by='price', top_n=3, best_deal=False):
    """
    Parses a JSON file, gets top N from eBay and Amazon, combines them,
    and sorts by the specified key.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    ebay_products = []
    if 'ebay' in data and 'items' in data['ebay']:
        for item in data['ebay']['items']:
            product_info = {
                'source': 'eBay',
                'title': item.get('title'),
                'price': parse_price(item.get('price')),
                'condition': item.get('condition'),
                'url': item.get('link'),
            }
            product_info['quality_score'] = calculate_quality_score(product_info)
            ebay_products.append(product_info)

    amazon_products = []
    if 'amazon' in data and 'products' in data['amazon']:
        for product in data['amazon']['products']:
            product_info = {
                'source': 'Amazon',
                'title': product.get('product_title'),
                'price': parse_price(product.get('product_price')),
                'star_rating': product.get('product_star_rating'),
                'url': product.get('product_url'),
                'image': product.get('product_photo')
            }
            product_info['quality_score'] = calculate_quality_score(product_info)
            amazon_products.append(product_info)

    # Get top N from each source based on price (lowest first)
    top_ebay = sorted(ebay_products, key=lambda x: x['price'])[:top_n]
    top_amazon = sorted(amazon_products, key=lambda x: x['price'])[:top_n]

    combined_products = top_ebay + top_amazon

    if best_deal:
        # Calculate value score for the combined list
        max_price = max(p['price'] for p in combined_products if p['price'] > 0) or 1.0
        for product in combined_products:
            normalized_price = product['price'] / max_price if max_price > 0 else 0
            product['value_score'] = product['quality_score'] - normalized_price

        # Sort by value score
        combined_products.sort(key=lambda x: x['value_score'], reverse=True)

        # Ensure at least one from each vendor
        final_list = []
        ebay_added = False
        amazon_added = False
        for product in combined_products:
            if len(final_list) < top_n:
                if product['source'] == 'eBay' and not ebay_added:
                    final_list.append(product)
                    ebay_added = True
                elif product['source'] == 'Amazon' and not amazon_added:
                    final_list.append(product)
                    amazon_added = True
        
        for product in combined_products:
            if len(final_list) < top_n and product not in final_list:
                final_list.append(product)

        for product in final_list:
            if 'value_score' in product:
                del product['value_score']
        
        return final_list


    # Sort the combined list based on the user's choice
    if sort_by == 'quality':
        # Sort by quality score, descending
        combined_products.sort(key=lambda x: x['quality_score'], reverse=True)
    else: # Default to sorting by price
        # Sort by price, ascending (lowest first)
        combined_products.sort(key=lambda x: x['price'])
    return combined_products[:top_n]

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Parse and sort products from JSON file.')
    parser.add_argument('--sort-by', type=str, choices=['price', 'quality'], default='price',
                        help='The criteria to sort the combined products by (price or quality).')
    parser.add_argument('--best-deal', action='store_true',
                        help='Find the best overall deals (lowest price and best quality).')
    args = parser.parse_args()

    top_items = get_top_products('test.json', sort_by=args.sort_by, best_deal=args.best_deal)
    
    print(json.dumps(top_items, indent=4))
