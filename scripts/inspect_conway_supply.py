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

from backend.app.services.street_supply_engine import (
    calculate_geometry_length_meters,
    normalize_geometry_lines,
)


# ============================================================
# Configuration
# ============================================================

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

TARGET_SEGMENT_ID = 821528

EXPECTED_STREET_NAME = "CONWAY ST"


# ============================================================
# Helpers
# ============================================================

def load_geojson(path):
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
            f"Could not read GeoJSON file: {path}"
        ) from error


def find_segment(
    features,
    segment_id,
):
    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        if (
            properties.get("segment_id")
            == segment_id
        ):
            return feature

    return None


def count_geometry_points(
    geometry,
):
    lines = normalize_geometry_lines(
        geometry
    )

    point_count = 0

    for line in lines:
        point_count += len(
            line
        )

    return point_count


def get_first_coordinate(
    geometry,
):
    lines = normalize_geometry_lines(
        geometry
    )

    for line in lines:
        if not line:
            continue

        point = line[0]

        if len(point) < 2:
            continue

        return {
            "longitude": point[0],
            "latitude": point[1],
        }

    return None


def get_last_coordinate(
    geometry,
):
    lines = normalize_geometry_lines(
        geometry
    )

    for line in reversed(
        lines
    ):
        if not line:
            continue

        point = line[-1]

        if len(point) < 2:
            continue

        return {
            "longitude": point[0],
            "latitude": point[1],
        }

    return None


def calculate_line_lengths(
    geometry,
):
    """
    Calculate the length of each individual line inside
    a LineString or MultiLineString geometry.
    """

    lines = normalize_geometry_lines(
        geometry
    )

    results = []

    for line_index, line in enumerate(
        lines,
        start=1,
    ):
        line_geometry = {
            "type": "LineString",
            "coordinates": line,
        }

        length = (
            calculate_geometry_length_meters(
                line_geometry
            )
        )

        results.append(
            {
                "line_number": line_index,
                "point_count": len(line),
                "length_meters": length,
            }
        )

    return results


