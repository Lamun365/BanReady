import sys
from pathlib import Path


# ============================================================
# Project setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.services.destination_engine import (
    find_nearby_destinations,
    find_winter_ban_parking_options,
    load_parking_destinations,
)


# ============================================================
# Controlled Worcester test coordinate
#
# This is the verified Conway Street RIGHT-side point
# previously used for the real MUST_MOVE iPhone test.
# ============================================================

CONWAY_LATITUDE = 42.219500116630
CONWAY_LONGITUDE = -71.796851990903


# ============================================================
# Test helper
# ============================================================

def print_options(result):
    print(
        f"Candidate count: {result.candidate_count}"
    )

    print(
        f"Returned count:  {result.returned_count}"
    )

    print(
        f"Reason:          {result.reason}"
    )

    print()

    for index, option in enumerate(
        result.options,
        start=1,
    ):
        print(
            f"Option {index}"
        )

        print("-" * 35)

        print(
            f"Parking ID:        "
            f"{option.parking_id}"
        )

        print(
            f"Name:              "
            f"{option.name}"
        )

        print(
            f"Type:              "
            f"{option.destination_type}"
        )

        print(
            f"Address:           "
            f"{option.address}"
        )

        print(
            f"Distance:          "
            f"{option.distance_meters:.2f} m"
        )

        print(
            f"Distance km:       "
            f"{option.distance_km:.3f} km"
        )

        print(
            f"Verification:      "
            f"{option.verification_status}"
        )

        print(
            f"Ban evidence:      "
            f"{option.ban_available}"
        )

        print(
            f"Live availability: "
            f"{option.availability_status}"
        )

        print(
            f"Total capacity:    "
            f"{option.total_capacity}"
        )

        print(
            f"Ban capacity:      "
            f"{option.ban_capacity}"
        )

        print()


# ============================================================
# Main test suite
# ============================================================

