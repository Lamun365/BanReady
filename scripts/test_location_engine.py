import json
import sys
from pathlib import Path


# ============================================================
# Project setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.services.location_engine import (
    find_nearest_street,
    normalize_line_coordinates,
)


# ============================================================
# Data file
# ============================================================

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)


# ============================================================
# Test helper
# ============================================================

def print_result(result):
    print(f"Matched:         {result.matched}")
    print(f"Street:          {result.street_name}")
    print(f"Segment ID:      {result.segment_id}")
    print(f"Street ID:       {result.street_id}")
    print(f"Ban Type:        {result.ban_type}")
    print(f"Ban Zone:        {result.ban_zone}")
    print(f"Restricted Side: {result.restricted_side}")

    if result.distance_meters == float("inf"):
        print("Distance:        Infinity")
    else:
        print(
            f"Distance:        "
            f"{result.distance_meters:.2f} m"
        )

    print(f"Reason:          {result.reason}")


# ============================================================
# Find test point from a specific segment
# ============================================================

def get_first_coordinate(feature):
    geometry = feature.get(
        "geometry",
        {},
    )

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    lines = normalize_line_coordinates(
        coordinates
    )

    for line in lines:
        if not line:
            continue

        first_point = line[0]

        if len(first_point) < 2:
            continue

        longitude = first_point[0]
        latitude = first_point[1]

        if (
            isinstance(latitude, (int, float))
            and isinstance(longitude, (int, float))
        ):
            return latitude, longitude

    return None


# ============================================================
# Main test suite
# ============================================================