# ============================================================
# Main inspection
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Street Supply Inspector"
    )

    print(
        "======================================="
    )

    print()


    # --------------------------------------------------------
    # Load Worcester winter-parking data
    # --------------------------------------------------------

    try:
        data = load_geojson(
            PARKING_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return


    features = data.get(
        "features",
        [],
    )


    print(
        f"Loaded Worcester segments: "
        f"{len(features)}"
    )

    print()


    if not features:
        print(
            "ERROR: No Worcester winter-parking "
            "segments were found."
        )

        return


    # --------------------------------------------------------
    # Locate Conway segment
    # --------------------------------------------------------

    feature = find_segment(
        features,
        TARGET_SEGMENT_ID,
    )


    if feature is None:
        print(
            "ERROR: Target Conway Street "
            f"segment {TARGET_SEGMENT_ID} "
            "was not found."
        )

        return


    properties = feature.get(
        "properties",
        {},
    )

    geometry = feature.get(
        "geometry",
        {},
    )


    # --------------------------------------------------------
    # Extract attributes
    # --------------------------------------------------------

    street_name = str(
        properties.get(
            "street_name"
        )
        or ""
    ).strip()


    segment_id = properties.get(
        "segment_id"
    )


    street_id = properties.get(
        "street_id"
    )


    ban_type = str(
        properties.get(
            "ban_type"
        )
        or ""
    ).strip().upper()


    ban_zone = str(
        properties.get(
            "ban_zone"
        )
        or ""
    ).strip().upper()


    restricted_side = str(
        properties.get(
            "no_parking_side"
        )
        or ""
    ).strip().upper()


    geometry_type = geometry.get(
        "type"
    )


    # --------------------------------------------------------
    # Calculate real centerline geometry length
    # --------------------------------------------------------

    segment_length = (
        calculate_geometry_length_meters(
            geometry
        )
    )


    geometry_lines = (
        normalize_geometry_lines(
            geometry
        )
    )


    line_count = len(
        geometry_lines
    )


    point_count = (
        count_geometry_points(
            geometry
        )
    )


    first_coordinate = (
        get_first_coordinate(
            geometry
        )
    )


    last_coordinate = (
        get_last_coordinate(
            geometry
        )
    )


    line_lengths = (
        calculate_line_lengths(
            geometry
        )
    )


    # ========================================================
    # Print real Worcester segment information
    # ========================================================

    print("REAL WORCESTER SEGMENT")
    print("======================")
    print()


    print(
        f"Street name:      "
        f"{street_name}"
    )


    print(
        f"Segment ID:       "
        f"{segment_id}"
    )


    print(
        f"Street ID:        "
        f"{street_id}"
    )


    print()


    print(
        f"Ban type:         "
        f"{ban_type}"
    )


    print(
        f"Ban zone:         "
        f"{ban_zone}"
    )


    print(
        f"Restricted side:  "
        f"{restricted_side}"
    )


    print()


    print(
        f"Geometry type:    "
        f"{geometry_type}"
    )


    print(
        f"Geometry lines:   "
        f"{line_count}"
    )


    print(
        f"Geometry points:  "
        f"{point_count}"
    )


    print()


    print(
        f"Centerline length:"
        f" {segment_length:.2f} m"
    )


    print()


    # ========================================================
    # Geometry components
    # ========================================================

    print("GEOMETRY LINE LENGTHS")
    print("=====================")
    print()


    for line_info in line_lengths:
        print(
            f"Line "
            f"{line_info['line_number']}: "
            f"{line_info['length_meters']:.2f} m "
            f"("
            f"{line_info['point_count']} points"
            f")"
        )


    print()


    # ========================================================
    # First and last coordinates
    # ========================================================

    print("GEOMETRY ENDPOINTS")
    print("==================")
    print()


    if first_coordinate is not None:
        print(
            "First coordinate:"
        )

        print(
            f"  Latitude:  "
            f"{first_coordinate['latitude']}"
        )

        print(
            f"  Longitude: "
            f"{first_coordinate['longitude']}"
        )

    else:
        print(
            "First coordinate: UNKNOWN"
        )


    print()


    if last_coordinate is not None:
        print(
            "Last coordinate:"
        )

        print(
            f"  Latitude:  "
            f"{last_coordinate['latitude']}"
        )

        print(
            f"  Longitude: "
            f"{last_coordinate['longitude']}"
        )

    else:
        print(
            "Last coordinate: UNKNOWN"
        )


    print()


    # ========================================================
    # Side interpretation
    #
    # This comes from the parity work already validated
    # earlier for the Conway segment.
    # ========================================================

    print("SIDE INTERPRETATION")
    print("===================")
    print()


    print(
        "ODD side:         LEFT"
    )


    print(
        "EVEN side:        RIGHT"
    )


    print(
        f"Restricted side:  "
        f"{restricted_side}"
    )


    print()


    # ========================================================
    # Supply status
    #
    # IMPORTANT:
    #
    # We intentionally do not manufacture usable curb
    # lengths from the centerline geometry.
    # ========================================================

    odd_usable_length = None

    even_usable_length = None

    odd_normal_capacity = None

    even_normal_capacity = None

    odd_ban_capacity = None

    even_ban_capacity = None


    print("CURRENT SUPPLY EVIDENCE")
    print("=======================")
    print()


    print(
        f"Segment centerline length: "
        f"{segment_length:.2f} m"
    )


    print(
        f"ODD usable curb length:    "
        f"{odd_usable_length}"
    )


    print(
        f"EVEN usable curb length:   "
        f"{even_usable_length}"
    )


    print()


    print(
        f"ODD normal capacity:       "
        f"{odd_normal_capacity}"
    )


    print(
        f"EVEN normal capacity:      "
        f"{even_normal_capacity}"
    )


    print()


    print(
        f"ODD ban capacity:          "
        f"{odd_ban_capacity}"
    )


    print(
        f"EVEN ban capacity:         "
        f"{even_ban_capacity}"
    )


    print()


    print(
        "Capacity evidence status:  UNKNOWN"
    )


    print()


    # ========================================================
    # Why supply remains unknown
    # ========================================================

    print("WHY CAPACITY REMAINS UNKNOWN")
    print("============================")
    print()


    print(
        "The centerline geometry gives BanReady the "
        "street-segment length, but it does not provide "
        "a complete legal curb inventory."
    )


    print()


    print(
        "Before calculating a real street-capacity "
        "estimate, BanReady needs defensible ODD and EVEN "
        "usable curb lengths that account for relevant "
        "parking exclusions."
    )


    print()


    print(
        "Examples include driveways, intersections, "
        "hydrants, curb cuts, loading areas, bus stops, "
        "signed restrictions, and other unusable curb."
    )


    print()


    print(
        "Therefore the real Conway usable curb lengths "
        "and capacities remain UNKNOWN at this step."
    )


    print()


    # ========================================================
    # Consistency checks
    # ========================================================

    print("CONSISTENCY CHECK")
    print("=================")
    print()


    checks = []


    checks.append(
        (
            "Target segment found",
            segment_id
            == TARGET_SEGMENT_ID,
        )
    )


    checks.append(
        (
            "Street is CONWAY ST",
            street_name
            == EXPECTED_STREET_NAME,
        )
    )


    checks.append(
        (
            "Geometry has positive length",
            segment_length > 0,
        )
    )


    checks.append(
        (
            "Geometry has at least one line",
            line_count >= 1,
        )
    )


    checks.append(
        (
            "Geometry has at least two points",
            point_count >= 2,
        )
    )


    checks.append(
        (
            "Ban type is present",
            ban_type != "",
        )
    )


    checks.append(
        (
            "Restricted side is present",
            restricted_side != "",
        )
    )


    checks.append(
        (
            "ODD usable curb remains unknown",
            odd_usable_length is None,
        )
    )


    checks.append(
        (
            "EVEN usable curb remains unknown",
            even_usable_length is None,
        )
    )


    checks.append(
        (
            "No street capacity invented",
            (
                odd_normal_capacity
                is None
                and even_normal_capacity
                is None
                and odd_ban_capacity
                is None
                and even_ban_capacity
                is None
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


    passed_checks = sum(
        1
        for _, passed
        in checks
        if passed
    )


    failed_checks = (
        len(checks)
        - passed_checks
    )


    # ========================================================
    # Summary
    # ========================================================

    print()

    print(
        "======================================="
    )


    print(
        "BANREADY CONWAY SUPPLY INSPECTION"
    )


    print(
        "======================================="
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
            "CONWAY SUPPLY INSPECTION PASSED"
        )

        print()

        print(
            "The real Worcester segment is ready "
            "for curb-level supply evidence work."
        )

    else:
        print(
            "CONWAY SUPPLY INSPECTION FAILED"
        )

        print()

        print(
            "Resolve the segment or geometry issues "
            "before estimating usable curb supply."
        )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()