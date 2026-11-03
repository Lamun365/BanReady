import json
from pathlib import Path


DATA_FILE = Path(
    "data/raw/worcester/winter_parking_ban/Winter_Parking_Ban.geojson"
)


print()
print("BanReady GIS Data Inspector")
print("===========================")
print()


# --------------------------------------------------
# 1. Check that the file exists
# --------------------------------------------------

if not DATA_FILE.exists():
    print("ERROR: GeoJSON file was not found.")
    print()
    print("Expected file:")
    print(DATA_FILE)
    raise SystemExit


print("File found:")
print(DATA_FILE)
print()


# --------------------------------------------------
# 2. Load GeoJSON
# --------------------------------------------------

with open(DATA_FILE, "r", encoding="utf-8") as file:
    data = json.load(file)


print("GeoJSON loaded successfully.")
print()


# --------------------------------------------------
# 3. Inspect top-level GeoJSON information
# --------------------------------------------------

geojson_type = data.get("type")

print("GeoJSON type:")
print(geojson_type)
print()


# --------------------------------------------------
# 4. Get all features
# --------------------------------------------------

features = data.get("features", [])

print("Number of features:")
print(len(features))
print()


if len(features) == 0:
    print("ERROR: No features were found.")
    raise SystemExit


# --------------------------------------------------
# 5. Inspect first feature
# --------------------------------------------------

first_feature = features[0]

properties = first_feature.get("properties", {})
geometry = first_feature.get("geometry", {})


print("Available property fields")
print("-------------------------")

for field_name in properties.keys():
    print(field_name)

print()


# --------------------------------------------------
# 6. Geometry information
# --------------------------------------------------

print("Geometry type:")
print(geometry.get("type"))
print()


# --------------------------------------------------
# 7. Display first record
# --------------------------------------------------

print("First feature properties")
print("------------------------")

for key, value in properties.items():
    print(f"{key}: {value}")

print()


# --------------------------------------------------
# 8. Display several sample records
# --------------------------------------------------

print("Sample records")
print("==============")

sample_count = min(5, len(features))

for index in range(sample_count):
    feature = features[index]

    print()
    print(f"Record {index + 1}")
    print("----------------")

    feature_properties = feature.get(
        "properties",
        {}
    )

    for key, value in feature_properties.items():
        print(f"{key}: {value}")


print()
print("Inspection complete.")
