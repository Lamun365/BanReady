import json
import math
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
# Configuration
# ============================================================

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_intersection_inspection.json"
)


TARGET_SEGMENT_ID = 821528

EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_STREET_ID = 753050

EXPECTED_SEGMENT_LENGTH_METERS = 253.31


EARTH_RADIUS_METERS = 6371000.0


# ============================================================
# Endpoint search configuration
#
# CONNECTION_TOLERANCE_METERS is used to identify street
# endpoints that appear geometrically connected.
#
# NEARBY_TOLERANCE_METERS is a broader inspection distance
# used to show other nearby street endpoints.
#
# Neither value is a legal parking-clearance distance.
# ============================================================

CONNECTION_TOLERANCE_METERS = 3.0

NEARBY_TOLERANCE_METERS = 20.0


# ============================================================
# Helpers
# ============================================================

def is_number(value):
    if isinstance(value, bool):
        return False

    if not isinstance(
        value,
        (int, float),
    ):
        return False

    return math.isfinite(
        float(value)
    )


def clean_text(value):
    if value is None:
        return ""

    return str(value).strip()


def load_geojson(path):
    if not path.exists():
        raise RuntimeError(
            f"Required GeoJSON file not found: {path}"
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
            f"Could not parse GeoJSON file: {path}"
        ) from error


# ============================================================
# Distance calculation
# ============================================================

def distance_meters(
    longitude_1,
    latitude_1,
    longitude_2,
    latitude_2,
):
    values = (
        longitude_1,
        latitude_1,
        longitude_2,
        latitude_2,
    )

    if not all(
        is_number(value)
        for value in values
    ):
        return None

    latitude_1_radians = math.radians(
        latitude_1
    )

    latitude_2_radians = math.radians(
        latitude_2
    )

    delta_latitude = math.radians(
        latitude_2
        - latitude_1
    )

    delta_longitude = math.radians(
        longitude_2
        - longitude_1
    )

    a = (
        math.sin(
            delta_latitude / 2.0
        ) ** 2
        + math.cos(
            latitude_1_radians
        )
        * math.cos(
            latitude_2_radians
        )
        * math.sin(
            delta_longitude / 2.0
        ) ** 2
    )

    c = 2.0 * math.atan2(
        math.sqrt(a),
        math.sqrt(1.0 - a),
    )

    return (
        EARTH_RADIUS_METERS
        * c
    )


# ============================================================
# Geometry normalization
# ============================================================

def normalize_geometry_lines(
    geometry,
):
    if not isinstance(
        geometry,
        dict,
    ):
        return []

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    if geometry_type == "LineString":
        return [
            coordinates
        ]

    if geometry_type == "MultiLineString":
        return coordinates

    return []


def valid_coordinate(
    coordinate,
):
    return (
        isinstance(
            coordinate,
            (list, tuple),
        )
        and len(coordinate) >= 2
        and is_number(
            coordinate[0]
        )
        and is_number(
            coordinate[1]
        )
        and -180
        <= coordinate[0]
        <= 180
        and -90
        <= coordinate[1]
        <= 90
    )


# ============================================================
# Segment endpoints
# ============================================================

def get_geometry_endpoints(
    geometry,
):
    """
    Return every start and end coordinate represented by
    a LineString or MultiLineString.

    A normal LineString produces two endpoint records.
    """

    lines = normalize_geometry_lines(
        geometry
    )

    endpoints = []

    for line_number, line in enumerate(
        lines,
        start=1,
    ):
        if (
            not isinstance(
                line,
                list,
            )
            or len(line) < 2
        ):
            continue

        start = line[0]

        end = line[-1]

        if valid_coordinate(
            start
        ):
            endpoints.append(
                {
                    "endpoint_type": "START",
                    "line_number": line_number,
                    "longitude": float(
                        start[0]
                    ),
                    "latitude": float(
                        start[1]
                    ),
                }
            )

        if valid_coordinate(
            end
        ):
            endpoints.append(
                {
                    "endpoint_type": "END",
                    "line_number": line_number,
                    "longitude": float(
                        end[0]
                    ),
                    "latitude": float(
                        end[1]
                    ),
                }
            )

    return endpoints


