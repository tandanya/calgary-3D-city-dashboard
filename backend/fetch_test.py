import requests
import json

url = "https://data.calgary.ca/resource/4bsw-nn7w.json"

response = requests.get(url, params={'$limit': 5}, timeout=30)
data = response.json()

print("="*60)
print("RAW API RESPONSE - First 2 records")
print("="*60)

for i, record in enumerate(data[:2]):
    print(f"\n--- Record {i+1} ---")
    for key, value in record.items():
        if key != 'multipolygon':  # Skip the long polygon data
            print(f"  {key}: {value} (type: {type(value).__name__})")
        else:
            print(f"  {key}: [POLYGON DATA]")

print("\n" + "="*60)
print("CHECKING SPECIFIC FIELDS")
print("="*60)

record = data[0]
print(f"\nassessed_value raw: {record.get('assessed_value')}")
print(f"assessed_value type: {type(record.get('assessed_value'))}")
print(f"nr_assessed_value raw: {record.get('nr_assessed_value')}")
print(f"land_size_sf raw: {record.get('land_size_sf')}")
print(f"land_use_designation raw: {record.get('land_use_designation')}")
print(f"assessment_class_description raw: {record.get('assessment_class_description')}")