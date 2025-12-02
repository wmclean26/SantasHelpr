"""
Flask web application for eBay and Amazon product search
"""

from flask import Flask, render_template, request, jsonify
from int2 import integrated_API
from RecommendationAlgorithm.simple_nlp import SimpleNLPExtractor

app = Flask(__name__)

# Initialize NLP extractor for chat mode
nlp_extractor = SimpleNLPExtractor()


@app.route('/')
def index():
    """Render the main search page"""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """Handle search requests from the frontend - uses integrated API with LLM recommendations"""
    try:
        # Get search parameters from request
        data = request.json
        product = data.get('product', '')
        min_price = data.get('min_price', '') or None
        max_price = data.get('max_price', '') or None
        condition = data.get('condition', '') or None
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
        
        # Call the integrated API which uses LLM for similar recommendations
        result = integrated_API(
            product_name=product,
            min_price=min_price,
            max_price=max_price,
            condition_filter=condition,
            ebay_sort=sort_by,
            delivery_country=country,
            delivery_postal=postal,
            max_ship_cost=max_ship_cost,
            guaranteed_days=guaranteed_days,
            amazon_sort=amazon_sort if amazon_sort != "RELEVANCE" else None,
            comparison_criteria='price'
        )
        
        return jsonify({
            'success': True,
            'search_query': result.get('search_query', product),
            'filters': result.get('filters', {}),
            'products': result.get('products', []),
            'total_count': len(result.get('products', []))
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/chat-search', methods=['POST'])
def chat_search():
    """Handle chat-based natural language search requests"""
    try:
        data = request.json
        user_message = data.get('message', '')
        
        if not user_message.strip():
            return jsonify({'success': False, 'error': 'Please enter a search query'}), 400
        
        # Use NLP extractor to parse the natural language query
        extracted = nlp_extractor.extract(user_message)
        
        product = extracted['query']
        min_price = extracted['min_price']
        max_price = extracted['max_price']
        metadata = extracted['metadata']
        
        # Call the integrated API which uses LLM for similar recommendations
        result = integrated_API(
            product_name=product,
            min_price=str(min_price) if min_price else None,
            max_price=str(max_price) if max_price else None,
            condition_filter=None,
            ebay_sort='price',
            comparison_criteria='price'
        )
        
        return jsonify({
            'success': True,
            'extracted': {
                'query': product,
                'min_price': min_price,
                'max_price': max_price,
                'metadata': metadata
            },
            'search_query': result.get('search_query', product),
            'filters': result.get('filters', {}),
            'products': result.get('products', []),
            'total_count': len(result.get('products', []))
        })
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