def main():
    print()
    print("BanReady Location Engine Test Suite")
    print("===================================")
    print()

    # --------------------------------------------------------
    # Load Worcester parking data
    # --------------------------------------------------------

    if not PARKING_FILE.exists():
        print("ERROR: Parking-ban data not found.")
        print(f"Expected file: {PARKING_FILE}")
        return

    try:
        with open(
            PARKING_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            parking_data = json.load(file)

    except json.JSONDecodeError:
        print(
            "ERROR: Parking-ban GeoJSON "
            "could not be read."
        )
        return

    features = parking_data.get(
        "features",
        [],
    )

    if not features:
        print(
            "ERROR: No Worcester parking "
            "features found."
        )
        return

    print(
        f"Loaded {len(features)} "
        "Worcester parking-ban segments."
    )

    print()

    results = []


    # ========================================================
    # TEST 1
    #
    # Controlled Rose Lane coordinate.
    #
    # This exact coordinate came from the Worcester
    # ROSE LN geometry during our earlier inspection.
    #
    # Expected:
    # matched = True
    # street = ROSE LN
    # segment = 821519
    # distance approximately 0 meters
    # ========================================================

    print("Test 1 - Known Rose Lane coordinate")
    print("-----------------------------------")

    rose_latitude = 42.211284604405
    rose_longitude = -71.795189475878

    rose_result = find_nearest_street(
        latitude=rose_latitude,
        longitude=rose_longitude,
        parking_features=features,
    )

    print_result(
        rose_result
    )

    rose_passed = (
        rose_result.matched
        and rose_result.street_name == "ROSE LN"
        and rose_result.segment_id == 821519
        and rose_result.distance_meters < 0.5
    )

    print()

    print(
        "Result:",
        "PASS" if rose_passed else "FAIL",
    )

    results.append(
        rose_passed
    )


    # ========================================================
    # TEST 2
    #
    # A coordinate intentionally far away from Worcester.
    #
    # The engine must NOT simply return the nearest Worcester
    # street as if the match were reliable.
    #
    # Expected:
    # matched = False
    # ========================================================

    print()
    print("Test 2 - Far-away coordinate rejection")
    print("--------------------------------------")

    far_result = find_nearest_street(
        latitude=40.7128,
        longitude=-74.0060,
        parking_features=features,
    )

    print_result(
        far_result
    )

    far_passed = (
        not far_result.matched
    )

    print()

    print(
        "Result:",
        "PASS" if far_passed else "FAIL",
    )

    results.append(
        far_passed
    )


    # ========================================================
    # TEST 3
    #
    # MultiLineString validation using GRANITE ST.
    #
    # We find Granite's real segment, extract a coordinate
    # directly from its geometry, and ask location_engine
    # to match that coordinate.
    #
    # Expected:
    # matched = True
    # street = GRANITE ST
    # segment = 821525
    # ========================================================

    print()
    print("Test 3 - Granite MultiLineString")
    print("--------------------------------")

    granite_feature = None

    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        if (
            properties.get("segment_id")
            == 821525
        ):
            granite_feature = feature
            break

    if granite_feature is None:
        print(
            "ERROR: Granite Street segment "
            "821525 was not found."
        )

        granite_passed = False

    else:
        granite_coordinate = get_first_coordinate(
            granite_feature
        )

        if granite_coordinate is None:
            print(
                "ERROR: Could not extract a usable "
                "Granite Street coordinate."
            )

            granite_passed = False

        else:
            (
                granite_latitude,
                granite_longitude,
            ) = granite_coordinate

            print(
                f"Test latitude:  "
                f"{granite_latitude}"
            )

            print(
                f"Test longitude: "
                f"{granite_longitude}"
            )

            print()

            granite_result = find_nearest_street(
                latitude=granite_latitude,
                longitude=granite_longitude,
                parking_features=features,
            )

            print_result(
                granite_result
            )

            granite_passed = (
                granite_result.matched
                and granite_result.street_name
                == "GRANITE ST"
                and granite_result.segment_id
                == 821525
                and granite_result.distance_meters
                < 0.5
            )

    print()

    print(
        "Result:",
        "PASS" if granite_passed else "FAIL",
    )

    results.append(
        granite_passed
    )


    # ========================================================
    # TEST 4
    #
    # Invalid latitude.
    #
    # Expected:
    # matched = False
    # ========================================================

    print()
    print("Test 4 - Invalid latitude")
    print("-------------------------")

    invalid_latitude_result = find_nearest_street(
        latitude=100.0,
        longitude=-71.80,
        parking_features=features,
    )

    print_result(
        invalid_latitude_result
    )

    invalid_latitude_passed = (
        not invalid_latitude_result.matched
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if invalid_latitude_passed
            else "FAIL"
        ),
    )

    results.append(
        invalid_latitude_passed
    )


    # ========================================================
    # TEST 5
    #
    # Invalid longitude.
    #
    # Expected:
    # matched = False
    # ========================================================

    print()
    print("Test 5 - Invalid longitude")
    print("--------------------------")

    invalid_longitude_result = find_nearest_street(
        latitude=42.26,
        longitude=-200.0,
        parking_features=features,
    )

    print_result(
        invalid_longitude_result
    )

    invalid_longitude_passed = (
        not invalid_longitude_result.matched
    )

    print()

    print(
        "Result:",
        (
            "PASS"
            if invalid_longitude_passed
            else "FAIL"
        ),
    )

    results.append(
        invalid_longitude_passed
    )


    # ========================================================
    # Summary
    # ========================================================

    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = (
        total_tests - passed_tests
    )

    print()
    print("===================================")
    print("BANREADY LOCATION TEST SUMMARY")
    print("===================================")
    print()

    print(
        f"Total tests: {total_tests}"
    )

    print(
        f"Passed:      {passed_tests}"
    )

    print(
        f"Failed:      {failed_tests}"
    )

    print()

    if failed_tests == 0:
        print(
            "ALL LOCATION ENGINE TESTS PASSED"
        )

        print()

        print(
            "BanReady's reusable backend street "
            "matcher is ready for API integration."
        )

    else:
        print(
            "SOME LOCATION ENGINE TESTS FAILED"
        )

        print()

        print(
            "Do not create the parking-check API "
            "endpoint until the failures are fixed."
        )


# ============================================================
# Run suite
# ============================================================

if __name__ == "__main__":
    main()