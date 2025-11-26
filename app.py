"""
Flask web application for eBay and Amazon product search
Integrated with AI keyword extraction and LLM-based similar gift recommendations
"""

from flask import Flask, render_template, request, jsonify
from EbayAPI.ebay_call import search_ebay, display_results as ebay_display_results
from RapidAmazon.rapidapi_amazon import search_amazon, filter_product_data
from RecommendationAlgorithm.Gift_keyword_extractor_final import GiftKeywordExtractor
from OutputParser.parse_products import compare
import traceback

app = Flask(__name__)

# Initialize the keyword extractor once at startup
keyword_extractor = GiftKeywordExtractor()

# Try to import LLM chat module (may not be available on all systems)
try:
    from chat.chat import get_similar_gift_ideas
    LLM_AVAILABLE = True
    print("✓ LLM module loaded successfully")
except Exception as e:
    LLM_AVAILABLE = False
    print(f"⚠ LLM module not available: {e}")
    print("  AI similar gift recommendations will be disabled")


def search_combined(query, min_price, max_price, condition, ebay_sort, amazon_sort,
                    country=None, postal=None, max_ship_cost=None, guaranteed_days=None):
    """
    Search both eBay and Amazon and return combined results in a format
    suitable for parse_products.compare()
    """
    combined_json = {
        "ebay": {"items": []},
        "amazon": {"amazon_products": []}
    }
    
    # Search eBay
    try:
        price_range = None
        if min_price or max_price:
            price_range = f"{min_price or ''}..{max_price or ''}"
        
        ebay_results = search_ebay(
            query=query,
            price_range=price_range,
            condition_filter=condition if condition else None,
            delivery_country=country,
            delivery_postal_code=postal,
            guaranteed_delivery_days=guaranteed_days,
            max_delivery_cost=max_ship_cost,
            sort_by=ebay_sort
        )
        
        if ebay_results:
            formatted = ebay_display_results(ebay_results)
            combined_json["ebay"]["items"] = formatted.get("items", [])[:10]
    except Exception as e:
        print(f"eBay search error for '{query}': {e}")
        combined_json["ebay"]["error"] = str(e)
    
    # Search Amazon
    try:
        amazon_min = int(float(min_price)) if min_price else None
        amazon_max = int(float(max_price)) if max_price else None
        
        amazon_results = search_amazon(
            query=query,
            min_price=amazon_min,
            max_price=amazon_max,
            sort_by=amazon_sort if amazon_sort != "RELEVANCE" else None
        )
        
        if amazon_results and "error" not in amazon_results:
            filtered = filter_product_data(
                amazon_results,
                max_items=10,
                fields=[
                    "product_title", "product_url", "product_price",
                    "product_photo", "product_star_rating", "is_prime",
                    "product_original_price", "product_delivery_info"
                ]
            )
            combined_json["amazon"]["amazon_products"] = filtered.get("amazon_products", [])
        elif amazon_results and "error" in amazon_results:
            combined_json["amazon"]["error"] = amazon_results["error"]
    except Exception as e:
        print(f"Amazon search error for '{query}': {e}")
        combined_json["amazon"]["error"] = str(e)
    
    return combined_json


