import json
import math
import sys
from pathlib import Path


# ============================================================
# Project imports
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.services.parking_status_engine import (
    evaluate_vehicle_parking_status,
)

from backend.app.services.side_engine import (
    normalize_line_coordinates,
)


# ============================================================
# Data files
# ============================================================

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

ADDRESS_FILE = Path(
    "data/raw/worcester/address_points/Address_Points.geojson"
)


# ============================================================
# Expected statuses
# ============================================================

MUST_MOVE = "MUST_MOVE"

CAN_STAY_DURING_BAN = "CAN_STAY_DURING_BAN"

NOT_AFFECTED = "NOT_AFFECTED"

VERIFY_RULE = "VERIFY_RULE"


# ============================================================
# Load GeoJSON
# ============================================================

def load_geojson(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


# ============================================================
# Find a specific Worcester parking-ban segment
# ============================================================

def find_segment(
    features,
    segment_id,
):
    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        if properties.get("segment_id") == segment_id:
            return feature

    return None


# ============================================================
# Find a usable section of street geometry
# ============================================================

def get_test_segment(
    street_feature,
):
    geometry = street_feature.get(
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
        if len(line) < 2:
            continue

        for index in range(
            len(line) - 1
        ):
            start = line[index]
            end = line[index + 1]

            if (
                len(start) < 2
                or len(end) < 2
            ):
                continue

            start_lon = start[0]
            start_lat = start[1]

            end_lon = end[0]
            end_lat = end[1]

            if not all(
                isinstance(value, (int, float))
                for value in (
                    start_lon,
                    start_lat,
                    end_lon,
                    end_lat,
                )
            ):
                continue

            # Avoid extremely short/zero-length pieces.
            if (
                start_lon == end_lon
                and start_lat == end_lat
            ):
                continue

            return (
                start_lat,
                start_lon,
                end_lat,
                end_lon,
            )

    return None


# ============================================================
# Generate test point beside a street
# ============================================================

def create_offset_point(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    side,
    offset_meters=8.0,
):
    """
    Create a point approximately offset from the midpoint
    of a street segment.

    side must be:

        LEFT
        RIGHT
    """

    earth_radius = 6371000.0

    reference_lat = (
        start_lat + end_lat
    ) / 2.0

    reference_lon = (
        start_lon + end_lon
    ) / 2.0

    # Convert start/end relative to midpoint.
    start_x = (
        math.radians(
            start_lon - reference_lon
        )
        * earth_radius
        * math.cos(
            math.radians(reference_lat)
        )
    )

    start_y = (
        math.radians(
            start_lat - reference_lat
        )
        * earth_radius
    )

    end_x = (
        math.radians(
            end_lon - reference_lon
        )
        * earth_radius
        * math.cos(
            math.radians(reference_lat)
        )
    )

    end_y = (
        math.radians(
            end_lat - reference_lat
        )
        * earth_radius
    )

    direction_x = end_x - start_x
    direction_y = end_y - start_y

    length = math.sqrt(
        direction_x * direction_x
        + direction_y * direction_y
    )

    if length == 0:
        raise ValueError(
            "Cannot create test point from "
            "zero-length street segment."
        )

    direction_x /= length
    direction_y /= length

    # Left-hand perpendicular.
    perpendicular_x = -direction_y
    perpendicular_y = direction_x

    if side == "RIGHT":
        perpendicular_x *= -1
        perpendicular_y *= -1

    elif side != "LEFT":
        raise ValueError(
            "side must be LEFT or RIGHT"
        )

    offset_x = (
        perpendicular_x
        * offset_meters
    )

    offset_y = (
        perpendicular_y
        * offset_meters
    )

    latitude = (
        reference_lat
        + math.degrees(
            offset_y / earth_radius
        )
    )

    longitude = (
        reference_lon
        + math.degrees(
            offset_x
            / (
                earth_radius
                * math.cos(
                    math.radians(
                        reference_lat
                    )
                )
            )
        )
    )

    return latitude, longitude


# ============================================================
# Run one integration test
# ============================================================

def run_test(
    test_name,
    street_feature,
    address_features,
    geometric_test_side,
    expected_status,
    declared_ban_active=False,
    snow_emergency_active=False,
    permanent_time_restriction_active=False,
):
    print()
    print(test_name)
    print("-" * len(test_name))

    properties = street_feature.get(
        "properties",
        {},
    )

    test_segment = get_test_segment(
        street_feature
    )

    if test_segment is None:
        print("Result: FAIL")
        print(
            "Reason: No usable geometry "
            "was found."
        )

        return False

    (
        start_lat,
        start_lon,
        end_lat,
        end_lon,
    ) = test_segment

    latitude, longitude = (
        create_offset_point(
            start_lat,
            start_lon,
            end_lat,
            end_lon,
            geometric_test_side,
        )
    )

    result = evaluate_vehicle_parking_status(
        latitude=latitude,
        longitude=longitude,
        street_feature=street_feature,
        address_features=address_features,
        declared_ban_active=(
            declared_ban_active
        ),
        snow_emergency_active=(
            snow_emergency_active
        ),
        permanent_time_restriction_active=(
            permanent_time_restriction_active
        ),
    )

    passed = (
        result.status
        == expected_status
    )

    print(
        f"Street:          "
        f"{result.street_name}"
    )

    print(
        f"Segment ID:      "
        f"{result.segment_id}"
    )

    print(
        f"Ban Type:        "
        f"{result.ban_type}"
    )

    print(
        f"Restricted Side: "
        f"{result.restricted_side}"
    )

    print()

    print(
        f"Requested Side:  "
        f"{geometric_test_side}"
    )

    print(
        f"Detected Side:   "
        f"{result.geometric_side}"
    )

    print(
        f"Parked Side:     "
        f"{result.parked_side}"
    )

    print()

    print(
        f"LEFT parity:     "
        f"{result.left_parity}"
    )

    print(
        f"RIGHT parity:    "
        f"{result.right_parity}"
    )

    print(
        f"Parity confidence: "
        f"{result.parity_confidence}"
    )

    print()

    print(
        f"Distance: "
        f"{result.distance_to_street_meters:.2f} m"
    )

    print()

    print(
        f"Expected Status: "
        f"{expected_status}"
    )

    print(
        f"Actual Status:   "
        f"{result.status}"
    )

    print()

    print(
        "Result:",
        "PASS" if passed else "FAIL"
    )

    print(
        f"Reason: {result.reason}"
    )

    return passed


# ============================================================
# Main integration suite
# ============================================================

def main():
    print()
    print(
        "BanReady Parking Status "
        "Integration Test"
    )

    print(
        "======================================"
    )

    print()

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    try:
        parking_data = load_geojson(
            PARKING_FILE
        )

        address_data = load_geojson(
            ADDRESS_FILE
        )

    except FileNotFoundError as error:
        print(f"ERROR: {error}")
        return

    except json.JSONDecodeError:
        print(
            "ERROR: A GeoJSON file "
            "could not be read."
        )
        return

    parking_features = (
        parking_data.get(
            "features",
            [],
        )
    )

    address_features = (
        address_data.get(
            "features",
            [],
        )
    )

    print(
        f"Parking segments: "
        f"{len(parking_features)}"
    )

    print(
        f"Address points:   "
        f"{len(address_features)}"
    )

    print()

    # --------------------------------------------------------
    # Find controlled test streets
    # --------------------------------------------------------

    conway = find_segment(
        parking_features,
        821528,
    )

    victoria = find_segment(
        parking_features,
        821579,
    )

    cliff = find_segment(
        parking_features,
        821534,
    )

    granite = find_segment(
        parking_features,
        821525,
    )

    abington = find_segment(
        parking_features,
        821757,
    )

    greenwood = find_segment(
        parking_features,
        821520,
    )

    required_segments = {
        "CONWAY ST": conway,
        "VICTORIA AVE": victoria,
        "CLIFF ST": cliff,
        "GRANITE ST": granite,
        "ABINGTON ST": abington,
        "GREENWOOD ST": greenwood,
    }

    missing = [
        name
        for name, feature
        in required_segments.items()
        if feature is None
    ]

    if missing:
        print(
            "ERROR: Required test segments "
            "were not found:"
        )

        for name in missing:
            print(f"  {name}")

        return

    results = []

    # ========================================================
    # TEST 1
    #
    # Conway:
    # LEFT = ODD
    # RIGHT = EVEN
    #
    # Declared restriction prohibits EVEN.
    #
    # Car on RIGHT -> EVEN -> MUST_MOVE
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 1 - Conway restricted EVEN side"
            ),
            street_feature=conway,
            address_features=address_features,
            geometric_test_side="RIGHT",
            expected_status=MUST_MOVE,
            declared_ban_active=True,
        )
    )

    # ========================================================
    # TEST 2
    #
    # Conway:
    # LEFT = ODD
    #
    # Restricted side = EVEN.
    #
    # Car on LEFT -> ODD -> CAN_STAY_DURING_BAN
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 2 - Conway allowed ODD side"
            ),
            street_feature=conway,
            address_features=address_features,
            geometric_test_side="LEFT",
            expected_status=CAN_STAY_DURING_BAN,
            declared_ban_active=True,
        )
    )

    # ========================================================
    # TEST 3
    #
    # Victoria:
    # LEFT = ODD
    # RIGHT = EVEN
    #
    # Restriction prohibits ODD.
    #
    # Car on LEFT -> ODD -> MUST_MOVE
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 3 - Victoria restricted ODD side"
            ),
            street_feature=victoria,
            address_features=address_features,
            geometric_test_side="LEFT",
            expected_status=MUST_MOVE,
            declared_ban_active=True,
        )
    )

    # ========================================================
    # TEST 4
    #
    # Victoria:
    # RIGHT = EVEN.
    #
    # Restriction prohibits ODD.
    #
    # Car on RIGHT -> EVEN -> CAN_STAY_DURING_BAN
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 4 - Victoria allowed EVEN side"
            ),
            street_feature=victoria,
            address_features=address_features,
            geometric_test_side="RIGHT",
            expected_status=CAN_STAY_DURING_BAN,
            declared_ban_active=True,
        )
    )

    # ========================================================
    # TEST 5
    #
    # Cliff is particularly important:
    #
    # LEFT = EVEN
    # RIGHT = ODD
    #
    # Restriction = BOTH.
    #
    # Regardless of parity, active declared ban -> MUST_MOVE
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 5 - Cliff both sides restricted"
            ),
            street_feature=cliff,
            address_features=address_features,
            geometric_test_side="LEFT",
            expected_status=MUST_MOVE,
            declared_ban_active=True,
        )
    )

    # ========================================================
    # TEST 6
    #
    # Granite:
    #
    # MultiLineString
    # LEFT = ODD
    # RIGHT = EVEN
    #
    # Permanent restriction prohibits EVEN.
    #
    # During snow emergency:
    # RIGHT -> EVEN -> MUST_MOVE
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 6 - Granite MultiLineString"
            ),
            street_feature=granite,
            address_features=address_features,
            geometric_test_side="RIGHT",
            expected_status=MUST_MOVE,
            snow_emergency_active=True,
        )
    )

    # ========================================================
    # TEST 7
    #
    # Abington:
    # LEFT = ODD
    # RIGHT = EVEN
    #
    # Permanent rule prohibits ODD.
    #
    # During active permanent time restriction:
    # LEFT -> ODD -> MUST_MOVE
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 7 - Abington permanent ODD"
            ),
            street_feature=abington,
            address_features=address_features,
            geometric_test_side="LEFT",
            expected_status=MUST_MOVE,
            permanent_time_restriction_active=True,
        )
    )

    # ========================================================
    # TEST 8
    #
    # Greenwood:
    #
    # MultiLineString
    # LEFT = EVEN
    # RIGHT = ODD
    #
    # Restriction = BOTH.
    #
    # During snow emergency -> MUST_MOVE.
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 8 - Greenwood MultiLineString both"
            ),
            street_feature=greenwood,
            address_features=address_features,
            geometric_test_side="RIGHT",
            expected_status=MUST_MOVE,
            snow_emergency_active=True,
        )
    )

    # ========================================================
    # TEST 9
    #
    # Declared rule exists but ban is inactive.
    #
    # Even if selected side would normally be restricted,
    # expected result is NOT_AFFECTED.
    # ========================================================

    results.append(
        run_test(
            test_name=(
                "Test 9 - Declared ban inactive"
            ),
            street_feature=conway,
            address_features=address_features,
            geometric_test_side="RIGHT",
            expected_status=NOT_AFFECTED,
            declared_ban_active=False,
        )
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
    print(
        "======================================"
    )

    print(
        "BANREADY INTEGRATION TEST SUMMARY"
    )

    print(
        "======================================"
    )

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
            "ALL INTEGRATION TESTS PASSED"
        )

        print()

        print(
            "BanReady successfully combined "
            "street geometry, address parity, "
            "and winter parking-ban rules."
        )

    else:
        print(
            "SOME INTEGRATION TESTS FAILED"
        )

        print()

        print(
            "Do not move to Milestone 6 "
            "until the failures are reviewed."
        )


# ============================================================
# Start program
# ============================================================

if __name__ == "__main__":
    main()