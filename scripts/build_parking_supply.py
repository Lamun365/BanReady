import json
import sys
from pathlib import Path


# ============================================================
# Project setup
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# BanReady imports
# ============================================================

from backend.app.models.parking_supply import (
    GARAGE,
    LOT,
    UNKNOWN,
    VERIFIED,
    ParkingSupply,
)


# ============================================================
# Files
# ============================================================

DESTINATION_FILE = Path(
    "data/processed/parking_destinations.json"
)

OUTPUT_FILE = Path(
    "data/processed/parking_supply.json"
)


# ============================================================
# Authoritative capacity sources
# ============================================================

UNION_STATION_SOURCE_NAME = (
    "City of Worcester - Union Station"
)

UNION_STATION_SOURCE_URL = (
    "https://www.worcesterma.gov/union-station"
)


MUNICIPAL_LOTS_SOURCE_NAME = (
    "City of Worcester - Municipal Lots"
)

MUNICIPAL_LOTS_SOURCE_URL = (
    "https://www.worcesterma.gov/parking/municipal-lots"
)


MUNICIPAL_GARAGES_SOURCE_NAME = (
    "City of Worcester - Municipal Garages"
)

MUNICIPAL_GARAGES_SOURCE_URL = (
    "https://www.worcesterma.gov/parking/municipal-garages"
)


# ============================================================
# Verified normal capacities
#
# These values represent total/normal facility capacity.
#
# They do NOT represent verified winter-ban capacity.
# ============================================================

VERIFIED_TOTAL_CAPACITIES = {
    # Garage
    "Union Station Garage": 500,

    # Municipal lots
    "Amtrak-MBTA Lot": 124,
    "Grafton Street Lot": 66,
    "Green Street Lot": 27,
    "Highland Street Lot": 93,
    "McGrath (Library) Lot": 282,
    "Milbury Street Lot": 47,
    "Water Street Lot": 34,
}


# ============================================================
# Garages whose numerical capacity remains unknown
# ============================================================

UNKNOWN_GARAGE_CAPACITIES = {
    "Federal Plaza Garage",
    "Major Taylor Garage",
    "Pearl-Elm Garage",
    "Worcester Common Garage",
}


# ============================================================
# Helpers
# ============================================================

def load_json_file(path):
    if not path.exists():
        raise RuntimeError(
            f"Required BanReady file not found: {path}"
        )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"BanReady could not read JSON file: {path}"
        ) from error


def normalize_supply_type(
    destination_type,
):
    if (
        destination_type
        == "MUNICIPAL_GARAGE"
    ):
        return GARAGE

    if (
        destination_type
        == "MUNICIPAL_LOT"
    ):
        return LOT

    return None


def create_supply_id(
    parking_id,
):
    return (
        "supply-"
        f"{parking_id}"
    )


def get_capacity_source(
    name,
    supply_type,
):
    """
    Return the source relevant to the total-capacity
    evidence for the facility.
    """

    if (
        name == "Union Station Garage"
        and supply_type == GARAGE
    ):
        return (
            UNION_STATION_SOURCE_NAME,
            UNION_STATION_SOURCE_URL,
        )

    if (
        supply_type == LOT
        and name
        in VERIFIED_TOTAL_CAPACITIES
    ):
        return (
            MUNICIPAL_LOTS_SOURCE_NAME,
            MUNICIPAL_LOTS_SOURCE_URL,
        )

    return (
        MUNICIPAL_GARAGES_SOURCE_NAME,
        MUNICIPAL_GARAGES_SOURCE_URL,
    )


def build_methodology(
    name,
    total_capacity,
    supply_type,
):
    if total_capacity is None:
        return (
            "BanReady found no authoritative numerical "
            "total-capacity value for this facility in "
            "the sources reviewed during Milestone 9. "
            "The capacity is therefore retained as "
            "UNKNOWN rather than estimated."
        )

    if (
        name == "Union Station Garage"
        and supply_type == GARAGE
    ):
        return (
            "Total capacity is taken directly from the "
            "official City of Worcester Union Station "
            "page, which identifies the Union Station "
            "parking garage as a 500-space garage."
        )

    if supply_type == LOT:
        return (
            "Total capacity is taken directly from the "
            "official City of Worcester Municipal Lots "
            "page. The published approximate public "
            "space count is used. Separately designated "
            "Zipcar spaces are not added to the general "
            "parking supply."
        )

    return (
        "No numerical capacity methodology is currently "
        "available for this facility."
    )


