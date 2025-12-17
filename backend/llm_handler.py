import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.environ.get('HUGGINGFACE_API_KEY')

if not HF_TOKEN:
    raise ValueError("No HuggingFace token found. Set HF_TOKEN in your .env file")

API_URL = "https://router.huggingface.co/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    return response.json()

def process_query(user_query):
    """
    Process natural language query using HuggingFace Router API.
    Returns a filter object for the building data.
    """
    
    print(f"\n{'='*60}")
    print(f"LLM Query Processing")
    print(f"{'='*60}")
    print(f"User Query: '{user_query}'")
    
    system_prompt = """You are a query parser for a Calgary building database. Extract ALL filter criteria from user queries.

The database has these attributes:
- height (in feet, numeric)
- assessed_value (in dollars, numeric)  
- zoning (string like "RC-G", "C-COR1", "M-C1", etc.)
- building_type (one of: Commercial, Residential, Industrial, Mixed Use, Special Purpose, Other)
- address (full street address including quadrant, e.g. "10101 SOUTHPORT RD SW")
- land_size_sf (land size in square feet, numeric)

Calgary addresses end with a quadrant: NW, NE, SW, SE.

Return ONLY a valid JSON object with a "filters" array. Each filter has:
- "attribute": the database field to filter on
- "operator": one of ">", "<", ">=", "<=", "==", "!=", "contains", "equals", "endswith"
- "value": the value to compare against

For location queries:
- "in the NW" or "in NW" -> {"attribute": "address", "operator": "endswith", "value": "NW"}
- "on 17th avenue" -> {"attribute": "address", "operator": "contains", "value": "17"}
- "on Stephen Ave" -> {"attribute": "address", "operator": "contains", "value": "STEPHEN"}

Examples:
Query: "buildings over 100 feet and commercial type"
Response: {"filters": [{"attribute": "height", "operator": ">", "value": 100}, {"attribute": "building_type", "operator": "equals", "value": "Commercial"}]}

Query: "show buildings in the NW"
Response: {"filters": [{"attribute": "address", "operator": "endswith", "value": "NW"}]}

Query: "commercial buildings on centre street in NE"
Response: {"filters": [{"attribute": "building_type", "operator": "equals", "value": "Commercial"}, {"attribute": "address", "operator": "contains", "value": "CENTRE"}, {"attribute": "address", "operator": "endswith", "value": "NE"}]}

Query: "buildings worth over 1 million"
Response: {"filters": [{"attribute": "assessed_value", "operator": ">", "value": 1000000}]}

Query: "large lots over 5000 square feet"
Response: {"filters": [{"attribute": "land_size_sf", "operator": ">", "value": 5000}]}

Respond with ONLY the JSON object, no other text or explanation."""

    try:
        print("Sending request to HuggingFace Router API...")
        
        response = query({
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_query
                }
            ],
            "model": "deepseek-ai/DeepSeek-V3.2:novita",
            "max_tokens": 250,
            "temperature": 0.1
        })
        
        print(f"Raw API Response: {json.dumps(response, indent=2)}")
        
        if "error" in response:
            print(f"API Error: {response['error']}")
            result = fallback_parser(user_query)
            result['source'] = 'FALLBACK_ERROR'
            return result
        
        generated_text = response["choices"][0]["message"]["content"]
        print(f"Generated Text: {generated_text}")
        
        filter_obj = extract_json(generated_text)
        
        if filter_obj:
            print(f"LLM Successfully Parsed: {filter_obj}")
            return {
                'success': True,
                'filter': filter_obj,
                'raw_response': generated_text,
                'source': 'LLM'
            }
        else:
            print("LLM returned invalid JSON, falling back to rule-based parser")
            result = fallback_parser(user_query)
            result['source'] = 'FALLBACK'
            return result
            
    except requests.RequestException as e:
        print(f"Request Error: {e}")
        result = fallback_parser(user_query)
        result['source'] = 'FALLBACK_ERROR'
        return result
    except KeyError as e:
        print(f"Response parsing error: {e}")
        result = fallback_parser(user_query)
        result['source'] = 'FALLBACK_PARSE_ERROR'
        return result
    except Exception as e:
        print(f"Processing Error: {e}")
        import traceback
        traceback.print_exc()
        result = fallback_parser(user_query)
        result['source'] = 'FALLBACK_EXCEPTION'
        return result


def extract_json(text):
    """Extract JSON object from text response."""
    try:
        text = text.strip()
        
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()
        
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    return None


