import json
from datetime import datetime

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

def quality_score(product):
    """Calculates a normalized quality score for a product (0.0 to 1.0)."""
    if product['source'] == 'eBay':
        condition = product.get('condition', '').lower()
        if 'new' in condition:
            return 1.0
        elif 'used' in condition:
            return 0.5
        return 0.0
    elif product['source'] == 'Amazon':
        rating_str = product.get('star_rating')
        if rating_str:
            try:
                rating = float(rating_str)
                return rating / 5.0
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    return 0.0

def compare(json_data, sort_by, top_n=3, ensure_both_sources=True):
    """
    Compare and sort products from JSON data.
    
    Args:
        json_data: Dict containing ebay and amazon product data
        sort_by: String - 'price', 'delivery', or 'quality'
        top_n: Int - Number of top products to return (default: 3)
        ensure_both_sources: Bool - If True and top_n >= 2, ensures at least one from each source (default: True)
    
    Returns:
        List of top N products based on sort criteria
    """
    all_products = []

    # Process eBay products
    if 'ebay' in json_data and 'items' in json_data['ebay']:
        for item in json_data['ebay']['items']:
            shipping_info = item.get('shippingOptions', [])
            delivery_info = shipping_info[0] if shipping_info else None
            
            # Extract min delivery date (ignore time)
            min_delivery_date = None
            if delivery_info and 'minDelivery' in delivery_info:
                try:
                    min_delivery_str = delivery_info['minDelivery']
                    min_delivery_date = datetime.fromisoformat(min_delivery_str.replace('Z', '+00:00')).date()
                except:
                    pass
            
            product_info = {
                'source': 'eBay',
                'title': item.get('title'),
                'price': parse_price(item.get('price')),
                'condition': item.get('condition'),
                'url': item.get('url'),
                'min_delivery_date': min_delivery_date
            }
            all_products.append(product_info)

    # Process Amazon products
    if 'amazon' in json_data and 'amazon_products' in json_data['amazon']:
        for product in json_data['amazon']['amazon_products']:
            delivery_info = product.get('product_delivery_info')
            
            # Extract min delivery date (ignore time)
            min_delivery_date = None
            if delivery_info and 'minDelivery' in delivery_info:
                try:
                    min_delivery_str = delivery_info['minDelivery']
                    min_delivery_date = datetime.strptime(min_delivery_str, '%Y-%m-%d').date()
                except:
                    pass
            
            product_info = {
                'source': 'Amazon',
                'title': product.get('product_title'),
                'price': parse_price(product.get('product_price')),
                'star_rating': product.get('product_star_rating'),
                'url': product.get('product_url'),
                'image': product.get('product_photo'),
                'min_delivery_date': min_delivery_date
            }
            all_products.append(product_info)

    # Sort based on sort_by parameter
    if sort_by == 'price':
        # Sort by lowest price
        all_products.sort(key=lambda x: x['price'])
    elif sort_by == 'delivery':
        # Sort by earliest delivery date (None values go to end)
        all_products.sort(key=lambda x: (x['min_delivery_date'] is None, x['min_delivery_date']))
    elif sort_by == 'quality':
        # Calculate quality scores and sort
        for product in all_products:
            product['quality_score'] = quality_score(product)
        all_products.sort(key=lambda x: x['quality_score'], reverse=True)
    
    final_list = []
    
    # If top_n is 1 or ensure_both_sources is False, just take top N
    if top_n == 1 or not ensure_both_sources:
        final_list = all_products[:top_n]
    else:
        # Ensure at least one from each source (eBay and Amazon) when top_n >= 2
        ebay_added = False
        amazon_added = False
        
        # First pass: add at least one from each source
        for product in all_products:
            if len(final_list) >= top_n:
                break
            if product['source'] == 'eBay' and not ebay_added:
                final_list.append(product)
                ebay_added = True
            elif product['source'] == 'Amazon' and not amazon_added:
                final_list.append(product)
                amazon_added = True
        
        # Second pass: fill remaining slots
        for product in all_products:
            if len(final_list) >= top_n:
                break
            if product not in final_list:
                final_list.append(product)
    
    # Convert dates to strings for JSON serialization
    for product in final_list:
        if product.get('min_delivery_date'):
            product['min_delivery_date'] = str(product['min_delivery_date'])
    
    # Return top N products
    return final_list

def main():
    """Main function to load JSON and compare products."""
    # Load JSON from file
    with open('test.json', 'r') as f:
        json_data = json.load(f)
    
    # Configure parameters
    sort_by = 'price'  # 'price', 'delivery', or 'quality'
    top_n = 1 # Number of results to return (1, 3, 5, etc.)
    ensure_both_sources = True  # Ensure at least one from each source
    
    # Get top N products
    top_products = compare(json_data, sort_by, top_n, ensure_both_sources)
    
    # Print results
    print(json.dumps(top_products, indent=4))
    
    return top_products

if __name__ == '__main__':
    main()