def build_notes(
    name,
    supply_type,
    total_capacity,
):
    notes = []

    if total_capacity is None:
        notes.append(
            "Total capacity remains unknown."
        )
    else:
        notes.append(
            "Total capacity has authoritative "
            "numerical evidence."
        )

    notes.append(
        "Ban-period capacity remains unknown because "
        "total facility capacity does not establish "
        "how many spaces are available specifically "
        "for displaced vehicles during a winter ban."
    )

    if supply_type == LOT:
        notes.append(
            "Municipal-lot inclusion in the supply "
            "dataset does not mean BanReady currently "
            "recommends the lot for overnight winter-ban "
            "relocation."
        )

    if (
        name
        in UNKNOWN_GARAGE_CAPACITIES
    ):
        notes.append(
            "The facility is a verified Worcester "
            "municipal garage, but no authoritative "
            "numeric total capacity was established "
            "during the current research pass."
        )

    return " ".join(notes)


# ============================================================
# Build individual supply record
# ============================================================

def build_supply_record(
    destination,
):
    parking_id = destination.get(
        "parking_id"
    )

    name = destination.get(
        "name"
    )

    destination_type = (
        destination.get(
            "destination_type"
        )
    )

    supply_type = (
        normalize_supply_type(
            destination_type
        )
    )

    if not parking_id:
        return None

    if not name:
        return None

    if supply_type is None:
        return None

    # --------------------------------------------------------
    # Normal/total capacity
    # --------------------------------------------------------

    total_capacity = (
        VERIFIED_TOTAL_CAPACITIES.get(
            name
        )
    )

    if total_capacity is None:
        total_capacity_status = UNKNOWN
    else:
        total_capacity_status = VERIFIED

    # --------------------------------------------------------
    # Ban-period capacity
    #
    # No municipal facility currently has a verified
    # ban-specific capacity.
    # --------------------------------------------------------

    ban_capacity = None
    ban_capacity_status = UNKNOWN

    # --------------------------------------------------------
    # Evidence
    # --------------------------------------------------------

    source_name, source_url = (
        get_capacity_source(
            name=name,
            supply_type=supply_type,
        )
    )

    methodology = (
        build_methodology(
            name=name,
            total_capacity=total_capacity,
            supply_type=supply_type,
        )
    )

    notes = build_notes(
        name=name,
        supply_type=supply_type,
        total_capacity=total_capacity,
    )

    # --------------------------------------------------------
    # Build model
    # --------------------------------------------------------

    return ParkingSupply(
        supply_id=create_supply_id(
            parking_id
        ),

        name=name,

        supply_type=supply_type,

        latitude=destination.get(
            "latitude"
        ),

        longitude=destination.get(
            "longitude"
        ),

        address=destination.get(
            "address"
        ),

        total_capacity=total_capacity,

        ban_capacity=ban_capacity,

        total_capacity_status=(
            total_capacity_status
        ),

        ban_capacity_status=(
            ban_capacity_status
        ),

        source_name=source_name,

        source_url=source_url,

        street_name=None,

        segment_id=None,

        ban_type=None,

        restricted_side=None,

        segment_length_meters=None,

        usable_length_meters=None,

        assumed_space_length_meters=None,

        methodology=methodology,

        notes=notes,
    )


# ============================================================
# Main builder
# ============================================================

