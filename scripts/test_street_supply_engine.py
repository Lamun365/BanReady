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

from backend.app.services.street_supply_engine import (
    BOTH,
    EVEN,
    NONE,
    ODD,
    calculate_ban_capacity,
    calculate_geometry_length_meters,
    estimate_capacity_from_length,
    estimate_street_supply,
    side_is_restricted,
    validate_usable_length,
)


# ============================================================
# Synthetic geometries
#
# These are test geometries only.
# They are not Worcester street records.
# ============================================================

SYNTHETIC_LINESTRING = {
    "type": "LineString",
    "coordinates": [
        [-71.800000, 42.260000],
        [-71.799000, 42.260000],
    ],
}


SYNTHETIC_MULTILINESTRING = {
    "type": "MultiLineString",
    "coordinates": [
        [
            [-71.800000, 42.260000],
            [-71.799500, 42.260000],
        ],
        [
            [-71.799500, 42.260000],
            [-71.799000, 42.260000],
        ],
    ],
}


# ============================================================
# Test helper
# ============================================================

def print_test(
    number,
    name,
    passed,
):
    result = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"Test {number:02d} - "
        f"{name}: "
        f"{result}"
    )


# ============================================================
# Main test suite
# ============================================================

def main():
    print()
    print(
        "BanReady Street Supply Engine Test Suite"
    )

    print(
        "========================================"
    )

    print()

    results = []


    # ========================================================
    # TEST 1
    #
    # LineString geometry length.
    # ========================================================

    line_length = (
        calculate_geometry_length_meters(
            SYNTHETIC_LINESTRING
        )
    )

    print(
        f"Synthetic LineString length: "
        f"{line_length:.2f} m"
    )

    test_1 = (
        line_length > 0
    )

    results.append(
        (
            "LineString length",
            test_1,
        )
    )


    # ========================================================
    # TEST 2
    #
    # MultiLineString geometry length.
    #
    # The synthetic MultiLineString represents the same
    # overall line as the LineString.
    # ========================================================

    multiline_length = (
        calculate_geometry_length_meters(
            SYNTHETIC_MULTILINESTRING
        )
    )

    print(
        f"Synthetic MultiLineString length: "
        f"{multiline_length:.2f} m"
    )

    test_2 = (
        multiline_length > 0
        and abs(
            multiline_length
            - line_length
        )
        < 1.0
    )

    results.append(
        (
            "MultiLineString length",
            test_2,
        )
    )


    # ========================================================
    # TEST 3
    #
    # Capacity estimate uses floor().
    #
    # 100 / 5.5 = 18.18...
    #
    # Expected:
    # 18 vehicles
    # ========================================================

    estimated_capacity = (
        estimate_capacity_from_length(
            usable_length_meters=100.0,
            assumed_space_length_meters=5.5,
        )
    )

    print(
        f"Synthetic 100 m capacity: "
        f"{estimated_capacity}"
    )

    test_3 = (
        estimated_capacity == 18
    )

    results.append(
        (
            "Capacity floor calculation",
            test_3,
        )
    )


    # ========================================================
    # TEST 4
    #
    # EVEN restriction should identify EVEN as restricted.
    # ========================================================

    test_4 = (
        side_is_restricted(
            EVEN,
            EVEN,
        )
        is True
        and side_is_restricted(
            ODD,
            EVEN,
        )
        is False
    )

    results.append(
        (
            "EVEN restriction detection",
            test_4,
        )
    )


    # ========================================================
    # TEST 5
    #
    # EVEN normal capacity should become zero during
    # an EVEN-side active ban.
    # ========================================================

    even_ban_capacity = (
        calculate_ban_capacity(
            normal_capacity=18,
            side=EVEN,
            restricted_side=EVEN,
        )
    )

    odd_ban_capacity = (
        calculate_ban_capacity(
            normal_capacity=18,
            side=ODD,
            restricted_side=EVEN,
        )
    )

    test_5 = (
        even_ban_capacity == 0
        and odd_ban_capacity == 18
    )

    results.append(
        (
            "EVEN ban transformation",
            test_5,
        )
    )


    # ========================================================
    # TEST 6
    #
    # BOTH restriction removes both sides.
    # ========================================================

    test_6 = (
        calculate_ban_capacity(
            normal_capacity=10,
            side=ODD,
            restricted_side=BOTH,
        )
        == 0
        and calculate_ban_capacity(
            normal_capacity=12,
            side=EVEN,
            restricted_side=BOTH,
        )
        == 0
    )

    results.append(
        (
            "BOTH sides restricted",
            test_6,
        )
    )


    # ========================================================
    # TEST 7
    #
    # NONE restriction preserves normal capacity.
    # ========================================================

    test_7 = (
        calculate_ban_capacity(
            normal_capacity=10,
            side=ODD,
            restricted_side=NONE,
        )
        == 10
        and calculate_ban_capacity(
            normal_capacity=12,
            side=EVEN,
            restricted_side=NONE,
        )
        == 12
    )

    results.append(
        (
            "NONE restriction preserves supply",
            test_7,
        )
    )


    # ========================================================
    # TEST 8
    #
    # Usable curb length cannot exceed segment length.
    # ========================================================

    test_8 = (
        validate_usable_length(
            segment_length_meters=100.0,
            usable_length_meters=101.0,
        )
        is False
    )

    results.append(
        (
            "Reject excessive usable length",
            test_8,
        )
    )


    # ========================================================
    # TEST 9
    #
    # Negative usable curb length must be rejected.
    # ========================================================

    test_9 = (
        validate_usable_length(
            segment_length_meters=100.0,
            usable_length_meters=-1.0,
        )
        is False
    )

    results.append(
        (
            "Reject negative usable length",
            test_9,
        )
    )


    # ========================================================
    # TEST 10
    #
    # Complete synthetic street estimate.
    #
    # Geometry length is approximately 82 m.
    #
    # Use:
    # ODD usable curb = 60 m
    # EVEN usable curb = 55 m
    # space length = 5.5 m
    #
    # Normal:
    # ODD  = floor(60 / 5.5) = 10
    # EVEN = floor(55 / 5.5) = 10
    #
    # Total normal = 20
    #
    # EVEN restricted:
    # ODD ban  = 10
    # EVEN ban = 0
    #
    # Total ban = 10
    # displaced capacity = 10
    # ========================================================

    street_result = (
        estimate_street_supply(
            street_name="SYNTHETIC STREET",
            segment_id=999999,
            geometry=SYNTHETIC_LINESTRING,
            ban_type="DECLARED",
            restricted_side=EVEN,
            odd_usable_length_meters=60.0,
            even_usable_length_meters=55.0,
            assumed_space_length_meters=5.5,
        )
    )

    print()
    print(
        "Synthetic full street result"
    )

    print(
        "----------------------------"
    )

    print(
        f"Segment length: "
        f"{street_result.segment_length_meters:.2f} m"
    )

    print(
        f"ODD normal capacity: "
        f"{street_result.odd.normal_capacity}"
    )

    print(
        f"EVEN normal capacity: "
        f"{street_result.even.normal_capacity}"
    )

    print(
        f"Total normal capacity: "
        f"{street_result.total_normal_capacity}"
    )

    print(
        f"ODD ban capacity: "
        f"{street_result.odd.ban_capacity}"
    )

    print(
        f"EVEN ban capacity: "
        f"{street_result.even.ban_capacity}"
    )

    print(
        f"Total ban capacity: "
        f"{street_result.total_ban_capacity}"
    )

    print(
        f"Displaced capacity: "
        f"{street_result.displaced_capacity}"
    )

    print()

    test_10 = (
        street_result.odd.normal_capacity
        == 10
        and street_result.even.normal_capacity
        == 10
        and street_result.total_normal_capacity
        == 20
        and street_result.odd.ban_capacity
        == 10
        and street_result.even.ban_capacity
        == 0
        and street_result.total_ban_capacity
        == 10
        and street_result.displaced_capacity
        == 10
    )

    results.append(
        (
            "Complete street estimate",
            test_10,
        )
    )


    # ========================================================
    # TEST 11
    #
    # Ban capacity must never exceed normal capacity.
    # ========================================================

    test_11 = (
        street_result.total_ban_capacity
        <= street_result.total_normal_capacity
        and street_result.odd.ban_capacity
        <= street_result.odd.normal_capacity
        and street_result.even.ban_capacity
        <= street_result.even.normal_capacity
    )

    results.append(
        (
            "Ban capacity relationship",
            test_11,
        )
    )


    # ========================================================
    # TEST 12
    #
    # Estimated capacity evidence should remain ESTIMATED.
    # ========================================================

    test_12 = (
        street_result.capacity_status
        == "ESTIMATED"
        and street_result.odd.normal_capacity_status
        == "ESTIMATED"
        and street_result.odd.ban_capacity_status
        == "ESTIMATED"
        and street_result.even.normal_capacity_status
        == "ESTIMATED"
        and street_result.even.ban_capacity_status
        == "ESTIMATED"
    )

    results.append(
        (
            "Evidence status remains ESTIMATED",
            test_12,
        )
    )


    # ========================================================
    # TEST 13
    #
    # Invalid usable length should raise ValueError through
    # the complete street estimation pipeline.
    # ========================================================

    invalid_usable_length_rejected = False

    try:
        estimate_street_supply(
            street_name="INVALID STREET",
            segment_id=111111,
            geometry=SYNTHETIC_LINESTRING,
            ban_type="DECLARED",
            restricted_side=EVEN,
            odd_usable_length_meters=500.0,
            even_usable_length_meters=50.0,
            assumed_space_length_meters=5.5,
        )

    except ValueError:
        invalid_usable_length_rejected = True

    test_13 = (
        invalid_usable_length_rejected
    )

    results.append(
        (
            "Invalid curb input rejected",
            test_13,
        )
    )


    # ========================================================
    # TEST 14
    #
    # Invalid parking-space assumption should be rejected.
    # ========================================================

    invalid_space_length_rejected = False

    try:
        estimate_capacity_from_length(
            usable_length_meters=50.0,
            assumed_space_length_meters=0.0,
        )

    except ValueError:
        invalid_space_length_rejected = True

    test_14 = (
        invalid_space_length_rejected
    )

    results.append(
        (
            "Invalid space length rejected",
            test_14,
        )
    )


    # ========================================================
    # TEST 15
    #
    # Methodology must be retained so an ESTIMATED result
    # remains reproducible and auditable.
    # ========================================================

    test_15 = (
        isinstance(
            street_result.methodology,
            str,
        )
        and street_result.methodology.strip()
        != ""
        and isinstance(
            street_result.odd.methodology,
            str,
        )
        and street_result.odd.methodology.strip()
        != ""
        and isinstance(
            street_result.even.methodology,
            str,
        )
        and street_result.even.methodology.strip()
        != ""
    )

    results.append(
        (
            "Methodology retained",
            test_15,
        )
    )


    # ========================================================
    # Print results
    # ========================================================

    print("ENGINE CHECKS")
    print("=============")
    print()

    for index, (
        name,
        passed,
    ) in enumerate(
        results,
        start=1,
    ):
        print_test(
            index,
            name,
            passed,
        )


    # ========================================================
    # Summary
    # ========================================================

    total_tests = len(
        results
    )

    passed_tests = sum(
        1
        for _, passed
        in results
        if passed
    )

    failed_tests = (
        total_tests
        - passed_tests
    )

    print()
    print(
        "======================================="
    )

    print(
        "BANREADY STREET SUPPLY TEST SUMMARY"
    )

    print(
        "======================================="
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
            "ALL STREET SUPPLY ENGINE TESTS PASSED"
        )

        print()

        print(
            "BanReady's street-supply engine "
            "is ready for a controlled Worcester "
            "street prototype."
        )

    else:
        print(
            "STREET SUPPLY ENGINE TESTS FAILED"
        )

        print()

        print(
            "Do not apply the engine to real "
            "Worcester street supply until every "
            "test passes."
        )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
