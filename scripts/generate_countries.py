import json
import math
import urllib.request
import os
import sys

GEOJSON_URL = "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "_ne_countries_cache.geojson")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "web", "static", "web", "js", "_countries.js")


NAME_MAP = {
    "United States of America": "united_states_of_america",
    "United Republic of Tanzania": "united_republic_of_tanzania",
    "Western Sahara": "western_sahara",
    "Canada": "canada",
    "Japan": "japan",
    "Kosovo": "kosovo",
    "Azerbaijan": "azerbaijan",
    "Uzbekistan": "uzbekistan",
    "North Korea": "north_korea",
    "Dem. Rep. Korea": "north_korea",
    "Korea, Democratic People's Republic of": "north_korea",
    "Senegal": "senegal",
    "Equatorial Guinea": "equatorial_guinea",
    "Hungary": "hungary",
    "Tajikistan": "tajikistan",
    "Côte d'Ivoire": "ivory_coast",
    "Ivory Coast": "ivory_coast",
    "Lithuania": "lithuania",
    "Mongolia": "mongolia",
    "Egypt": "egypt",
    "Rwanda": "rwanda",
    "Spain": "spain",
    "Argentina": "argentina",
    "Norway": "norway",
    "Ghana": "ghana",
    "Belarus": "belarus",
    "Mauritania": "mauritania",
    "Zambia": "zambia",
    "Bosnia and Herzegovina": "bosnia_and_herzegovina",
    "Bosnia and Herz.": "bosnia_and_herzegovina",
    "Guatemala": "guatemala",
    "Zimbabwe": "zimbabwe",
    "Belgium": "belgium",
    "Kazakhstan": "kazakhstan",
    "Liberia": "liberia",
    "Kyrgyzstan": "kyrgyzstan",
    "Netherlands": "netherlands",
    "Sierra Leone": "sierra_leone",
    "Portugal": "portugal",
    "Djibouti": "djibouti",
    "Latvia": "latvia",
    "Namibia": "namibia",
    "Papua New Guinea": "papua_new_guinea",
    "Switzerland": "switzerland",
    "Bulgaria": "bulgaria",
    "Greenland": "greenland",
    "Honduras": "honduras",
    "Serbia": "republic_of_serbia",
    "Republic of Serbia": "republic_of_serbia",
    "Lebanon": "lebanon",
    "Malaysia": "malaysia",
    "Mozambique": "mozambique",
    "Greece": "greece",
    "Nicaragua": "nicaragua",
    "Afghanistan": "afghanistan",
    "Turkmenistan": "turkmenistan",
    "Sudan": "sudan",
    "Guinea": "guinea",
    "Panama": "panama",
    "Nepal": "nepal",
    "Luxembourg": "luxembourg",
    "Somalia": "somalia",
    "Croatia": "croatia",
    "Venezuela": "venezuela",
    "Venezuela, Bolivarian Republic of": "venezuela",
    "Central African Republic": "central_african_republic",
    "Central African Rep.": "central_african_republic",
    "Iran": "iran",
    "Iran, Islamic Republic of": "iran",
    "Iran (Islamic Republic of)": "iran",
    "Guyana": "guyana",
    "China": "china",
    "Armenia": "armenia",
    "Thailand": "thailand",
    "Iraq": "iraq",
    "South Korea": "south_korea",
    "Korea, Republic of": "south_korea",
    "Rep. Korea": "south_korea",
    "Ukraine": "ukraine",
    "Libya": "libya",
    "South Africa": "south_africa",
    "Oman": "oman",
    "Finland": "finland",
    "El Salvador": "el_salvador",
    "Republic of the Congo": "republic_of_the_congo",
    "Congo": "republic_of_the_congo",
    "Syria": "syria",
    "Syrian Arab Republic": "syria",
    "Pakistan": "pakistan",
    "Romania": "romania",
    "Myanmar": "myanmar",
    "Tunisia": "tunisia",
    "Austria": "austria",
    "United Arab Emirates": "united_arab_emirates",
    "Guinea-Bissau": "guinea_bissau",
    "Guinea Bissau": "guinea_bissau",
    "Colombia": "colombia",
    "Angola": "angola",
    "Niger": "niger",
    "Turkey": "turkey",
    "Türkiye": "turkey",
    "Madagascar": "madagascar",
    "Belize": "belize",
    "Bangladesh": "bangladesh",
    "Democratic Republic of the Congo": "democratic_republic_of_the_congo",
    "Dem. Rep. Congo": "democratic_republic_of_the_congo",
    "Congo, the Democratic Republic of the": "democratic_republic_of_the_congo",
    "Congo, Democratic Republic of the": "democratic_republic_of_the_congo",
    "Uruguay": "uruguay",
    "France": "france",
    "Slovakia": "slovakia",
    "Peru": "peru",
    "Laos": "laos",
    "Lao People's Democratic Republic": "laos",
    "Lao PDR": "laos",
    "Nigeria": "nigeria",
    "Bolivia": "bolivia",
    "Bolivia, Plurinational State of": "bolivia",
    "Bolivia (Plurinational State of)": "bolivia",
    "United Kingdom": "united_kingdom",
    "Malawi": "malawi",
    "Ecuador": "ecuador",
    "Israel": "israel",
    "Albania": "albania",
    "Suriname": "suriname",
    "Algeria": "algeria",
    "Czechia": "czechia",
    "Czech Republic": "czechia",
    "Togo": "togo",
    "Jordan": "jordan",
    "Chile": "chile",
    "Costa Rica": "costa_rica",
    "Georgia": "georgia",
    "Burkina Faso": "burkina_faso",
    "Morocco": "morocco",
    "Sweden": "sweden",
    "Gabon": "gabon",
    "Saudi Arabia": "saudi_arabia",
    "Mali": "mali",
    "Yemen": "yemen",
    "Russia": "russia",
    "Russian Federation": "russia",
    "Chad": "chad",
    "Mexico": "mexico",
    "India": "india",
    "Paraguay": "paraguay",
    "Antarctica": "antarctica",
    "Australia": "australia",
    "Uganda": "uganda",
    "Burundi": "burundi",
    "Kenya": "kenya",
    "Botswana": "botswana",
    "Italy": "italy",
    "Cambodia": "cambodia",
    "Ethiopia": "ethiopia",
    "South Sudan": "south_sudan",
    "S. Sudan": "south_sudan",
    "Cameroon": "cameroon",
    "Benin": "benin",
    "Somaliland": "somaliland",
    "Brazil": "brazil",
    "Estonia": "estonia",
    "Montenegro": "montenegro",
    "Slovenia": "slovenia",
    "Germany": "germany",
    "Eritrea": "eritrea",
    "Poland": "poland",
    "Indonesia": "indonesia",
    "Vietnam": "vietnam",
    "Viet Nam": "vietnam",
    "Kuwait": "kuwait",
    "North Macedonia": "north_macedonia",
    "Macedonia": "north_macedonia",
    "Dominican Republic": "dominican_republic",
    "Haiti": "haiti",
    "Cuba": "cuba",
    "Jamaica": "jamaica",
    "Trinidad and Tobago": "trinidad_and_tobago",
    "Puerto Rico": "puerto_rico",
    "New Zealand": "new_zealand",
    "Philippines": "philippines",
    "Sri Lanka": "sri_lanka",
    "Taiwan": "taiwan",
    "Taiwan, Province of China": "taiwan",
    "Qatar": "qatar",
    "Bahrain": "bahrain",
    "Cyprus": "cyprus",
    "Moldova": "moldova",
    "Republic of Moldova": "moldova",
    "Moldova, Republic of": "moldova",
    "Denmark": "denmark",
    "Ireland": "ireland",
    "Iceland": "iceland",
    "Bhutan": "bhutan",
    "Brunei": "brunei",
    "Brunei Darussalam": "brunei",
    "East Timor": "east_timor",
    "Timor-Leste": "east_timor",
    "Eswatini": "eswatini",
    "Swaziland": "eswatini",
    "Lesotho": "lesotho",
    "Gambia": "gambia",
    "The Gambia": "gambia",
    "Palestine": "palestine",
    "State of Palestine": "palestine",
    "Palestinian Territory, Occupied": "palestine",
    "W. Sahara": "western_sahara",
    "Falkland Islands": "falkland_islands",
    "Falkland Islands (Malvinas)": "falkland_islands",
    "Fiji": "fiji",
    "New Caledonia": "new_caledonia",
    "Solomon Islands": "solomon_islands",
    "Vanuatu": "vanuatu",
}