def get_primary_start_and_end(
    geometry,
):
    lines = normalize_geometry_lines(
        geometry
    )

    if not lines:
        return (
            None,
            None,
        )

    first_line = None

    last_line = None

    for line in lines:
        if (
            isinstance(line, list)
            and len(line) >= 2
        ):
            if first_line is None:
                first_line = line

            last_line = line

    if (
        first_line is None
        or last_line is None
    ):
        return (
            None,
            None,
        )

    start = first_line[0]

    end = last_line[-1]

    if not valid_coordinate(
        start
    ):
        start = None

    if not valid_coordinate(
        end
    ):
        end = None

    return (
        start,
        end,
    )


# ============================================================
# Geometry length
# ============================================================

def calculate_geometry_length_meters(
    geometry,
):
    lines = normalize_geometry_lines(
        geometry
    )

    total_length = 0.0

    for line in lines:
        if (
            not isinstance(line, list)
            or len(line) < 2
        ):
            continue

        for index in range(
            len(line) - 1
        ):
            start = line[index]

            end = line[
                index + 1
            ]

            if not (
                valid_coordinate(start)
                and valid_coordinate(end)
            ):
                continue

            length = distance_meters(
                start[0],
                start[1],
                end[0],
                end[1],
            )

            if length is not None:
                total_length += length

    return round(
        total_length,
        2,
    )


# ============================================================
# Feature identity
# ============================================================

def get_feature_identity(
    feature,
):
    properties = feature.get(
        "properties",
        {},
    )

    return {
        "street_name": clean_text(
            properties.get(
                "street_name"
            )
        ),

        "segment_id": properties.get(
            "segment_id"
        ),

        "street_id": properties.get(
            "street_id"
        ),

        "ban_type": clean_text(
            properties.get(
                "ban_type"
            )
        ).upper(),

        "ban_zone": clean_text(
            properties.get(
                "ban_zone"
            )
        ).upper(),

        "restricted_side": clean_text(
            properties.get(
                "no_parking_side"
            )
        ).upper(),

        "geometry_type": (
            feature.get(
                "geometry",
                {},
            ).get(
                "type"
            )
        ),
    }


def find_feature_by_segment_id(
    features,
    segment_id,
):
    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        if (
            properties.get(
                "segment_id"
            )
            == segment_id
        ):
            return feature

    return None


# ============================================================
# Endpoint candidate search
# ============================================================

def inspect_endpoint(
    target_endpoint,
    target_segment_id,
    features,
):
    """
    Find other street-feature endpoints near a target
    Conway endpoint.

    Results are categorized as:

    CONNECTED_CANDIDATE
        Endpoint is within the strict connection tolerance.

    NEARBY_ENDPOINT
        Endpoint is outside the connection tolerance but
        within the broader inspection radius.
    """

    target_longitude = (
        target_endpoint[
            "longitude"
        ]
    )

    target_latitude = (
        target_endpoint[
            "latitude"
        ]
    )

    candidates = []

    for feature in features:
        identity = get_feature_identity(
            feature
        )

        segment_id = identity[
            "segment_id"
        ]

        if (
            segment_id
            == target_segment_id
        ):
            continue

        endpoints = get_geometry_endpoints(
            feature.get(
                "geometry",
                {},
            )
        )

        for endpoint in endpoints:
            distance = distance_meters(
                target_longitude,
                target_latitude,
                endpoint[
                    "longitude"
                ],
                endpoint[
                    "latitude"
                ],
            )

            if distance is None:
                continue

            if (
                distance
                > NEARBY_TOLERANCE_METERS
            ):
                continue

            if (
                distance
                <= CONNECTION_TOLERANCE_METERS
            ):
                relationship = (
                    "CONNECTED_CANDIDATE"
                )

            else:
                relationship = (
                    "NEARBY_ENDPOINT"
                )

            candidates.append(
                {
                    **identity,

                    "candidate_endpoint_type": (
                        endpoint[
                            "endpoint_type"
                        ]
                    ),

                    "candidate_line_number": (
                        endpoint[
                            "line_number"
                        ]
                    ),

                    "candidate_longitude": (
                        endpoint[
                            "longitude"
                        ]
                    ),

                    "candidate_latitude": (
                        endpoint[
                            "latitude"
                        ]
                    ),

                    "distance_meters": round(
                        distance,
                        2,
                    ),

                    "relationship": (
                        relationship
                    ),
                }
            )

    # --------------------------------------------------------
    # The same segment can occasionally have multiple
    # endpoints nearby. Keep the nearest endpoint per segment.
    # --------------------------------------------------------

    nearest_by_segment = {}

    for candidate in candidates:
        segment_id = candidate[
            "segment_id"
        ]

        existing = nearest_by_segment.get(
            segment_id
        )

        if (
            existing is None
            or candidate[
                "distance_meters"
            ]
            < existing[
                "distance_meters"
            ]
        ):
            nearest_by_segment[
                segment_id
            ] = candidate

    results = list(
        nearest_by_segment.values()
    )

    results.sort(
        key=lambda item: (
            item[
                "distance_meters"
            ],
            item[
                "street_name"
            ],
            str(
                item[
                    "segment_id"
                ]
            ),
        )
    )

    return results


