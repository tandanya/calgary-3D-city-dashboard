import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
# Using a smaller, faster model for inference
API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"

def process_query(user_query):
    """
    Process natural language query using Hugging Face API.
    Returns a filter object for the building data.
    """
    
    print(f"\n{'='*60}")
    print(f"🤖 LLM Query Processing")
    print(f"{'='*60}")
    print(f"User Query: '{user_query}'")
    print(f"HuggingFace API Key Present: {bool(HUGGINGFACE_API_KEY)}")
    print(f"API URL: {API_URL}")
    
    prompt = f"""<s>[INST] You are a query parser for a building database. Extract the filter criteria from the user's query.

The database has these attributes:
- height (in feet, numeric)
- assessed_value (in dollars, numeric)  
- zoning (string like "RC-G", "C-COR1", "M-C1", etc.)
- building_type (one of: Commercial, Residential, Industrial, Mixed Use, Special Purpose, Other)

Return ONLY a valid JSON object with these fields:
- "attribute": the database field to filter on
- "operator": one of ">", "<", ">=", "<=", "==", "!=", "contains", "equals"
- "value": the value to compare against (number for numeric fields, string for text fields)

User query: "{user_query}"

Respond with ONLY the JSON object, no other text. [/INST]"""

    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 100,
            "temperature": 0.1,
            "return_full_text": False
        }
    }
    
    try:
        print("📡 Sending request to HuggingFace API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        
        print(f"📥 Response Status: {response.status_code}")
        
        response.raise_for_status()
        
        result = response.json()
        print(f"📦 Raw API Response: {json.dumps(result, indent=2)}")
        
        # Extract the generated text
        if isinstance(result, list) and len(result) > 0:
            generated_text = result[0].get('generated_text', '')
        else:
            generated_text = str(result)
        
        print(f"✨ Generated Text: {generated_text}")
        
        # Parse the JSON from the response
        filter_obj = extract_json(generated_text)
        
        if filter_obj:
            print(f"✅ LLM Successfully Parsed: {filter_obj}")
            return {
                'success': True,
                'filter': filter_obj,
                'raw_response': generated_text,
                'source': 'LLM'  # ← ADD THIS to track source
            }
        else:
            print("⚠️ LLM returned invalid JSON, falling back to rule-based parser")
            result = fallback_parser(user_query)
            result['source'] = 'FALLBACK'  # ← ADD THIS
            return result
            
    except requests.RequestException as e:
        print(f"❌ API Error: {e}")
        result = fallback_parser(user_query)
        result['source'] = 'FALLBACK_ERROR'  # ← ADD THIS
        return result
    except Exception as e:
        print(f"❌ Processing Error: {e}")
        import traceback
        traceback.print_exc()
        result = fallback_parser(user_query)
        result['source'] = 'FALLBACK_EXCEPTION'  # ← ADD THIS
        return result

def extract_json(text):
    """Extract JSON object from text response."""
    try:
        # Try to find JSON in the response
        text = text.strip()
        
        # Look for JSON object pattern
        start = text.find('{')
        end = text.rfind('}') + 1
        
        if start != -1 and end > start:
            json_str = text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass
    
    return None

def fallback_parser(query):
    """
    Rule-based fallback parser for common query patterns.
    Used when LLM is unavailable or returns invalid response.
    """
    print(f"🔧 Using fallback parser for: '{query}'")
    
    query_lower = query.lower()
    
    # Height queries
    if 'height' in query_lower or 'feet' in query_lower or 'tall' in query_lower:
        number = extract_number(query)
        if number:
            if 'over' in query_lower or 'above' in query_lower or 'greater' in query_lower or 'more than' in query_lower:
                return {'success': True, 'filter': {'attribute': 'height', 'operator': '>', 'value': number}}
            elif 'under' in query_lower or 'below' in query_lower or 'less' in query_lower:
                return {'success': True, 'filter': {'attribute': 'height', 'operator': '<', 'value': number}}
    
    # Value queries
    if 'value' in query_lower or '$' in query_lower or 'worth' in query_lower or 'assessed' in query_lower:
        number = extract_number(query)
        if number:
            if 'over' in query_lower or 'above' in query_lower or 'more' in query_lower or 'greater' in query_lower:
                return {'success': True, 'filter': {'attribute': 'assessed_value', 'operator': '>', 'value': number}}
            elif 'under' in query_lower or 'below' in query_lower or 'less' in query_lower:
                return {'success': True, 'filter': {'attribute': 'assessed_value', 'operator': '<', 'value': number}}
    
    # Zoning queries
    zoning_patterns = ['rc-g', 'c-cor', 'm-c', 'cc-', 'r-c', 'i-g', 'mu-']
    for pattern in zoning_patterns:
        if pattern in query_lower:
            # Find the full zoning code
            import re
            match = re.search(r'[a-z]+-[a-z0-9]+', query_lower, re.IGNORECASE)
            if match:
                return {'success': True, 'filter': {'attribute': 'zoning', 'operator': 'contains', 'value': match.group().upper()}}
    
    # Building type queries
    building_types = ['commercial', 'residential', 'industrial', 'mixed use', 'special']
    for btype in building_types:
        if btype in query_lower:
            return {'success': True, 'filter': {'attribute': 'building_type', 'operator': 'equals', 'value': btype.title()}}
    
    return {
        'success': False,
        'error': 'Could not parse query. Try queries like "show buildings over 100 feet" or "highlight commercial buildings"',
        'source':'FALLBACK'
    }

def extract_number(text):
    """Extract a number from text, handling various formats."""
    import re
    
    # Handle millions/thousands
    text_lower = text.lower()
    
    # Match patterns like "$500,000" or "500000" or "500k" or "1 million"
    if 'million' in text_lower:
        match = re.search(r'(\d+(?:\.\d+)?)\s*million', text_lower)
        if match:
            return float(match.group(1)) * 1000000
    
    if 'k' in text_lower:
        match = re.search(r'(\d+(?:\.\d+)?)\s*k', text_lower)
        if match:
            return float(match.group(1)) * 1000
    
    # Match regular numbers
    match = re.search(r'\$?([\d,]+(?:\.\d+)?)', text)
    if match:
        return float(match.group(1).replace(',', ''))
    
    return None