def main():
    print()
    print("BanReady Destination Engine Test Suite")
    print("======================================")
    print()

    results = []


    # ========================================================
    # TEST 1
    #
    # Search from the real Conway MUST_MOVE coordinate.
    #
    # Current processed data contains five verified garages
    # with historical winter-ban evidence.
    #
    # Expected:
    #
    # candidate_count = 5
    # returned_count = 5
    # ========================================================

    print("Test 1 - Conway winter-ban parking options")
    print("-------------------------------------------")
    print()

    result = find_winter_ban_parking_options(
        latitude=CONWAY_LATITUDE,
        longitude=CONWAY_LONGITUDE,
        limit=5,
    )

    print_options(
        result
    )

    test_1_passed = (
        result.candidate_count == 5
        and result.returned_count == 5
    )

    print(
        "Result:",
        "PASS" if test_1_passed else "FAIL",
    )

    results.append(
        test_1_passed
    )


    # ========================================================
    # TEST 2
    #
    # Every resident-facing result must currently be:
    #
    # VERIFIED
    # ban_available == True
    #
    # ========================================================

    print()
    print("Test 2 - Eligibility safety")
    print("---------------------------")
    print()

    eligibility_passed = True

    for option in result.options:
        if (
            option.verification_status
            != "VERIFIED"
        ):
            eligibility_passed = False

        if option.ban_available is not True:
            eligibility_passed = False

    print(
        "Every returned destination is VERIFIED:",
        eligibility_passed,
    )

    print(
        "Every returned destination has "
        "winter-ban evidence:",
        eligibility_passed,
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if eligibility_passed
            else "FAIL"
        ),
    )

    results.append(
        eligibility_passed
    )


    # ========================================================
    # TEST 3
    #
    # Distances must be sorted nearest to farthest.
    # ========================================================

    print()
    print("Test 3 - Distance ordering")
    print("--------------------------")
    print()

    distances = [
        option.distance_meters
        for option in result.options
    ]

    sorted_distances = sorted(
        distances
    )

    ordering_passed = (
        distances == sorted_distances
    )

    print(
        "Distances returned:"
    )

    for distance in distances:
        print(
            f"{distance:.2f} m"
        )

    print()

    print(
        "Nearest-to-farthest ordering:",
        ordering_passed,
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if ordering_passed
            else "FAIL"
        ),
    )

    results.append(
        ordering_passed
    )


    # ========================================================
    # TEST 4
    #
    # Capacity must remain unknown during Milestone 8.
    #
    # We must not accidentally create fake supply values.
    # ========================================================

    print()
    print("Test 4 - Capacity remains unknown")
    print("---------------------------------")
    print()

    capacity_passed = True

    for option in result.options:
        if option.total_capacity is not None:
            capacity_passed = False

        if option.ban_capacity is not None:
            capacity_passed = False

    print(
        "All total capacities are None:",
        capacity_passed,
    )

    print(
        "All ban capacities are None:",
        capacity_passed,
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if capacity_passed
            else "FAIL"
        ),
    )

    results.append(
        capacity_passed
    )


    # ========================================================
    # TEST 5
    #
    # Verify the result limit works.
    #
    # Expected:
    #
    # candidate_count = 5
    # returned_count = 2
    # ========================================================

    print()
    print("Test 5 - Result limit")
    print("---------------------")
    print()

    limited_result = (
        find_winter_ban_parking_options(
            latitude=CONWAY_LATITUDE,
            longitude=CONWAY_LONGITUDE,
            limit=2,
        )
    )

    print(
        f"Candidate count: "
        f"{limited_result.candidate_count}"
    )

    print(
        f"Returned count:  "
        f"{limited_result.returned_count}"
    )

    limit_passed = (
        limited_result.candidate_count == 5
        and limited_result.returned_count == 2
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if limit_passed
            else "FAIL"
        ),
    )

    results.append(
        limit_passed
    )


    # ========================================================
    # TEST 6
    #
    # Use a deliberately tiny search radius.
    #
    # We expect no verified garage to fall within 10 meters
    # of the Conway test coordinate.
    # ========================================================

    print()
    print("Test 6 - Tiny search radius")
    print("---------------------------")
    print()

    tiny_radius_result = (
        find_winter_ban_parking_options(
            latitude=CONWAY_LATITUDE,
            longitude=CONWAY_LONGITUDE,
            limit=5,
            max_distance_meters=10.0,
        )
    )

    print(
        f"Candidate count: "
        f"{tiny_radius_result.candidate_count}"
    )

    print(
        f"Returned count:  "
        f"{tiny_radius_result.returned_count}"
    )

    tiny_radius_passed = (
        tiny_radius_result.candidate_count == 0
        and tiny_radius_result.returned_count == 0
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if tiny_radius_passed
            else "FAIL"
        ),
    )

    results.append(
        tiny_radius_passed
    )


    # ========================================================
    # TEST 7
    #
    # Invalid coordinate.
    #
    # Expected:
    #
    # no destinations
    # ========================================================

    print()
    print("Test 7 - Invalid coordinate")
    print("---------------------------")
    print()

    destinations = (
        load_parking_destinations()
    )

    invalid_result = (
        find_nearby_destinations(
            latitude=100.0,
            longitude=-71.80,
            destinations=destinations,
        )
    )

    print(
        f"Candidate count: "
        f"{invalid_result.candidate_count}"
    )

    print(
        f"Returned count:  "
        f"{invalid_result.returned_count}"
    )

    print(
        f"Reason: "
        f"{invalid_result.reason}"
    )

    invalid_passed = (
        invalid_result.candidate_count == 0
        and invalid_result.returned_count == 0
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if invalid_passed
            else "FAIL"
        ),
    )

    results.append(
        invalid_passed
    )


    # ========================================================
    # TEST 8
    #
    # Confirm municipal lots are excluded from the current
    # resident-facing winter-ban search.
    #
    # All current eligible destinations should be garages.
    # ========================================================

    print()
    print("Test 8 - Municipal lots excluded")
    print("--------------------------------")
    print()

    lots_excluded_passed = True

    for option in result.options:
        if (
            option.destination_type
            != "MUNICIPAL_GARAGE"
        ):
            lots_excluded_passed = False

    print(
        "Only municipal garages returned:",
        lots_excluded_passed,
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if lots_excluded_passed
            else "FAIL"
        ),
    )

    results.append(
        lots_excluded_passed
    )


    # ========================================================
    # TEST SUMMARY
    # ========================================================

    total_tests = len(
        results
    )

    passed_tests = sum(
        results
    )

    failed_tests = (
        total_tests
        - passed_tests
    )

    print()
    print("======================================")
    print("BANREADY DESTINATION TEST SUMMARY")
    print("======================================")
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
            "ALL DESTINATION ENGINE TESTS PASSED"
        )

        print()

        print(
            "BanReady can safely search and rank "
            "the current verified winter-ban "
            "parking destinations."
        )

    else:
        print(
            "SOME DESTINATION ENGINE TESTS FAILED"
        )

        print()

        print(
            "Do not expose destination search "
            "through FastAPI until the failures "
            "are resolved."
        )


if __name__ == "__main__":
    main()