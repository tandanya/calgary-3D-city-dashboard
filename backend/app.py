print("Starting imports...") 

from flask import Flask, jsonify, request
from flask_cors import CORS
print("Flask imported...")

from data_fetcher import fetch_calgary_buildings
print("data_fetcher imported...")

from llm_handler import process_query
print("llm_handler imported...")

import os
from dotenv import load_dotenv

load_dotenv()
print("Environment loaded...")

app = Flask(__name__)
CORS(app)
print("Flask app created...")

building_cache = None

@app.route('/api/buildings', methods=['GET'])
def get_buildings():
    """Fetch and return building data for Calgary."""
    global building_cache
    
    try:
        if building_cache is None:
            building_cache = fetch_calgary_buildings()
        
        return jsonify({
            'success': True,
            'data': building_cache,
            'count': len(building_cache)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/query', methods=['POST'])
def query_buildings():
    """Process natural language query and filter buildings."""
    global building_cache
    
    print("="*60)
    print("ROUTE /api/query HIT")
    print("="*60)
    
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        
        print(f"User query: '{user_query}'")
        
        if not user_query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400
        
        if building_cache is None:
            print("Loading building cache...")
            building_cache = fetch_calgary_buildings()
            print(f"Loaded {len(building_cache)} buildings")
        
        print("Calling process_query...")
        filter_result = process_query(user_query)
        print(f"Filter result: {filter_result}")
        
        if not filter_result.get('success'):
            return jsonify(filter_result), 400
        
        filter_data = filter_result.get('filter', {})
        
        print("Applying filter...")
        filtered_ids = apply_filter(building_cache, filter_data)
        print(f"Found {len(filtered_ids)} matching buildings")
        
        return jsonify({
            'success': True,
            'filter': filter_data,
            'matching_ids': filtered_ids,
            'count': len(filtered_ids),
            'source': filter_result.get('source', 'UNKNOWN')
        })
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def apply_filter(buildings, filter_obj):
    """Apply the parsed filter(s) to building data."""
    
    # Handle both single filter and multiple filters
    if 'filters' in filter_obj:
        filters = filter_obj['filters']
    else:
        filters = [filter_obj]
    
    print(f"Applying {len(filters)} filter(s): {filters}")
    
    # Map attribute names to actual data fields
    attribute_map = {
        'height': 'height',
        'value': 'assessed_value',
        'assessed_value': 'assessed_value',
        'zoning': 'zoning',
        'zone': 'zoning',
        'type': 'building_type',
        'building_type': 'building_type',
        'address': 'address',
        'street': 'address',
        'land_size': 'land_size_sf',
        'land_size_sf': 'land_size_sf',
        'lot_size': 'land_size_sf'
    }
    
    matching_ids = []
    
    for building in buildings:
        matches_all = True
        
        for f in filters:
            attribute = f.get('attribute', '').lower()
            operator = f.get('operator', '')
            value = f.get('value')
            
            actual_attribute = attribute_map.get(attribute, attribute)
            building_value = building.get(actual_attribute)
            
            if building_value is None:
                matches_all = False
                break
            
            try:
                # Numeric comparisons
                if operator in ['>', '<', '>=', '<=', '==', '!=']:
                    building_num = float(building_value) if not isinstance(building_value, (int, float)) else building_value
                    value_num = float(value)
                    
                    if operator == '>' and not (building_num > value_num):
                        matches_all = False
                    elif operator == '<' and not (building_num < value_num):
                        matches_all = False
                    elif operator == '>=' and not (building_num >= value_num):
                        matches_all = False
                    elif operator == '<=' and not (building_num <= value_num):
                        matches_all = False
                    elif operator == '==' and not (building_num == value_num):
                        matches_all = False
                    elif operator == '!=' and not (building_num != value_num):
                        matches_all = False
                
                # String matching
                elif operator in ['contains', 'equals', '=', 'endswith', 'startswith']:
                    building_str = str(building_value).upper()
                    value_str = str(value).upper()
                    
                    if operator == 'contains' and value_str not in building_str:
                        matches_all = False
                    elif operator in ['equals', '='] and building_str != value_str:
                        matches_all = False
                    elif operator == 'endswith' and not building_str.endswith(value_str):
                        matches_all = False
                    elif operator == 'startswith' and not building_str.startswith(value_str):
                        matches_all = False
            
            except (ValueError, TypeError):
                matches_all = False
                break
        
        if matches_all:
            matching_ids.append(building['id'])
    
    return matching_ids


if __name__ == '__main__':
    app.run(debug=True, port=5000)