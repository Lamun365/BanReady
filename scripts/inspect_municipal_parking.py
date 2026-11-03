import json
from collections import Counter
from pathlib import Path


DATA_FOLDER = Path(
    "data/raw/worcester/municipal_parking"
)


def find_geojson():
    """
    Find the first GeoJSON file inside the
    Worcester municipal parking raw-data folder.
    """

    if not DATA_FOLDER.exists():
        return None

    files = list(
        DATA_FOLDER.glob("*.geojson")
    )

    if not files:
        return None

    return files[0]


def clean_value(value):
    """
    Convert missing or empty values into a readable
    terminal value.
    """

    if value is None:
        return "(EMPTY)"

    text = str(value).strip()

    if text == "":
        return "(EMPTY)"

    return text


def main():
    print()
    print("BanReady Municipal Parking Inspector")
    print("====================================")
    print()

    # ========================================================
    # Find GeoJSON
    # ========================================================

    data_file = find_geojson()

    if data_file is None:
        print(
            "ERROR: Municipal Parking GeoJSON was not found."
        )
        print()
        print("Expected folder:")
        print(DATA_FOLDER)
        return

    print("File:")
    print(data_file)
    print()

    # ========================================================
    # Load GeoJSON
    # ========================================================

    try:
        with open(
            data_file,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError:
        print(
            "ERROR: Municipal Parking GeoJSON "
            "could not be read."
        )
        return

    print("GeoJSON loaded successfully.")
    print()

    print(
        f"GeoJSON type: "
        f"{data.get('type')}"
    )

    print()

    # ========================================================
    # Get features
    # ========================================================

    features = data.get(
        "features",
        [],
    )

    print(
        f"Number of parking features: "
        f"{len(features)}"
    )

    print()

    if not features:
        print(
            "ERROR: No municipal parking "
            "features were found."
        )
        return

    # ========================================================
    # Property fields
    # ========================================================

    first_properties = features[0].get(
        "properties",
        {},
    )

    print("AVAILABLE PROPERTY FIELDS")
    print("=========================")
    print()

    for field in first_properties.keys():
        print(field)

    print()

    # ========================================================
    # Geometry types
    # ========================================================

    geometry_types = Counter()

    for feature in features:
        geometry = feature.get(
            "geometry",
            {},
        )

        geometry_type = clean_value(
            geometry.get("type")
        )

        geometry_types[
            geometry_type
        ] += 1

    print("GEOMETRY TYPES")
    print("==============")
    print()

    for geometry_type, count in sorted(
        geometry_types.items()
    ):
        print(
            f"{geometry_type}: {count}"
        )

    print()

    # ========================================================
    # Parking types
    # ========================================================

    parking_types = Counter()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        parking_type = clean_value(
            properties.get("PK_TYPE")
        )

        parking_types[
            parking_type
        ] += 1

    print("PARKING TYPES")
    print("=============")
    print()

    for parking_type, count in sorted(
        parking_types.items()
    ):
        print(
            f"{parking_type}: {count}"
        )

    print()

    # ========================================================
    # PK_MNTH values
    # ========================================================

    monthly_values = Counter()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        value = clean_value(
            properties.get("PK_MNTH")
        )

        monthly_values[
            value
        ] += 1

    print("PK_MNTH VALUES")
    print("==============")
    print()

    for value, count in sorted(
        monthly_values.items()
    ):
        print(
            f"{value}: {count}"
        )

    print()

    print(
        "NOTE: PK_MNTH is being inspected only."
    )

    print(
        "BanReady will not assign a meaning to "
        "Y or N until that field is verified."
    )

    print()

    # ========================================================
    # Payment values
    # ========================================================

    payment_values = Counter()

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        value = clean_value(
            properties.get("PK_PAY")
        )

        payment_values[
            value
        ] += 1

    print("PK_PAY VALUES")
    print("=============")
    print()

    for value, count in sorted(
        payment_values.items()
    ):
        print(
            f"{value}: {count}"
        )

    print()

    # ========================================================
    # Print all facilities
    # ========================================================

    print("MUNICIPAL PARKING FACILITIES")
    print("============================")
    print()

    for index, feature in enumerate(
        features,
        start=1,
    ):
        properties = feature.get(
            "properties",
            {},
        )

        geometry = feature.get(
            "geometry",
            {},
        )

        print(
            f"Facility {index}"
        )

        print("-" * 40)

        print(
            "Name:",
            clean_value(
                properties.get("PK_NAME")
            ),
        )

        print(
            "Type:",
            clean_value(
                properties.get("PK_TYPE")
            ),
        )

        print(
            "Address:",
            clean_value(
                properties.get("PK_ADDR")
            ),
        )

        print(
            "Parking ID:",
            clean_value(
                properties.get("PARKING_ID")
            ),
        )

        print(
            "Parking record:",
            clean_value(
                properties.get("PARKING_")
            ),
        )

        print(
            "Payment:",
            clean_value(
                properties.get("PK_PAY")
            ),
        )

        print(
            "PK_MNTH:",
            clean_value(
                properties.get("PK_MNTH")
            ),
        )

        print(
            "Building ID:",
            clean_value(
                properties.get("BLDG_ID")
            ),
        )

        print(
            "Buildings ID:",
            clean_value(
                properties.get("BLDGS_ID")
            ),
        )

        print(
            "OBJECTID:",
            clean_value(
                properties.get("OBJECTID")
            ),
        )

        print(
            "GlobalID:",
            clean_value(
                properties.get("GlobalID")
            ),
        )

        print(
            "Geometry:",
            clean_value(
                geometry.get("type")
            ),
        )

        print()

    # ========================================================
    # Consistency check
    # ========================================================

    garage_count = 0
    lot_count = 0
    other_count = 0

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        parking_type = clean_value(
            properties.get("PK_TYPE")
        ).upper()

        if parking_type == "GARAGE":
            garage_count += 1

        elif parking_type == "LOT":
            lot_count += 1

        else:
            other_count += 1

    classified_total = (
        garage_count
        + lot_count
        + other_count
    )

    print("CONSISTENCY CHECK")
    print("=================")
    print()

    print(
        f"Total features: {len(features)}"
    )

    print(
        f"Garages:        {garage_count}"
    )

    print(
        f"Lots:           {lot_count}"
    )

    print(
        f"Other:          {other_count}"
    )

    print(
        f"Classified:     {classified_total}"
    )

    print()

    if classified_total == len(features):
        print(
            "PASS: Every municipal parking "
            "feature was inspected."
        )
    else:
        print(
            "FAIL: Feature counts do not match."
        )

    print()

    if other_count == 0:
        print(
            "PASS: Every facility is classified "
            "as Garage or Lot."
        )
    else:
        print(
            "WARNING: Some facilities have another "
            "or missing parking type."
        )

    print()

    print(
        "Municipal parking inspection complete."
    )


if __name__ == "__main__":
    main()