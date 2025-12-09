import requests
import json
import os

CACHE_FILE = "cached_buildings.json"
BASE_URL = "https://data.calgary.ca/resource/4bsw-nn7w.json"

def safe_float(v):
    try:
        return float(str(v).replace(",", "").replace("$", "").strip())
    except:
        return 0.0

# Extract lat/lon from multipolygon
def extract_coordinates(mp):
    if not mp:
        return None
    if isinstance(mp, str):
        mp = json.loads(mp)

    coords = mp.get("coordinates")
    if not coords:
        return None

    lats = []
    lons = []
    footprint = []

    for poly in coords:
        for ring in poly:
            for lon, lat in ring:
                lats.append(lat)
                lons.append(lon)
                footprint.append([lon, lat])

    if not lats or not lons:
        return None

    return {
        "centroid": (sum(lats)/len(lats), sum(lons)/len(lons)),
        "footprint": footprint
    }

# Convert land use → building type category
def classify_type(zoning):
    if not zoning:
        return "Other"
    z = zoning.upper()
    if z.startswith("C-"):
        return "Commercial"
    if z.startswith("I-"):
        return "Industrial"
    if z.startswith("R-") or z.startswith("M-") or z.startswith("RM") or z.startswith("R1"):
        return "Residential"
    if z.startswith("MU"):
        return "Mixed Use"
    if z.startswith("S-") or z.startswith("P-"):
        return "Special Purpose"
    return "Other"

# Simple rank-based height distribution
def assign_ranked_heights(buildings):
    buildings_sorted = sorted(buildings, key=lambda b: b["assessed_value"], reverse=True)
    max_h, min_h = 350, 30
    n = len(buildings_sorted)

    for i, b in enumerate(buildings_sorted):
        t = 1 - (i / max(1, n - 1))
        b["height"] = min_h + t * (max_h - min_h)

    return buildings_sorted

def fetch_calgary_buildings(use_cache=True):
    # 1. Try to load from cache
    if use_cache and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                print("Loaded buildings from cache")
                return json.load(f)
        except:
            print("Cache file corrupted, refetching...")

    # 2. Otherwise fetch from API
    print("Fetching buildings from API...")
    buildings = fetch_from_api()

    # 3. Save to cache
    try:
        with open(CACHE_FILE, "w") as f:
            json.dump(buildings, f)
        print("Saved buildings to cache")
    except Exception as e:
        print("Failed to save cache:", e)

    return buildings

def fetch_from_api():
    print("Fetching balanced land-use buildings...")

    land_use_filters = {
        "Commercial": "land_use_designation like 'C-%'",
        "Industrial": "land_use_designation like 'I-%'",
        "Residential": "land_use_designation like 'R%'",
        "Mixed Use": "land_use_designation like 'MU%'",
        "Special Purpose": "land_use_designation like 'S-%'"
    }

    buildings = []

    # For each category, fetch 30 buildings if possible
    for category, where in land_use_filters.items():
        params = {
            "$limit": 50,
            "$where": f"{where} AND assessed_value > 0 AND land_size_sf IS NOT NULL AND multipolygon IS NOT NULL",
            "$order": "assessed_value DESC"
        }

        try:
            r = requests.get(BASE_URL, params=params, timeout=20)
            r.raise_for_status()
            data = r.json()

            for rec in data:
                coords = extract_coordinates(rec.get("multipolygon"))
                if not coords:
                    continue

                lat, lon = coords["centroid"]

                building = {
                    "id": rec.get("roll_number"),
                    "address": rec.get("address"),
                    "latitude": lat,
                    "longitude": lon,
                    "zoning": rec.get("land_use_designation"),
                    "building_type": classify_type(rec.get("land_use_designation")),
                    "assessed_value": safe_float(rec.get("assessed_value")),
                    "land_size_sf": safe_float(rec.get("land_size_sf")),
                    "footprint": coords["footprint"],
                }

                # Only add if all popup-required fields exist
                if (
                    building["id"]
                    and building["address"]
                    and building["assessed_value"] > 0
                    and building["zoning"]
                    and building["building_type"]
                ):
                    buildings.append(building)

                if len([b for b in buildings if b["building_type"] == category]) >= 30:
                    break

            print(f"{category}: {len([b for b in buildings if b['building_type']==category])} buildings loaded")

        except Exception as e:
            print("Error fetching category:", category, e)

    # distribute heights visually
    buildings = assign_ranked_heights(buildings)

    print(f"Total buildings loaded: {len(buildings)}")
    return buildings

if __name__ == "__main__":
    fetch_calgary_buildings()