def main():
    print()
    print("BanReady Parking Supply Builder")
    print("===============================")
    print()

    # --------------------------------------------------------
    # Load destination dataset
    # --------------------------------------------------------

    try:
        data = load_json_file(
            DESTINATION_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    destinations = data.get(
        "destinations",
        [],
    )

    if not destinations:
        print(
            "ERROR: No parking destinations "
            "were found."
        )

        return

    print(
        f"Input destinations: "
        f"{len(destinations)}"
    )

    print()

    # --------------------------------------------------------
    # Build supply records
    # --------------------------------------------------------

    supplies = []

    skipped = 0

    for destination in destinations:
        supply = build_supply_record(
            destination
        )

        if supply is None:
            skipped += 1
            continue

        supplies.append(
            supply.to_dict()
        )

    # --------------------------------------------------------
    # Stable output order
    # --------------------------------------------------------

    supplies.sort(
        key=lambda item: (
            item["supply_type"],
            item["name"],
        )
    )

    # --------------------------------------------------------
    # Count supply types
    # --------------------------------------------------------

    garage_count = sum(
        1
        for item in supplies
        if (
            item["supply_type"]
            == GARAGE
        )
    )

    lot_count = sum(
        1
        for item in supplies
        if (
            item["supply_type"]
            == LOT
        )
    )

    # --------------------------------------------------------
    # Count capacity evidence
    # --------------------------------------------------------

    verified_total_count = sum(
        1
        for item in supplies
        if (
            item[
                "total_capacity_status"
            ]
            == VERIFIED
        )
    )

    unknown_total_count = sum(
        1
        for item in supplies
        if (
            item[
                "total_capacity_status"
            ]
            == UNKNOWN
        )
    )

    known_ban_count = sum(
        1
        for item in supplies
        if (
            item["ban_capacity"]
            is not None
        )
    )

    unknown_ban_count = sum(
        1
        for item in supplies
        if (
            item[
                "ban_capacity_status"
            ]
            == UNKNOWN
        )
    )

    # --------------------------------------------------------
    # Verified normal capacity sum
    # --------------------------------------------------------

    verified_capacity_sum = sum(
        item["total_capacity"]
        for item in supplies
        if (
            item["total_capacity"]
            is not None
            and item[
                "total_capacity_status"
            ]
            == VERIFIED
        )
    )

    # --------------------------------------------------------
    # Break down known normal supply
    # --------------------------------------------------------

    verified_garage_capacity = sum(
        item["total_capacity"]
        for item in supplies
        if (
            item["supply_type"]
            == GARAGE
            and item[
                "total_capacity"
            ]
            is not None
            and item[
                "total_capacity_status"
            ]
            == VERIFIED
        )
    )

    verified_lot_capacity = sum(
        item["total_capacity"]
        for item in supplies
        if (
            item["supply_type"]
            == LOT
            and item[
                "total_capacity"
            ]
            is not None
            and item[
                "total_capacity_status"
            ]
            == VERIFIED
        )
    )

    # --------------------------------------------------------
    # Output dataset
    # --------------------------------------------------------

    output = {
        "dataset_name": (
            "BanReady Parking Supply"
        ),

        "city": "Worcester",

        "state": "MA",

        "supply_count": len(
            supplies
        ),

        "metadata": {
            "garage_count": (
                garage_count
            ),

            "lot_count": (
                lot_count
            ),

            "verified_total_capacity_records": (
                verified_total_count
            ),

            "unknown_total_capacity_records": (
                unknown_total_count
            ),

            "known_ban_capacity_records": (
                known_ban_count
            ),

            "unknown_ban_capacity_records": (
                unknown_ban_count
            ),

            "verified_normal_capacity_sum": (
                verified_capacity_sum
            ),

            "verified_garage_capacity_sum": (
                verified_garage_capacity
            ),

            "verified_lot_capacity_sum": (
                verified_lot_capacity
            ),

            "capacity_note": (
                "Verified normal capacity does not "
                "represent verified winter-ban "
                "available supply."
            ),
        },

        "supplies": supplies,
    }

    # --------------------------------------------------------
    # Save dataset
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # ========================================================
    # Report
    # ========================================================

    print(
        f"Supply records created: "
        f"{len(supplies)}"
    )

    print(
        f"Skipped records:        "
        f"{skipped}"
    )

    print()

    print(
        f"Garages:                "
        f"{garage_count}"
    )

    print(
        f"Lots:                   "
        f"{lot_count}"
    )

    print()

    print(
        f"Verified total capacity records: "
        f"{verified_total_count}"
    )

    print(
        f"Unknown total capacity records:  "
        f"{unknown_total_count}"
    )

    print()

    print(
        f"Known ban capacity records:      "
        f"{known_ban_count}"
    )

    print(
        f"Unknown ban capacity records:    "
        f"{unknown_ban_count}"
    )

    print()

    print(
        "VERIFIED NORMAL CAPACITY"
    )

    print(
        "========================"
    )

    print()

    print(
        f"Garage capacity: "
        f"{verified_garage_capacity}"
    )

    print(
        f"Lot capacity:    "
        f"{verified_lot_capacity}"
    )

    print(
        f"Combined:        "
        f"{verified_capacity_sum}"
    )

    print()

    # ========================================================
    # Print individual records
    # ========================================================

    print("SUPPLY RECORDS")
    print("==============")
    print()

    for supply in supplies:
        print(
            supply["supply_id"]
        )

        print(
            f"  Name: "
            f"{supply['name']}"
        )

        print(
            f"  Type: "
            f"{supply['supply_type']}"
        )

        print(
            f"  Address: "
            f"{supply['address']}"
        )

        print(
            f"  Total capacity: "
            f"{supply['total_capacity']}"
        )

        print(
            f"  Total status: "
            f"{supply['total_capacity_status']}"
        )

        print(
            f"  Ban capacity: "
            f"{supply['ban_capacity']}"
        )

        print(
            f"  Ban status: "
            f"{supply['ban_capacity_status']}"
        )

        print(
            f"  Source: "
            f"{supply['source_name']}"
        )

        print(
            f"  Source URL: "
            f"{supply['source_url']}"
        )

        print()

    # ========================================================
    # Consistency checks
    # ========================================================

    print("CONSISTENCY CHECK")
    print("=================")
    print()

    checks = []


    # Test 1
    checks.append(
        (
            "12 supply records",
            len(supplies) == 12,
        )
    )


    # Test 2
    checks.append(
        (
            "No records skipped",
            skipped == 0,
        )
    )


    # Test 3
    checks.append(
        (
            "5 garages",
            garage_count == 5,
        )
    )


    # Test 4
    checks.append(
        (
            "7 lots",
            lot_count == 7,
        )
    )


    # Test 5
    checks.append(
        (
            "8 verified total capacities",
            verified_total_count == 8,
        )
    )


    # Test 6
    checks.append(
        (
            "4 unknown total capacities",
            unknown_total_count == 4,
        )
    )


    # Test 7
    checks.append(
        (
            "No known ban capacities",
            known_ban_count == 0,
        )
    )


    # Test 8
    checks.append(
        (
            "12 unknown ban capacities",
            unknown_ban_count == 12,
        )
    )


    # Test 9
    checks.append(
        (
            "Verified garage capacity = 500",
            verified_garage_capacity == 500,
        )
    )


    # Test 10
    checks.append(
        (
            "Verified lot capacity = 673",
            verified_lot_capacity == 673,
        )
    )


    # Test 11
    checks.append(
        (
            "Verified normal capacity = 1173",
            verified_capacity_sum == 1173,
        )
    )


    # Test 12
    #
    # No known ban capacity can appear before
    # BanReady establishes ban-specific evidence.
    # --------------------------------------------------------

    checks.append(
        (
            "No accidental ban supply",
            all(
                supply["ban_capacity"]
                is None
                for supply in supplies
            ),
        )
    )


    # ========================================================
    # Print checks
    # ========================================================

    for index, (
        check_name,
        passed,
    ) in enumerate(
        checks,
        start=1,
    ):
        result_text = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            f"Test {index:02d} - "
            f"{check_name}: "
            f"{result_text}"
        )

    failed_checks = sum(
        1
        for _, passed in checks
        if not passed
    )

    passed_checks = (
        len(checks)
        - failed_checks
    )

    print()

    print(
        "===================================="
    )

    print(
        "BANREADY SUPPLY BUILD SUMMARY"
    )

    print(
        "===================================="
    )

    print()

    print(
        f"Total checks: "
        f"{len(checks)}"
    )

    print(
        f"Passed:       "
        f"{passed_checks}"
    )

    print(
        f"Failed:       "
        f"{failed_checks}"
    )

    print()

    if failed_checks == 0:
        print(
            "ALL SUPPLY BUILD CHECKS PASSED"
        )

    else:
        print(
            "SUPPLY BUILD CHECKS FAILED"
        )

    print()

    print(
        "Saved:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "1173 represents verified NORMAL "
        "facility capacity in the currently "
        "modeled records."
    )

    print()

    print(
        "1173 does NOT represent verified "
        "winter-ban capacity."
    )

    print()

    print(
        "1173 does NOT represent currently "
        "available parking spaces."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()