ELEVATION_MAP = {
    "afghanistan": 1884, "albania": 708, "algeria": 800, "angola": 1023,
    "argentina": 595, "armenia": 1792, "australia": 330, "austria": 910,
    "azerbaijan": 384, "bangladesh": 85, "belarus": 160, "belgium": 181,
    "belize": 173, "benin": 273, "bhutan": 3280, "bolivia": 1192,
    "bosnia_and_herzegovina": 500, "botswana": 1013, "brazil": 320,
    "brunei": 478, "bulgaria": 472, "burkina_faso": 297, "burundi": 1504,
    "cambodia": 126, "cameroon": 667, "canada": 487, "central_african_republic": 635,
    "chad": 543, "chile": 1871, "china": 1840, "colombia": 593,
    "costa_rica": 746, "croatia": 331, "cuba": 108, "cyprus": 91,
    "czechia": 433, "democratic_republic_of_the_congo": 726, "denmark": 34,
    "djibouti": 430, "dominican_republic": 424, "east_timor": 800,
    "ecuador": 1117, "egypt": 321, "el_salvador": 442, "equatorial_guinea": 577,
    "eritrea": 853, "eswatini": 745, "estonia": 61, "ethiopia": 1330,
    "fiji": 281, "finland": 164, "france": 375, "gabon": 377,
    "gambia": 34, "georgia": 1432, "germany": 263, "ghana": 190,
    "greece": 498, "greenland": 1792, "guatemala": 759, "guinea": 452,
    "guinea_bissau": 70, "guyana": 207, "haiti": 367, "honduras": 604,
    "hungary": 143, "iceland": 557, "india": 621, "indonesia": 367,
    "iran": 1305, "iraq": 312, "ireland": 118, "israel": 508,
    "italy": 538, "ivory_coast": 250, "jamaica": 340, "japan": 438,
    "jordan": 812, "kazakhstan": 387, "kenya": 762, "kosovo": 492,
    "kuwait": 108, "kyrgyzstan": 2988, "laos": 710, "latvia": 87,
    "lebanon": 1250, "lesotho": 2161, "liberia": 243, "libya": 331,
    "lithuania": 110, "luxembourg": 325, "madagascar": 615, "malawi": 779,
    "malaysia": 300, "mali": 343, "mauritania": 276, "mexico": 1111,
    "moldova": 139, "mongolia": 1528, "montenegro": 1086, "morocco": 909,
    "mozambique": 345, "myanmar": 702, "namibia": 1141, "nepal": 3265,
    "netherlands": 30, "new_caledonia": 300, "new_zealand": 388,
    "nicaragua": 298, "niger": 474, "nigeria": 380, "north_korea": 600,
    "north_macedonia": 741, "norway": 460, "oman": 310, "pakistan": 900,
    "palestine": 600, "panama": 360, "papua_new_guinea": 667, "paraguay": 178,
    "peru": 1555, "philippines": 442, "poland": 173, "portugal": 372,
    "qatar": 28, "republic_of_serbia": 473, "republic_of_the_congo": 430,
    "romania": 414, "russia": 600, "rwanda": 1598, "saudi_arabia": 665,
    "senegal": 69, "sierra_leone": 279, "slovakia": 458, "slovenia": 492,
    "solomon_islands": 300, "somalia": 410, "somaliland": 410, "south_africa": 1034,
    "south_korea": 282, "south_sudan": 500, "spain": 660, "sri_lanka": 228,
    "sudan": 568, "suriname": 246, "sweden": 320, "switzerland": 1350,
    "syria": 514, "taiwan": 1150, "tajikistan": 3186, "thailand": 287,
    "togo": 236, "trinidad_and_tobago": 83, "tunisia": 246, "turkey": 1132,
    "turkmenistan": 288, "uganda": 1100, "ukraine": 175,
    "united_arab_emirates": 149, "united_kingdom": 162,
    "united_republic_of_tanzania": 1018, "united_states_of_america": 760,
    "uruguay": 109, "uzbekistan": 353, "vanuatu": 300, "venezuela": 450,
    "vietnam": 398, "western_sahara": 256, "yemen": 999, "zambia": 1138,
    "zimbabwe": 1024, "falkland_islands": 200,
}


