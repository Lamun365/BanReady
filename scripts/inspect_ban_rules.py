import json
from collections import Counter
from pathlib import Path


DATA_FILE = Path("data/processed/winter_parking_ban.geojson")


def clean_value(value):
    """
    Convert empty or missing values into a readable label.
    """

    if value is None:
        return "(EMPTY)"

    value = str(value).strip()

    if value == "":
        return "(EMPTY)"

    return value


def print_counter(title, counter):
    """
    Print a frequency table for a Counter.
    """

    print()
    print(title)
    print("=" * len(title))

    for value, count in sorted(
        counter.items(),
        key=lambda item: (-item[1], item[0])
    ):
        print(f"{value}: {count}")

    print()
    print(f"Unique values: {len(counter)}")


def main():
    print()
    print("BanReady Parking Ban Rule Inspector")
    print("===================================")
    print()

    # --------------------------------------------------
    # Check file
    # --------------------------------------------------

    if not DATA_FILE.exists():
        print("ERROR: Processed parking-ban data was not found.")
        print(f"Expected file: {DATA_FILE}")
        return

    # --------------------------------------------------
    # Load GeoJSON
    # --------------------------------------------------

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            geojson = json.load(file)

    except json.JSONDecodeError:
        print("ERROR: The GeoJSON file could not be read.")
        return

    features = geojson.get("features", [])

    if not features:
        print("ERROR: No street features were found.")
        return

    print(f"Loaded {len(features)} Worcester street features.")

    # --------------------------------------------------
    # Counters
    # --------------------------------------------------

    ban_types = Counter()
    ban_zones = Counter()
    parking_sides = Counter()
    rule_combinations = Counter()

    # --------------------------------------------------
    # Inspect every feature
    # --------------------------------------------------

    for feature in features:
        properties = feature.get("properties", {})

        ban_type = clean_value(
            properties.get("ban_type")
        )

        ban_zone = clean_value(
            properties.get("ban_zone")
        )

        parking_side = clean_value(
            properties.get("no_parking_side")
        )

        ban_types[ban_type] += 1
        ban_zones[ban_zone] += 1
        parking_sides[parking_side] += 1

        combination = (
            ban_type,
            ban_zone,
            parking_side,
        )

        rule_combinations[combination] += 1

    # --------------------------------------------------
    # Print individual values
    # --------------------------------------------------

    print_counter(
        "BAN TYPES",
        ban_types
    )

    print_counter(
        "BAN ZONES",
        ban_zones
    )

    print_counter(
        "NO PARKING SIDES",
        parking_sides
    )

    # --------------------------------------------------
    # Print combinations
    # --------------------------------------------------

    print()
    print("RULE COMBINATIONS")
    print("=================")
    print()

    sorted_combinations = sorted(
        rule_combinations.items(),
        key=lambda item: (-item[1], item[0])
    )

    for combination, count in sorted_combinations:
        ban_type, ban_zone, parking_side = combination

        print(
            f"{ban_type} | "
            f"Zone {ban_zone} | "
            f"Side {parking_side} | "
            f"{count} segments"
        )

    print()
    print(
        f"Unique rule combinations: "
        f"{len(rule_combinations)}"
    )

    # --------------------------------------------------
    # Consistency check
    # --------------------------------------------------

    total_types = sum(ban_types.values())
    total_zones = sum(ban_zones.values())
    total_sides = sum(parking_sides.values())

    print()
    print("CONSISTENCY CHECK")
    print("=================")
    print()

    print(f"Total GIS features: {len(features)}")
    print(f"Ban type records:   {total_types}")
    print(f"Ban zone records:   {total_zones}")
    print(f"Side records:       {total_sides}")

    print()

    if (
        total_types == len(features)
        and total_zones == len(features)
        and total_sides == len(features)
    ):
        print("PASS: Every GIS feature was included.")
    else:
        print("WARNING: Record counts do not match.")

    print()
    print("Rule inspection complete.")


if __name__ == "__main__":
    main()