def fallback_parser(query):
    """Rule-based fallback parser for common query patterns."""
    print(f"Using fallback parser for: '{query}'")
    
    query_lower = query.lower()
    filters = []
    
    # Quadrant queries (NW, NE, SW, SE) - check address ending
    for quad in ['nw', 'ne', 'sw', 'se']:
        patterns = [
            f'in the {quad}',
            f'in {quad}',
            f' {quad} calgary',
            f' {quad} area'
        ]
        if any(p in query_lower for p in patterns) or query_lower.endswith(f' {quad}'):
            filters.append({'attribute': 'address', 'operator': 'endswith', 'value': quad.upper()})
            break
    
    # Street/Avenue queries
    street_patterns = [
        (r'on\s+(\d+(?:st|nd|rd|th)?)\s*(street|avenue|ave|st)?', lambda m: m.group(1)),
        (r'on\s+([a-z]+)\s*(street|avenue|ave|st|road|rd|drive|dr|way|blvd|boulevard)', lambda m: m.group(1)),
    ]
    for pattern, extractor in street_patterns:
        match = re.search(pattern, query_lower)
        if match:
            street_name = extractor(match).upper()
            filters.append({'attribute': 'address', 'operator': 'contains', 'value': street_name})
            break
    
    # Height queries
    height_keywords = ['height', 'feet', 'tall', 'ft']
    if any(kw in query_lower for kw in height_keywords):
        number = extract_number(query)
        if number:
            if any(kw in query_lower for kw in ['over', 'above', 'greater', 'more than', 'taller']):
                filters.append({'attribute': 'height', 'operator': '>', 'value': number})
            elif any(kw in query_lower for kw in ['under', 'below', 'less', 'shorter']):
                filters.append({'attribute': 'height', 'operator': '<', 'value': number})
    
    # Value queries
    value_keywords = ['value', 'worth', 'assessed', 'cost', 'price']
    if any(kw in query_lower for kw in value_keywords) or '$' in query_lower:
        number = extract_number(query)
        if number:
            if any(kw in query_lower for kw in ['over', 'above', 'more', 'greater', 'exceeds']):
                filters.append({'attribute': 'assessed_value', 'operator': '>', 'value': number})
            elif any(kw in query_lower for kw in ['under', 'below', 'less', 'cheaper']):
                filters.append({'attribute': 'assessed_value', 'operator': '<', 'value': number})
    
    # Land size queries
    land_keywords = ['land size', 'lot size', 'square feet', 'sq ft', 'sqft', 'land_size']
    if any(kw in query_lower for kw in land_keywords):
        number = extract_number(query)
        if number:
            if any(kw in query_lower for kw in ['over', 'above', 'more', 'greater', 'larger']):
                filters.append({'attribute': 'land_size_sf', 'operator': '>', 'value': number})
            elif any(kw in query_lower for kw in ['under', 'below', 'less', 'smaller']):
                filters.append({'attribute': 'land_size_sf', 'operator': '<', 'value': number})
    
    # Building type queries
    building_types = {
        'commercial': 'Commercial',
        'residential': 'Residential',
        'industrial': 'Industrial',
        'mixed use': 'Mixed Use',
        'mixed-use': 'Mixed Use',
        'special': 'Special Purpose'
    }
    for btype, proper_name in building_types.items():
        if btype in query_lower:
            filters.append({'attribute': 'building_type', 'operator': 'equals', 'value': proper_name})
            break
    
    # Zoning queries
    zoning_match = re.search(r'\b([a-z]{1,3}-[a-z0-9]+)\b', query_lower, re.IGNORECASE)
    if zoning_match:
        filters.append({'attribute': 'zoning', 'operator': 'contains', 'value': zoning_match.group(1).upper()})
    
    if filters:
        return {
            'success': True,
            'filter': {'filters': filters},
            'source': 'FALLBACK'
        }
    
    return {
        'success': False,
        'error': 'Could not parse query. Try: "buildings over 100 feet", "commercial buildings in NW", "buildings on 17th avenue", "properties worth over $1 million"',
        'source': 'FALLBACK'
    }


def extract_number(text):
    """Extract a number from text, handling various formats."""
    text_lower = text.lower()
    
    # Handle millions
    match = re.search(r'(\d+(?:\.\d+)?)\s*million', text_lower)
    if match:
        return float(match.group(1)) * 1000000
    
    # Handle thousands (k)
    match = re.search(r'(\d+(?:\.\d+)?)\s*k\b', text_lower)
    if match:
        return float(match.group(1)) * 1000
    
    # Handle thousands (thousand)
    match = re.search(r'(\d+(?:\.\d+)?)\s*thousand', text_lower)
    if match:
        return float(match.group(1)) * 1000
    
    # Match regular numbers (including currency)
    match = re.search(r'\$?([\d,]+(?:\.\d+)?)', text)
    if match:
        return float(match.group(1).replace(',', ''))
    
    return None


if __name__ == "__main__":
    print("Testing API connection...")
    test_response = query({
        "messages": [{"role": "user", "content": "Say 'working'"}],
        "model": "deepseek-ai/DeepSeek-V3.2:novita",
        "max_tokens": 10
    })
    print(f"Connection test: {test_response}")
    
    print("\n" + "="*60)
    test_queries = [
        "show buildings over 100 feet",
        "find commercial buildings",
        "buildings worth more than $1 million",
        "show buildings in the NW",
        "commercial buildings over 50 feet in NE",
        "buildings on 17th avenue",
        "residential buildings in SW",
        "buildings on centre street"
    ]
    
    for q in test_queries:
        result = process_query(q)
        print(f"\nQuery: {q}")
        print(f"Result: {result}\n")