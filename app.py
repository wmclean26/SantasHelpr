"""
Flask web application for eBay and Amazon product search
"""

from flask import Flask, render_template, request, jsonify
from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon

app = Flask(__name__)


@app.route('/')
def index():
    """Render the main search page"""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """Handle search requests from the frontend"""
    try:
        # Get search parameters from request
        data = request.json
        product = data.get('product', '')
        min_price = data.get('min_price', '')
        max_price = data.get('max_price', '')
        condition = data.get('condition', '')
        sort_by = data.get('sort_by', 'price')
        amazon_sort = data.get('amazon_sort', 'RELEVANCE')
        
        # Delivery location
        country = data.get('country', '') or None
        postal = data.get('postal', '') or None
        
        # Shipping options
        max_ship = data.get('max_shipping', '')
        max_ship_cost = float(max_ship) if max_ship else None
        
        # Guaranteed delivery
        delivery_days = data.get('delivery_days', '')
        guaranteed_days = int(delivery_days) if delivery_days else None
        
        ebay_items = []
        amazon_items = []
        ebay_error = None
        amazon_error = None
        
        # Search eBay
        try:
            price_range = None
            if min_price or max_price:
                price_range = f"{min_price or ''}..{max_price or ''}"
            
            ebay_results = search_ebay(
                query=product,
                price_range=price_range,
                condition_filter=condition if condition else None,
                delivery_country=country,
                delivery_postal_code=postal,
                guaranteed_delivery_days=guaranteed_days,
                max_delivery_cost=max_ship_cost,
                sort_by=sort_by
            )
            
            if ebay_results:
                formatted = ebay_display_results(ebay_results)
                ebay_items = formatted.get("items", [])[:5]  # Limit to 5
        except Exception as e:
            ebay_error = str(e)
            print(f"eBay search error: {e}")
        
        # Search Amazon
        try:
            amazon_min_price = int(float(min_price)) if min_price else None
            amazon_max_price = int(float(max_price)) if max_price else None
            
            amazon_results = search_amazon(
                query=product,
                min_price=amazon_min_price,
                max_price=amazon_max_price,
                sort_by=amazon_sort if amazon_sort != "RELEVANCE" else None
            )
            
            if amazon_results:
                if "error" in amazon_results:
                    amazon_error = amazon_results['error']
                elif "products" in amazon_results:
                    amazon_items = amazon_results.get("products", [])[:5]  # Limit to 5
        except Exception as e:
            amazon_error = str(e)
            print(f"Amazon search error: {e}")
        
        return jsonify({
            'success': True,
            'ebay': {
                'items': ebay_items,
                'count': len(ebay_items),
                'error': ebay_error
            },
            'amazon': {
                'items': amazon_items,
                'count': len(amazon_items),
                'error': amazon_error
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