def simplify_coords(coords, target_points=60):
    if len(coords) <= target_points:
        return coords
    
    total_len = 0
    for i in range(1, len(coords)):
        dx = coords[i][0] - coords[i-1][0]
        dy = coords[i][1] - coords[i-1][1]
        total_len += math.sqrt(dx*dx + dy*dy)
    
    if total_len == 0:
        return coords[:target_points]
    
    step = total_len / (target_points - 1)
    result = [coords[0]]
    accumulated = 0
    next_threshold = step
    
    for i in range(1, len(coords)):
        dx = coords[i][0] - coords[i-1][0]
        dy = coords[i][1] - coords[i-1][1]
        seg_len = math.sqrt(dx*dx + dy*dy)
        accumulated += seg_len
        
        while accumulated >= next_threshold and len(result) < target_points - 1:
            result.append(coords[i])
            next_threshold += step
    
    if result[-1] != coords[-1]:
        result.append(coords[-1])
    
    return result


def elevation_to_height(elev_m):
    h = 0.3 + (min(elev_m, 4000) / 4000) * 0.7
    return round(h, 2)


def normalize_name(name):
    if name in NAME_MAP:
        return NAME_MAP[name]
    return name.lower().replace(' ', '_').replace('-', '_').replace("'", "").replace(",", "")


