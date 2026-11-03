import json
from pathlib import Path


DATA_FOLDER = Path(
    "data/raw/worcester/address_points"
)


def main():
    print()
    print("BanReady Address Point Inspector")
    print("===============================")
    print()

    if not DATA_FOLDER.exists():
        print("ERROR: Address-points folder not found.")
        print()
        print(f"Expected: {DATA_FOLDER}")
        return

    geojson_files = list(
        DATA_FOLDER.glob("*.geojson")
    )

    if not geojson_files:
        print("ERROR: No GeoJSON file found.")
        print()
        print(
            "Place the Worcester Address Points "
            "GeoJSON inside:"
        )
        print(DATA_FOLDER)
        return

    data_file = geojson_files[0]

    print(f"File: {data_file.name}")
    print()

    try:
        with open(
            data_file,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError:
        print("ERROR: GeoJSON could not be read.")
        return

    print(f"GeoJSON type: {data.get('type')}")
    print()

    features = data.get("features", [])

    print(f"Number of address features: {len(features)}")
    print()

    if not features:
        print("ERROR: No address features found.")
        return

    first_feature = features[0]

    properties = first_feature.get(
        "properties",
        {}
    )

    geometry = first_feature.get(
        "geometry",
        {}
    )

    print("AVAILABLE PROPERTY FIELDS")
    print("=========================")
    print()

    for field in properties.keys():
        print(field)

    print()
    print("GEOMETRY")
    print("========")
    print()

    print(f"Type: {geometry.get('type')}")

    coordinates = geometry.get(
        "coordinates"
    )

    print(f"Coordinates: {coordinates}")

    print()
    print("FIRST FIVE ADDRESS RECORDS")
    print("==========================")

    for index, feature in enumerate(
        features[:5],
        start=1
    ):
        print()
        print(f"Record {index}")
        print("-" * 30)

        record = feature.get(
            "properties",
            {}
        )

        for key, value in record.items():
            print(f"{key}: {value}")

    print()
    print("Inspection complete.")


if __name__ == "__main__":
    main()