@app.route('/')
def index():
    """Render the main search page"""
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    """
    Handle search requests from the frontend.
    Supports two modes:
    1. Filter mode: Uses provided filters directly
    2. Chat mode: Extracts filters from natural language
    
    Returns top 3 from original search AND top 3 from LLM similar items
    """
    try:
        data = request.json
        mode = data.get('mode', 'filter')  # 'filter' or 'chat'
        sort_criteria = data.get('sort_criteria', 'price')  # 'price', 'delivery', 'quality'
        
        # Extract parameters based on mode
        if mode == 'chat':
            # Chat mode: Extract keywords from natural language
            chat_input = data.get('chat_input', '')
            if not chat_input:
                return jsonify({'success': False, 'error': 'Please enter a gift description'}), 400
            
            # Use keyword extractor to parse natural language
            extracted = keyword_extractor.extract(chat_input)
            
            # Get parameters from extraction
            ebay_params = extracted['ebay_params']
            amazon_params = extracted['amazon_params']
            metadata = extracted['metadata']
            
            product = ebay_params['query']
            min_price = str(ebay_params['min_price']) if ebay_params['min_price'] else ''
            max_price = str(ebay_params['max_price']) if ebay_params['max_price'] else ''
            condition = ebay_params['condition'] or ''
            ebay_sort = 'price'
            amazon_sort = amazon_params.get('sort_by') or 'RELEVANCE'
            
            # Use defaults for other params in chat mode
            country = 'US'
            postal = None
            max_ship_cost = None
            guaranteed_days = None
            
            # Include extracted metadata in response
            extraction_info = {
                'detected_age': metadata.get('age'),
                'detected_relationship': metadata.get('relationship'),
                'detected_budget': metadata.get('budget'),
                'detected_categories': metadata.get('categories', []),
                'search_query': product
            }
        else:
            # Filter mode: Use filters directly
            product = data.get('product', '')
            min_price = data.get('min_price', '')
            max_price = data.get('max_price', '')
            condition = data.get('condition', '')
            ebay_sort = data.get('sort_by', 'price')
            amazon_sort = data.get('amazon_sort', 'RELEVANCE')
            country = data.get('country', '') or None
            postal = data.get('postal', '') or None
            max_ship = data.get('max_shipping', '')
            max_ship_cost = float(max_ship) if max_ship else None
            delivery_days = data.get('delivery_days', '')
            guaranteed_days = int(delivery_days) if delivery_days else None
            extraction_info = None
        
        if not product:
            return jsonify({'success': False, 'error': 'Please enter a product to search for'}), 400
        
        # ============ RUN #1: Original Search ============
        print(f"\n{'='*50}")
        print(f"Running original search for: {product}")
        print(f"{'='*50}")
        
        original_json = search_combined(
            query=product,
            min_price=min_price,
            max_price=max_price,
            condition=condition,
            ebay_sort=ebay_sort,
            amazon_sort=amazon_sort,
            country=country,
            postal=postal,
            max_ship_cost=max_ship_cost,
            guaranteed_days=guaranteed_days
        )
        
        # Get top 3 from original search
        original_top3 = compare(original_json, sort_criteria)
        
        # ============ RUN #2: LLM Similar Items Search ============
        similar_gifts = []
        similar_top3 = []
        llm_error = None
        
        if LLM_AVAILABLE:
            try:
                print(f"\n{'='*50}")
                print(f"Getting AI similar gift ideas for: {product}")
                print(f"{'='*50}")
                
                similar_gifts = get_similar_gift_ideas(product, num_ideas=3)
                print(f"Similar items: {similar_gifts}")
                
                # Search for each similar gift and combine results
                similar_combined_json = {
                    "ebay": {"items": []},
                    "amazon": {"amazon_products": []}
                }
                
                for gift in similar_gifts:
                    if gift and gift != "(no ideas found)":
                        gift_results = search_combined(
                            query=gift,
                            min_price=min_price,
                            max_price=max_price,
                            condition=condition,
                            ebay_sort=ebay_sort,
                            amazon_sort=amazon_sort,
                            country=country,
                            postal=postal,
                            max_ship_cost=max_ship_cost,
                            guaranteed_days=guaranteed_days
                        )
                        # Merge results
                        similar_combined_json["ebay"]["items"].extend(
                            gift_results.get("ebay", {}).get("items", [])
                        )
                        similar_combined_json["amazon"]["amazon_products"].extend(
                            gift_results.get("amazon", {}).get("amazon_products", [])
                        )
                
                # Get top 3 from similar items search
                if similar_combined_json["ebay"]["items"] or similar_combined_json["amazon"]["amazon_products"]:
                    similar_top3 = compare(similar_combined_json, sort_criteria)
                    
            except Exception as e:
                llm_error = str(e)
                print(f"LLM error: {e}")
                traceback.print_exc()
        else:
            llm_error = "LLM module not available on this system"
        
        # Build response
        response = {
            'success': True,
            'mode': mode,
            'search_term': product,
            'sort_criteria': sort_criteria,
            'original_results': {
                'top3': original_top3,
                'total_ebay': len(original_json.get('ebay', {}).get('items', [])),
                'total_amazon': len(original_json.get('amazon', {}).get('amazon_products', []))
            },
            'similar_results': {
                'similar_gifts': similar_gifts,
                'top3': similar_top3,
                'error': llm_error
            }
        }
        
        # Add extraction info if in chat mode
        if extraction_info:
            response['extraction_info'] = extraction_info
        
        return jsonify(response)
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/llm_status')
def llm_status():
    """Check if LLM is available"""
    return jsonify({'available': LLM_AVAILABLE})


if __name__ == '__main__':
    app.run(debug=True, port=5000)