def extract_largest_polygon(geometry):
    if geometry["type"] == "Polygon":
        return geometry["coordinates"][0]
    elif geometry["type"] == "MultiPolygon":
        largest = max(geometry["coordinates"], key=lambda p: len(p[0]))
        return largest[0]
    return []


def main():
    if os.path.exists(CACHE_FILE):
        print(f"Using cached GeoJSON: {CACHE_FILE}")
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            geojson = json.load(f)
    else:
        print(f"Downloading GeoJSON from {GEOJSON_URL}...")
        req = urllib.request.Request(GEOJSON_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as resp:
            data = resp.read().decode('utf-8')
        geojson = json.loads(data)
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(geojson, f)
        print("Cached GeoJSON locally.")

    countries = {}
    skipped = []
    
    for feature in geojson["features"]:
        props = feature["properties"]
        name = props.get("ADMIN") or props.get("name") or props.get("NAME") or props.get("NAME_LONG") or ""
        if not name:
            continue
        
        key = normalize_name(name)
        
        geometry = feature["geometry"]
        coords = extract_largest_polygon(geometry)
        
        if len(coords) < 3:
            skipped.append(name)
            continue
        
        area_approx = abs(max(c[0] for c in coords) - min(c[0] for c in coords)) * \
                       abs(max(c[1] for c in coords) - min(c[1] for c in coords))
        
        if area_approx > 500:
            target = 120
        elif area_approx > 100:
            target = 80
        elif area_approx > 20:
            target = 60
        else:
            target = max(30, min(len(coords), 50))
        
        simplified = simplify_coords(coords, target)
        
        lats = [round(c[1], 4) for c in simplified]
        lons = [round(c[0], 4) for c in simplified]
        
        elev = ELEVATION_MAP.get(key, 300)
        height = elevation_to_height(elev)
        
        countries[key] = {
            "lat": lats,
            "lon": lons,
            "height": height
        }

    entries = []
    for key in sorted(countries.keys()):
        v = countries[key]
        lat_str = json.dumps(v["lat"])
        lon_str = json.dumps(v["lon"])
        entries.append(f'"{key}":{{"lat":{lat_str},"lon":{lon_str},"height":{v["height"]}}}')
    
    js_content = "const countries={" + ",".join(entries) + "};\n"
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    file_size = os.path.getsize(OUTPUT_FILE)
    total_points = sum(len(v["lat"]) for v in countries.values())
    
    print(f"\nGenerated {OUTPUT_FILE}")
    print(f"  Countries: {len(countries)}")
    print(f"  Total border points: {total_points}")
    print(f"  Avg points/country: {total_points / len(countries):.0f}")
    print(f"  File size: {file_size / 1024:.1f} KB")
    
    if skipped:
        print(f"  Skipped: {skipped}")


if __name__ == "__main__":
    main()
