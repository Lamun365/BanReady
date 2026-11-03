import json
from pathlib import Path


INPUT_FILE = Path(
    "data/raw/worcester/winter_parking_ban/Winter_Parking_Ban.geojson"
)

OUTPUT_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)


print()
print("BanReady Parking Ban Cleaner")
print("============================")
print()


# --------------------------------------------------
# 1. Check input
# --------------------------------------------------

if not INPUT_FILE.exists():
    print("ERROR: Input GeoJSON not found.")
    print(INPUT_FILE)
    raise SystemExit


# --------------------------------------------------
# 2. Load Worcester GeoJSON
# --------------------------------------------------

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    raw_data = json.load(file)


features = raw_data.get("features", [])

print(f"Raw features: {len(features)}")


# --------------------------------------------------
# 3. Clean features
# --------------------------------------------------

clean_features = []


for feature in features:

    properties = feature.get("properties", {})
    geometry = feature.get("geometry")

    clean_properties = {
        "segment_id": properties.get("OBJECTID"),
        "street_id": properties.get("STR_NM_ID"),
        "street_name": properties.get("FULL_NAME"),
        "from_location": properties.get("From_"),
        "to_location": properties.get("To_"),
        "ban_type": properties.get("BanType"),
        "ban_zone": properties.get("BanZone"),
        "no_parking_side": properties.get("Side"),
    }

    clean_feature = {
        "type": "Feature",
        "properties": clean_properties,
        "geometry": geometry,
    }

    clean_features.append(clean_feature)


# --------------------------------------------------
# 4. Create clean FeatureCollection
# --------------------------------------------------

clean_geojson = {
    "type": "FeatureCollection",
    "features": clean_features,
}


# --------------------------------------------------
# 5. Create output directory if necessary
# --------------------------------------------------

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)


# --------------------------------------------------
# 6. Save cleaned dataset
# --------------------------------------------------

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    json.dump(
        clean_geojson,
        file,
        indent=2,
        ensure_ascii=False
    )


print(f"Clean features: {len(clean_features)}")

print()
print("Saved:")
print(OUTPUT_FILE)

print()
print("Cleaning complete.")