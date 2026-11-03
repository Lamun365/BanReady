import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT)
    )


from backend.app.services.side_engine import (
    LEFT,
    ON_CENTERLINE,
    RIGHT,
    determine_side_of_linestring,
)


def run_test(
    name,
    expected,
    latitude,
    longitude,
    coordinates,
):
    result = determine_side_of_linestring(
        latitude,
        longitude,
        coordinates,
    )

    passed = (
        result.geometric_side
        == expected
    )

    print()
    print(name)
    print("-" * len(name))

    print(
        f"Expected: {expected}"
    )

    print(
        f"Actual:   {result.geometric_side}"
    )

    print(
        f"Distance: {result.distance_meters:.2f} m"
    )

    print(
        "Result:",
        "PASS" if passed else "FAIL"
    )

    return passed


def main():

    print()
    print("BanReady Side Engine Test Suite")
    print("===============================")

    results = []


    # --------------------------------------------------
    # Synthetic northbound street.
    #
    # GeoJSON:
    # longitude, latitude
    #
    # Direction:
    # south -> north
    # --------------------------------------------------

    street = [
        [-71.800000, 42.260000],
        [-71.800000, 42.261000],
    ]


    # --------------------------------------------------
    # TEST 1
    #
    # West of northbound street.
    # Expected LEFT.
    # --------------------------------------------------

    results.append(
        run_test(
            name="Test 1 - Left side",
            expected=LEFT,
            latitude=42.2605,
            longitude=-71.8001,
            coordinates=street,
        )
    )


    # --------------------------------------------------
    # TEST 2
    #
    # East of northbound street.
    # Expected RIGHT.
    # --------------------------------------------------

    results.append(
        run_test(
            name="Test 2 - Right side",
            expected=RIGHT,
            latitude=42.2605,
            longitude=-71.7999,
            coordinates=street,
        )
    )


    # --------------------------------------------------
    # TEST 3
    #
    # Exactly on centerline.
    # --------------------------------------------------

    results.append(
        run_test(
            name="Test 3 - On centerline",
            expected=ON_CENTERLINE,
            latitude=42.2605,
            longitude=-71.8000,
            coordinates=street,
        )
    )


    # --------------------------------------------------
    # TEST 4
    #
    # Reverse line direction.
    #
    # The same physical west-side point should now
    # geometrically be RIGHT because line orientation
    # has reversed.
    #
    # This test proves LEFT/RIGHT is dependent on
    # LineString direction.
    # --------------------------------------------------

    reversed_street = list(
        reversed(street)
    )

    results.append(
        run_test(
            name="Test 4 - Reversed street direction",
            expected=RIGHT,
            latitude=42.2605,
            longitude=-71.8001,
            coordinates=reversed_street,
        )
    )


    # --------------------------------------------------
    # Summary
    # --------------------------------------------------

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print()
    print("===============================")
    print("BANREADY SIDE TEST SUMMARY")
    print("===============================")
    print()

    print(
        f"Total tests: {total}"
    )

    print(
        f"Passed:      {passed}"
    )

    print(
        f"Failed:      {failed}"
    )

    print()

    if failed == 0:
        print("ALL SIDE TESTS PASSED")
    else:
        print("SOME SIDE TESTS FAILED")


if __name__ == "__main__":
    main()