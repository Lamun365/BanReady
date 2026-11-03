import json
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

DATA_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)


TARGET_RULES = [
    ("DECLARED", "EVEN"),
    ("DECLARED", "ODD"),
    ("DECLARED", "BOTH"),
    ("PERMANENT", "EVEN"),
    ("PERMANENT", "ODD"),
    ("PERMANENT", "BOTH"),
]


# ============================================================
# Main program
# ============================================================

def main():
    print()
    print("BanReady Side Test Street Finder")
    print("================================")
    print()

    # --------------------------------------------------------
    # Check processed Worcester parking-ban dataset
    # --------------------------------------------------------

    if not DATA_FILE.exists():
        print("ERROR: Processed parking-ban data not found.")
        print()
        print(f"Expected file: {DATA_FILE}")
        return

    # --------------------------------------------------------
    # Load GeoJSON
    # --------------------------------------------------------

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError:
        print("ERROR: Could not read the GeoJSON file.")
        return

    features = data.get("features", [])

    if not features:
        print("ERROR: No Worcester street features found.")
        return

    print(
        f"Loaded {len(features)} Worcester "
        "parking-ban segments."
    )
    print()

    # --------------------------------------------------------
    # Search each target rule combination
    # --------------------------------------------------------

    for target_ban_type, target_side in TARGET_RULES:

        matches = []

        # ----------------------------------------------------
        # Find matching GIS records
        # ----------------------------------------------------

        for feature in features:

            properties = feature.get(
                "properties",
                {},
            )

            ban_type = str(
                properties.get("ban_type") or ""
            ).strip().upper()

            restricted_side = str(
                properties.get("no_parking_side") or ""
            ).strip().upper()

            street_name = str(
                properties.get("street_name") or ""
            ).strip()

            if ban_type != target_ban_type:
                continue

            if restricted_side != target_side:
                continue

            if not street_name:
                continue

            matches.append(feature)

        # ----------------------------------------------------
        # Display category
        # ----------------------------------------------------

        print("=" * 60)

        print(
            f"{target_ban_type} | "
            f"NO PARKING SIDE = {target_side}"
        )

        print("=" * 60)
        print()

        print(
            f"Matching segments: {len(matches)}"
        )

        print()

        if not matches:
            print(
                "No matching Worcester segments found."
            )
            print()
            continue

        # ----------------------------------------------------
        # Avoid displaying the same street repeatedly
        # ----------------------------------------------------

        shown_streets = set()

        displayed = 0

        # ----------------------------------------------------
        # Display example streets
        # ----------------------------------------------------

        for feature in matches:

            properties = feature.get(
                "properties",
                {},
            )

            street_name = str(
                properties.get("street_name") or ""
            ).strip()

            normalized_name = street_name.upper()

            # Avoid showing the same street several times.
            if normalized_name in shown_streets:
                continue

            shown_streets.add(
                normalized_name
            )

            displayed += 1

            print(
                f"Example {displayed}"
            )

            print("-" * 30)

            print(
                f"Street:     {street_name}"
            )

            print(
                f"Segment ID: "
                f"{properties.get('segment_id')}"
            )

            print(
                f"Street ID:  "
                f"{properties.get('street_id')}"
            )

            print(
                f"From:       "
                f"{properties.get('from_location') or '-'}"
            )

            print(
                f"To:         "
                f"{properties.get('to_location') or '-'}"
            )

            print(
                f"Ban Type:   "
                f"{properties.get('ban_type')}"
            )

            print(
                f"Ban Zone:   "
                f"{properties.get('ban_zone')}"
            )

            print(
                f"Restricted: "
                f"{properties.get('no_parking_side')}"
            )

            print()

            # Show a maximum of five distinct streets
            # for each parking-rule category.
            if displayed >= 5:
                break

        print(
            f"Distinct streets shown: {displayed}"
        )

        print()

    # --------------------------------------------------------
    # Finished
    # --------------------------------------------------------

    print("=" * 60)
    print("SEARCH COMPLETE")
    print("=" * 60)
    print()

    print(
        "Use these street names with "
        "scripts/test_address_parity.py."
    )


# ============================================================
# Start program
# ============================================================

if __name__ == "__main__":
    main()