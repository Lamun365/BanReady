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
    ESTIMATED,
    STREET_SEGMENT,
    ParkingSupply,
)


# ============================================================
# Main test
# ============================================================

def main():
    print()
    print("BanReady Parking Supply Model Test")
    print("==================================")
    print()

    # --------------------------------------------------------
    # Synthetic supply record
    #
    # IMPORTANT:
    # These capacities are test values only.
    # They are NOT real Worcester parking-capacity data.
    # --------------------------------------------------------

    supply = ParkingSupply(
        supply_id="test-street-supply-001",

        name="Synthetic Test Street",

        supply_type=STREET_SEGMENT,

        latitude=42.26,

        longitude=-71.80,

        address=None,

        total_capacity=20,

        ban_capacity=10,

        total_capacity_status=ESTIMATED,

        ban_capacity_status=ESTIMATED,

        source_name=None,

        source_url=None,

        street_name="TEST STREET",

        segment_id=123456,

        ban_type="DECLARED",

        restricted_side="EVEN",

        segment_length_meters=120.0,

        usable_length_meters=100.0,

        assumed_space_length_meters=5.5,

        methodology=(
            "Synthetic test record used only "
            "to validate the BanReady parking "
            "supply data model."
        ),

        notes=(
            "Do not use this synthetic record "
            "as real Worcester parking data."
        ),
    )


    # ========================================================
    # Convert model to dictionary
    # ========================================================

    data = supply.to_dict()


    # ========================================================
    # Print model
    # ========================================================

    print(
        f"Supply ID:            "
        f"{data['supply_id']}"
    )

    print(
        f"Name:                 "
        f"{data['name']}"
    )

    print(
        f"Type:                 "
        f"{data['supply_type']}"
    )

    print()

    print(
        f"Latitude:             "
        f"{data['latitude']}"
    )

    print(
        f"Longitude:            "
        f"{data['longitude']}"
    )

    print()

    print(
        f"Total capacity:       "
        f"{data['total_capacity']}"
    )

    print(
        f"Ban capacity:         "
        f"{data['ban_capacity']}"
    )

    print()

    print(
        f"Total status:         "
        f"{data['total_capacity_status']}"
    )

    print(
        f"Ban status:           "
        f"{data['ban_capacity_status']}"
    )

    print()

    print(
        f"Street:               "
        f"{data['street_name']}"
    )

    print(
        f"Segment ID:           "
        f"{data['segment_id']}"
    )

    print()

    print(
        f"Ban type:             "
        f"{data['ban_type']}"
    )

    print(
        f"Restricted side:      "
        f"{data['restricted_side']}"
    )

    print()

    print(
        f"Segment length:       "
        f"{data['segment_length_meters']} m"
    )

    print(
        f"Usable length:        "
        f"{data['usable_length_meters']} m"
    )

    print(
        f"Modeled space length: "
        f"{data['assumed_space_length_meters']} m"
    )

    print()

    print(
        f"Methodology:          "
        f"{data['methodology']}"
    )

    print(
        f"Notes:                "
        f"{data['notes']}"
    )

    print()


    # ========================================================
    # Model tests
    # ========================================================

    tests = []


    # Test 1
    tests.append(
        (
            "Supply ID",
            data["supply_id"]
            == "test-street-supply-001",
        )
    )


    # Test 2
    tests.append(
        (
            "Supply type",
            data["supply_type"]
            == STREET_SEGMENT,
        )
    )


    # Test 3
    tests.append(
        (
            "Total capacity",
            data["total_capacity"]
            == 20,
        )
    )


    # Test 4
    tests.append(
        (
            "Ban capacity",
            data["ban_capacity"]
            == 10,
        )
    )


    # Test 5
    tests.append(
        (
            "Total capacity status",
            data["total_capacity_status"]
            == ESTIMATED,
        )
    )


    # Test 6
    tests.append(
        (
            "Ban capacity status",
            data["ban_capacity_status"]
            == ESTIMATED,
        )
    )


    # Test 7
    tests.append(
        (
            "Street relationship",
            (
                data["street_name"]
                == "TEST STREET"
                and data["segment_id"]
                == 123456
            ),
        )
    )


    # Test 8
    tests.append(
        (
            "Winter restriction",
            (
                data["ban_type"]
                == "DECLARED"
                and data["restricted_side"]
                == "EVEN"
            ),
        )
    )


    # Test 9
    tests.append(
        (
            "Segment length",
            data["segment_length_meters"]
            == 120.0,
        )
    )


    # Test 10
    tests.append(
        (
            "Usable length",
            data["usable_length_meters"]
            == 100.0,
        )
    )


    # Test 11
    tests.append(
        (
            "Space length assumption",
            data[
                "assumed_space_length_meters"
            ]
            == 5.5,
        )
    )


    # Test 12
    tests.append(
        (
            "Capacity relationship",
            (
                data["ban_capacity"]
                <= data["total_capacity"]
            ),
        )
    )


    # Test 13
    tests.append(
        (
            "Usable length relationship",
            (
                data["usable_length_meters"]
                <= data["segment_length_meters"]
            ),
        )
    )


    # Test 14
    tests.append(
        (
            "Methodology retained",
            (
                isinstance(
                    data["methodology"],
                    str,
                )
                and data[
                    "methodology"
                ].strip()
                != ""
            ),
        )
    )


    # Test 15
    tests.append(
        (
            "Notes retained",
            (
                isinstance(
                    data["notes"],
                    str,
                )
                and data[
                    "notes"
                ].strip()
                != ""
            ),
        )
    )


    # ========================================================
    # Print individual test results
    # ========================================================

    print("MODEL CHECKS")
    print("============")
    print()

    for index, (
        test_name,
        passed,
    ) in enumerate(
        tests,
        start=1,
    ):
        result_text = (
            "PASS"
            if passed
            else "FAIL"
        )

        print(
            f"Test {index:02d} - "
            f"{test_name}: "
            f"{result_text}"
        )


    # ========================================================
    # Summary
    # ========================================================

    total_tests = len(
        tests
    )

    passed_tests = sum(
        1
        for _, passed in tests
        if passed
    )

    failed_tests = (
        total_tests
        - passed_tests
    )

    print()
    print(
        "==================================="
    )

    print(
        "BANREADY SUPPLY MODEL TEST SUMMARY"
    )

    print(
        "==================================="
    )

    print()

    print(
        f"Total tests: "
        f"{total_tests}"
    )

    print(
        f"Passed:      "
        f"{passed_tests}"
    )

    print(
        f"Failed:      "
        f"{failed_tests}"
    )

    print()

    if failed_tests == 0:
        print(
            "SUPPLY MODEL TEST PASSED"
        )

        print()

        print(
            "BanReady's parking supply model "
            "is ready for evidence classification."
        )

    else:
        print(
            "SUPPLY MODEL TEST FAILED"
        )

        print()

        print(
            "Do not proceed to real Worcester "
            "parking-supply data until every "
            "model test passes."
        )


# ============================================================
# Run test
# ============================================================

if __name__ == "__main__":
    main()