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

# Cache for building data
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
    
    try:
        data = request.get_json()
        user_query = data.get('query', '')
        
        if not user_query:
            return jsonify({'success': False, 'error': 'No query provided'}), 400
        
        if building_cache is None:
            building_cache = fetch_calgary_buildings()
        
        # Process query with LLM
        filter_result = process_query(user_query)
        
        if not filter_result.get('success'):
            return jsonify(filter_result), 400
        
        # Apply filter to buildings
        filtered_ids = apply_filter(building_cache, filter_result['filter'])
        
        return jsonify({
            'success': True,
            'filter': filter_result['filter'],
            'matching_ids': filtered_ids,
            'count': len(filtered_ids)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def apply_filter(buildings, filter_obj):
    """Apply the parsed filter to building data."""
    attribute = filter_obj.get('attribute', '').lower()
    operator = filter_obj.get('operator', '')
    value = filter_obj.get('value')
    
    matching_ids = []
    
    # Map common attribute names
    attribute_map = {
        'height': 'height',
        'value': 'assessed_value',
        'assessed_value': 'assessed_value',
        'zoning': 'zoning',
        'zone': 'zoning',
        'type': 'building_type',
        'building_type': 'building_type'
    }
    
    actual_attribute = attribute_map.get(attribute, attribute)
    
    for building in buildings:
        building_value = building.get(actual_attribute)
        
        if building_value is None:
            continue
        
        try:
            # Handle numeric comparisons
            if operator in ['>', '<', '>=', '<=', '==', '!=']:
                building_num = float(building_value) if not isinstance(building_value, (int, float)) else building_value
                value_num = float(value)
                
                if operator == '>' and building_num > value_num:
                    matching_ids.append(building['id'])
                elif operator == '<' and building_num < value_num:
                    matching_ids.append(building['id'])
                elif operator == '>=' and building_num >= value_num:
                    matching_ids.append(building['id'])
                elif operator == '<=' and building_num <= value_num:
                    matching_ids.append(building['id'])
                elif operator == '==' and building_num == value_num:
                    matching_ids.append(building['id'])
                elif operator == '!=' and building_num != value_num:
                    matching_ids.append(building['id'])
            
            # Handle string matching (contains/equals)
            elif operator in ['contains', 'equals', '=']:
                building_str = str(building_value).lower()
                value_str = str(value).lower()
                
                if operator == 'contains' and value_str in building_str:
                    matching_ids.append(building['id'])
                elif operator in ['equals', '='] and building_str == value_str:
                    matching_ids.append(building['id'])
        
        except (ValueError, TypeError):
            continue
    
    return matching_ids

if __name__ == '__main__':
    app.run(debug=True, port=5000)