import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from backend.app.services.parity_engine import (
    infer_address_parity_mapping,
)


PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

ADDRESS_FILE = Path(
    "data/raw/worcester/address_points/"
    "Address_Points.geojson"
)


def main():
    print()
    print("BanReady Address Parity Test")
    print("============================")
    print()

    if not PARKING_FILE.exists():
        print(
            "ERROR: Parking-ban GeoJSON not found."
        )
        return

    if not ADDRESS_FILE.exists():
        print(
            "ERROR: Address Points GeoJSON not found."
        )
        return

    print("Loading Worcester GIS data...")
    print()

    with open(
        PARKING_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        parking_data = json.load(file)

    with open(
        ADDRESS_FILE,
        "r",
        encoding="utf-8"
    ) as file:
        address_data = json.load(file)

    parking_features = parking_data.get(
        "features",
        []
    )

    address_features = address_data.get(
        "features",
        []
    )

    print(
        f"Parking segments: {len(parking_features)}"
    )

    print(
        f"Address points:   {len(address_features)}"
    )

    print()

    street_name = input(
        "Enter Worcester street name: "
    ).strip()

    if not street_name:
        print()
        print("ERROR: Street name is required.")
        return

    matching_segments = []

    for feature in parking_features:
        properties = feature.get(
            "properties",
            {}
        )

        name = properties.get(
            "street_name",
            ""
        )

        if (
            str(name).strip().upper()
            == street_name.upper()
        ):
            matching_segments.append(
                feature
            )

    if not matching_segments:
        print()
        print(
            "ERROR: No parking-ban segment "
            "found for that street."
        )
        return

    print()
    print(
        f"Matching segments: "
        f"{len(matching_segments)}"
    )

    print()

    for index, feature in enumerate(
        matching_segments,
        start=1
    ):
        properties = feature.get(
            "properties",
            {}
        )

        geometry = feature.get(
            "geometry",
            {}
        )

        coordinates = geometry.get(
            "coordinates",
            []
        )

        print("=" * 55)
        print(
            f"SEGMENT {index}"
        )
        print("=" * 55)

        print(
            f"Street: "
            f"{properties.get('street_name')}"
        )

        print(
            f"Segment ID: "
            f"{properties.get('segment_id')}"
        )

        print(
            f"From: "
            f"{properties.get('from_location')}"
        )

        print(
            f"To: "
            f"{properties.get('to_location')}"
        )

        print(
            f"Ban Type: "
            f"{properties.get('ban_type')}"
        )

        print(
            f"No Parking Side: "
            f"{properties.get('no_parking_side')}"
        )

        print()

        mapping = infer_address_parity_mapping(
            street_name=properties.get(
                "street_name"
            ),
            street_coordinates=coordinates,
            address_features=address_features,
        )

        print("ADDRESS PARITY EVIDENCE")
        print("-----------------------")

        print(
            f"LEFT  ODD:  "
            f"{mapping.left_odd_count}"
        )

        print(
            f"LEFT  EVEN: "
            f"{mapping.left_even_count}"
        )

        print()

        print(
            f"RIGHT ODD:  "
            f"{mapping.right_odd_count}"
        )

        print(
            f"RIGHT EVEN: "
            f"{mapping.right_even_count}"
        )

        print()

        print(
            f"Resolved LEFT:  "
            f"{mapping.left_parity}"
        )

        print(
            f"Resolved RIGHT: "
            f"{mapping.right_parity}"
        )

        print(
            f"Confidence:     "
            f"{mapping.confidence}"
        )

        print(
            f"Usable addresses: "
            f"{mapping.usable_address_count}"
        )

        print()


if __name__ == "__main__":
    main()