# ============================================================
# Print endpoint report
# ============================================================

def print_endpoint_report(
    endpoint_name,
    endpoint,
    candidates,
):
    connected = [
        candidate
        for candidate in candidates
        if (
            candidate[
                "relationship"
            ]
            == "CONNECTED_CANDIDATE"
        )
    ]

    nearby = [
        candidate
        for candidate in candidates
        if (
            candidate[
                "relationship"
            ]
            == "NEARBY_ENDPOINT"
        )
    ]

    print(
        f"{endpoint_name} ENDPOINT"
    )

    print(
        "=" * (
            len(endpoint_name)
            + 9
        )
    )

    print()

    print(
        f"Latitude:   "
        f"{endpoint['latitude']}"
    )

    print(
        f"Longitude:  "
        f"{endpoint['longitude']}"
    )

    print()

    print(
        f"Connected candidates: "
        f"{len(connected)}"
    )

    print(
        f"Nearby endpoints:     "
        f"{len(nearby)}"
    )

    print()

    print(
        "CONNECTED STREET CANDIDATES"
    )

    print(
        "---------------------------"
    )

    print()

    if not connected:
        print(
            "None"
        )

    for index, candidate in enumerate(
        connected,
        start=1,
    ):
        print(
            f"{index}. "
            f"{candidate['street_name']}"
        )

        print(
            f"   Segment ID:      "
            f"{candidate['segment_id']}"
        )

        print(
            f"   Street ID:       "
            f"{candidate['street_id']}"
        )

        print(
            f"   Distance:        "
            f"{candidate['distance_meters']:.2f} m"
        )

        print(
            f"   Endpoint type:   "
            f"{candidate['candidate_endpoint_type']}"
        )

        print(
            f"   Geometry type:   "
            f"{candidate['geometry_type']}"
        )

        print(
            f"   Ban type:        "
            f"{candidate['ban_type']}"
        )

        print(
            f"   Restricted side: "
            f"{candidate['restricted_side']}"
        )

        print()

    print(
        "OTHER NEARBY ENDPOINTS"
    )

    print(
        "----------------------"
    )

    print()

    if not nearby:
        print(
            "None"
        )

    for index, candidate in enumerate(
        nearby,
        start=1,
    ):
        print(
            f"{index}. "
            f"{candidate['street_name']}"
        )

        print(
            f"   Segment ID: "
            f"{candidate['segment_id']}"
        )

        print(
            f"   Distance:   "
            f"{candidate['distance_meters']:.2f} m"
        )

        print()

    print()


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Intersection Inspector"
    )

    print(
        "======================================"
    )

    print()

    # --------------------------------------------------------
    # Load Worcester street data
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

    if not features:
        print(
            "ERROR: Worcester winter-parking "
            "dataset contains no features."
        )

        return

    print(
        f"Loaded Worcester segments: "
        f"{len(features)}"
    )

    print()

    # --------------------------------------------------------
    # Locate Conway segment
    # --------------------------------------------------------

    conway_feature = (
        find_feature_by_segment_id(
            features,
            TARGET_SEGMENT_ID,
        )
    )

    if conway_feature is None:
        print(
            f"ERROR: Conway segment "
            f"{TARGET_SEGMENT_ID} "
            "was not found."
        )

        return

    identity = get_feature_identity(
        conway_feature
    )

    geometry = conway_feature.get(
        "geometry",
        {},
    )

    segment_length = (
        calculate_geometry_length_meters(
            geometry
        )
    )

    (
        start_coordinate,
        end_coordinate,
    ) = get_primary_start_and_end(
        geometry
    )

    if (
        start_coordinate is None
        or end_coordinate is None
    ):
        print(
            "ERROR: Conway segment endpoints "
            "could not be extracted."
        )

        return

    start_endpoint = {
        "longitude": float(
            start_coordinate[0]
        ),
        "latitude": float(
            start_coordinate[1]
        ),
    }

    end_endpoint = {
        "longitude": float(
            end_coordinate[0]
        ),
        "latitude": float(
            end_coordinate[1]
        ),
    }

    # --------------------------------------------------------
    # Inspect both endpoints
    # --------------------------------------------------------

    start_candidates = (
        inspect_endpoint(
            target_endpoint=(
                start_endpoint
            ),
            target_segment_id=(
                TARGET_SEGMENT_ID
            ),
            features=features,
        )
    )

    end_candidates = (
        inspect_endpoint(
            target_endpoint=(
                end_endpoint
            ),
            target_segment_id=(
                TARGET_SEGMENT_ID
            ),
            features=features,
        )
    )

    start_connected = [
        candidate
        for candidate in start_candidates
        if (
            candidate[
                "relationship"
            ]
            == "CONNECTED_CANDIDATE"
        )
    ]

    end_connected = [
        candidate
        for candidate in end_candidates
        if (
            candidate[
                "relationship"
            ]
            == "CONNECTED_CANDIDATE"
        )
    ]

    # ========================================================
    # Display Conway
    # ========================================================

    print("CONWAY SEGMENT")
    print("==============")
    print()

    print(
        f"Street:           "
        f"{identity['street_name']}"
    )

    print(
        f"Segment ID:       "
        f"{identity['segment_id']}"
    )

    print(
        f"Street ID:        "
        f"{identity['street_id']}"
    )

    print(
        f"Geometry type:    "
        f"{identity['geometry_type']}"
    )

    print(
        f"Centerline length:"
        f" {segment_length:.2f} m"
    )

    print()

    print(
        f"Connection tolerance: "
        f"{CONNECTION_TOLERANCE_METERS:.2f} m"
    )

    print(
        f"Nearby tolerance:     "
        f"{NEARBY_TOLERANCE_METERS:.2f} m"
    )

    print()

    # ========================================================
    # Endpoint reports
    # ========================================================

    print_endpoint_report(
        endpoint_name="START",
        endpoint=start_endpoint,
        candidates=start_candidates,
    )

    print_endpoint_report(
        endpoint_name="END",
        endpoint=end_endpoint,
        candidates=end_candidates,
    )

    # ========================================================
    # Output dataset
    # ========================================================

    output = {
        "dataset_name": (
            "BanReady Conway Intersection Inspection"
        ),

        "street_name": (
            identity[
                "street_name"
            ]
        ),

        "segment_id": (
            identity[
                "segment_id"
            ]
        ),

        "street_id": (
            identity[
                "street_id"
            ]
        ),

        "segment_length_meters": (
            segment_length
        ),

        "inspection_status": (
            "ENDPOINT_GEOMETRY_ONLY"
        ),

        "inventory_status": (
            "INCOMPLETE"
        ),

        "connection_tolerance_meters": (
            CONNECTION_TOLERANCE_METERS
        ),

        "nearby_tolerance_meters": (
            NEARBY_TOLERANCE_METERS
        ),

        "start_endpoint": {
            **start_endpoint,

            "connected_candidate_count": (
                len(
                    start_connected
                )
            ),

            "candidates": (
                start_candidates
            ),
        },

        "end_endpoint": {
            **end_endpoint,

            "connected_candidate_count": (
                len(
                    end_connected
                )
            ),

            "candidates": (
                end_candidates
            ),
        },

        "methodology": (
            "The start and end coordinates of Conway "
            "segment 821528 are compared with endpoints "
            "from other Worcester winter-parking street "
            "features. Segments within the strict "
            "connection tolerance are classified as "
            "connected candidates. This geometric "
            "inspection does not establish a legal "
            "parking-clearance distance."
        ),

        "limitations": [
            (
                "Endpoint proximity does not by itself "
                "prove a legal intersection."
            ),
            (
                "The winter-parking segment dataset may "
                "split streets for rule or data-management "
                "reasons rather than physical intersections."
            ),
            (
                "No intersection curb-exclusion length "
                "is assigned by this script."
            ),
            (
                "The Conway curb inventory must remain "
                "INCOMPLETE."
            ),
        ],
    }

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
    # Consistency checks
    # ========================================================

    checks = []

    checks.append(
        (
            "Target segment found",
            identity[
                "segment_id"
            ]
            == TARGET_SEGMENT_ID,
        )
    )

    checks.append(
        (
            "Street is CONWAY ST",
            identity[
                "street_name"
            ]
            == EXPECTED_STREET_NAME,
        )
    )

    checks.append(
        (
            "Street ID is 753050",
            identity[
                "street_id"
            ]
            == EXPECTED_STREET_ID,
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
            "Length approximately 253.31 m",
            abs(
                segment_length
                - EXPECTED_SEGMENT_LENGTH_METERS
            )
            <= 0.50,
        )
    )

    checks.append(
        (
            "Start endpoint valid",
            (
                -180
                <= start_endpoint[
                    "longitude"
                ]
                <= 180
                and -90
                <= start_endpoint[
                    "latitude"
                ]
                <= 90
            ),
        )
    )

    checks.append(
        (
            "End endpoint valid",
            (
                -180
                <= end_endpoint[
                    "longitude"
                ]
                <= 180
                and -90
                <= end_endpoint[
                    "latitude"
                ]
                <= 90
            ),
        )
    )

    checks.append(
        (
            "Start candidate distances valid",
            all(
                candidate[
                    "distance_meters"
                ]
                >= 0
                for candidate
                in start_candidates
            ),
        )
    )

    checks.append(
        (
            "End candidate distances valid",
            all(
                candidate[
                    "distance_meters"
                ]
                >= 0
                for candidate
                in end_candidates
            ),
        )
    )

    checks.append(
        (
            "No intersection exclusion invented",
            (
                output[
                    "inspection_status"
                ]
                == "ENDPOINT_GEOMETRY_ONLY"
                and output[
                    "inventory_status"
                ]
                == "INCOMPLETE"
            ),
        )
    )

    print("CONSISTENCY CHECK")
    print("=================")
    print()

    for index, (
        check_name,
        passed,
    ) in enumerate(
        checks,
        start=1,
    ):
        print(
            f"Test {index:02d} - "
            f"{check_name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    passed_checks = sum(
        1
        for _, passed in checks
        if passed
    )

    failed_checks = (
        len(checks)
        - passed_checks
    )

    print()
    print(
        "======================================="
    )

    print(
        "BANREADY INTERSECTION INSPECTION SUMMARY"
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
            "CONWAY INTERSECTION INSPECTION PASSED"
        )
    else:
        print(
            "CONWAY INTERSECTION INSPECTION FAILED"
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
        "This script identifies geometric endpoint "
        "connections only."
    )

    print()

    print(
        "It does not assign intersection-clearance "
        "lengths or complete the Conway curb inventory."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()