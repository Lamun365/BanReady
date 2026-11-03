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

DRIVEWAYS_FILE = Path(
    "data/raw/worcester/driveways/"
    "Conway_Driveways.geojson"
)

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

TARGET_SEGMENT_ID = 821528

EXPECTED_STREET_NAME = "CONWAY ST"


EARTH_RADIUS_METERS = 6371000.0


# ============================================================
# Candidate screening distance
#
# This is NOT a legal curb-exclusion distance.
#
# It is only used to determine whether a driveway polygon
# lies close enough to the Conway centerline to deserve
# detailed curb-inventory inspection.
# ============================================================

MAX_CANDIDATE_DISTANCE_METERS = 20.0


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


def clean_value(value):
    if value is None:
        return "(EMPTY)"

    text = str(value).strip()

    if text == "":
        return "(EMPTY)"

    return text


def load_json(path):
    if not path.exists():
        raise RuntimeError(
            f"Required file not found: {path}"
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
            f"Could not parse JSON file: {path}"
        ) from error


# ============================================================
# Load Conway street feature
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

        if (
            properties.get("segment_id")
            == segment_id
        ):
            return feature

    return None


# ============================================================
# Street geometry normalization
# ============================================================

def normalize_street_lines(
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


# ============================================================
# Driveway coordinate extraction
# ============================================================

def collect_coordinate_pairs(
    coordinates,
):
    pairs = []

    if not isinstance(
        coordinates,
        (list, tuple),
    ):
        return pairs

    if (
        len(coordinates) >= 2
        and is_number(
            coordinates[0]
        )
        and is_number(
            coordinates[1]
        )
    ):
        pairs.append(
            (
                float(
                    coordinates[0]
                ),
                float(
                    coordinates[1]
                ),
            )
        )

        return pairs

    for item in coordinates:
        pairs.extend(
            collect_coordinate_pairs(
                item
            )
        )

    return pairs


def get_feature_coordinate_pairs(
    feature,
):
    geometry = feature.get(
        "geometry"
    )

    if not isinstance(
        geometry,
        dict,
    ):
        return []

    return collect_coordinate_pairs(
        geometry.get(
            "coordinates",
            [],
        )
    )


# ============================================================
# Local coordinate transformation
#
# For a small study area, longitude/latitude is converted
# into local meter coordinates relative to a reference point.
# ============================================================

def lonlat_to_local_xy(
    longitude,
    latitude,
    reference_longitude,
    reference_latitude,
):
    latitude_radians = math.radians(
        reference_latitude
    )

    x = (
        math.radians(
            longitude
            - reference_longitude
        )
        * EARTH_RADIUS_METERS
        * math.cos(
            latitude_radians
        )
    )

    y = (
        math.radians(
            latitude
            - reference_latitude
        )
        * EARTH_RADIUS_METERS
    )

    return (
        x,
        y,
    )


# ============================================================
# Point to line-segment relationship
# ============================================================

def nearest_point_on_segment(
    point_x,
    point_y,
    start_x,
    start_y,
    end_x,
    end_y,
):
    direction_x = (
        end_x
        - start_x
    )

    direction_y = (
        end_y
        - start_y
    )

    length_squared = (
        direction_x
        * direction_x
        + direction_y
        * direction_y
    )

    if length_squared == 0:
        nearest_x = start_x
        nearest_y = start_y

        distance = math.hypot(
            point_x - nearest_x,
            point_y - nearest_y,
        )

        return {
            "nearest_x": nearest_x,
            "nearest_y": nearest_y,
            "fraction": 0.0,
            "distance_meters": distance,
            "cross_product": 0.0,
        }

    fraction = (
        (
            (
                point_x
                - start_x
            )
            * direction_x
        )
        + (
            (
                point_y
                - start_y
            )
            * direction_y
        )
    ) / length_squared

    fraction = max(
        0.0,
        min(
            1.0,
            fraction,
        ),
    )

    nearest_x = (
        start_x
        + fraction
        * direction_x
    )

    nearest_y = (
        start_y
        + fraction
        * direction_y
    )

    difference_x = (
        point_x
        - nearest_x
    )

    difference_y = (
        point_y
        - nearest_y
    )

    distance = math.hypot(
        difference_x,
        difference_y,
    )

    # --------------------------------------------------------
    # Cross product sign
    #
    # Positive:
    # point is geometrically LEFT of the directed segment.
    #
    # Negative:
    # point is geometrically RIGHT of the directed segment.
    # --------------------------------------------------------

    cross_product = (
        direction_x
        * (
            point_y
            - start_y
        )
        - direction_y
        * (
            point_x
            - start_x
        )
    )

    return {
        "nearest_x": nearest_x,
        "nearest_y": nearest_y,
        "fraction": fraction,
        "distance_meters": distance,
        "cross_product": cross_product,
    }


# ============================================================
# Conway reference coordinate
# ============================================================

def get_reference_coordinate(
    street_lines,
):
    longitudes = []
    latitudes = []

    for line in street_lines:
        for point in line:
            if (
                not isinstance(
                    point,
                    (list, tuple),
                )
                or len(point) < 2
            ):
                continue

            longitude = point[0]
            latitude = point[1]

            if not (
                is_number(longitude)
                and is_number(latitude)
            ):
                continue

            longitudes.append(
                longitude
            )

            latitudes.append(
                latitude
            )

    if not longitudes:
        return None

    if not latitudes:
        return None

    return (
        sum(longitudes)
        / len(longitudes),
        sum(latitudes)
        / len(latitudes),
    )


# ============================================================
# Build Conway local geometry
# ============================================================

def build_local_street_segments(
    street_lines,
    reference_longitude,
    reference_latitude,
):
    segments = []

    cumulative_length = 0.0

    for line_number, line in enumerate(
        street_lines,
        start=1,
    ):
        if len(line) < 2:
            continue

        for point_index in range(
            len(line) - 1
        ):
            start = line[
                point_index
            ]

            end = line[
                point_index + 1
            ]

            if (
                len(start) < 2
                or len(end) < 2
            ):
                continue

            start_longitude = start[0]
            start_latitude = start[1]

            end_longitude = end[0]
            end_latitude = end[1]

            if not all(
                is_number(value)
                for value in (
                    start_longitude,
                    start_latitude,
                    end_longitude,
                    end_latitude,
                )
            ):
                continue

            (
                start_x,
                start_y,
            ) = lonlat_to_local_xy(
                start_longitude,
                start_latitude,
                reference_longitude,
                reference_latitude,
            )

            (
                end_x,
                end_y,
            ) = lonlat_to_local_xy(
                end_longitude,
                end_latitude,
                reference_longitude,
                reference_latitude,
            )

            segment_length = (
                math.hypot(
                    end_x - start_x,
                    end_y - start_y,
                )
            )

            if segment_length <= 0:
                continue

            segments.append(
                {
                    "line_number": (
                        line_number
                    ),

                    "point_index": (
                        point_index
                    ),

                    "start_x": (
                        start_x
                    ),

                    "start_y": (
                        start_y
                    ),

                    "end_x": (
                        end_x
                    ),

                    "end_y": (
                        end_y
                    ),

                    "length_meters": (
                        segment_length
                    ),

                    "start_distance_meters": (
                        cumulative_length
                    ),

                    "end_distance_meters": (
                        cumulative_length
                        + segment_length
                    ),
                }
            )

            cumulative_length += (
                segment_length
            )

    return (
        segments,
        cumulative_length,
    )


# ============================================================
# Analyze one driveway polygon
# ============================================================

def analyze_driveway(
    feature,
    street_segments,
    reference_longitude,
    reference_latitude,
):
    coordinate_pairs = (
        get_feature_coordinate_pairs(
            feature
        )
    )

    if not coordinate_pairs:
        return None

    best_result = None

    # --------------------------------------------------------
    # Test all driveway polygon vertices against all
    # Conway centerline subsegments.
    #
    # This is much more useful than testing only a polygon
    # centroid against the Conway midpoint.
    # --------------------------------------------------------

    for (
        driveway_longitude,
        driveway_latitude,
    ) in coordinate_pairs:

        (
            driveway_x,
            driveway_y,
        ) = lonlat_to_local_xy(
            driveway_longitude,
            driveway_latitude,
            reference_longitude,
            reference_latitude,
        )

        for street_segment in (
            street_segments
        ):
            relationship = (
                nearest_point_on_segment(
                    driveway_x,
                    driveway_y,

                    street_segment[
                        "start_x"
                    ],

                    street_segment[
                        "start_y"
                    ],

                    street_segment[
                        "end_x"
                    ],

                    street_segment[
                        "end_y"
                    ],
                )
            )

            distance = relationship[
                "distance_meters"
            ]

            if (
                best_result is None
                or distance
                < best_result[
                    "distance_meters"
                ]
            ):
                distance_along_segment = (
                    street_segment[
                        "start_distance_meters"
                    ]
                    + relationship[
                        "fraction"
                    ]
                    * street_segment[
                        "length_meters"
                    ]
                )

                cross_product = (
                    relationship[
                        "cross_product"
                    ]
                )

                if cross_product > 0:
                    geometric_side = (
                        "LEFT"
                    )

                    parity_side = (
                        "ODD"
                    )

                elif cross_product < 0:
                    geometric_side = (
                        "RIGHT"
                    )

                    parity_side = (
                        "EVEN"
                    )

                else:
                    geometric_side = (
                        "ON_LINE"
                    )

                    parity_side = (
                        "UNKNOWN"
                    )

                best_result = {
                    "distance_meters": (
                        distance
                    ),

                    "distance_along_segment_meters": (
                        distance_along_segment
                    ),

                    "geometric_side": (
                        geometric_side
                    ),

                    "parity_side": (
                        parity_side
                    ),

                    "driveway_longitude": (
                        driveway_longitude
                    ),

                    "driveway_latitude": (
                        driveway_latitude
                    ),

                    "line_number": (
                        street_segment[
                            "line_number"
                        ]
                    ),

                    "street_piece_index": (
                        street_segment[
                            "point_index"
                        ]
                    ),
                }

    return best_result


# ============================================================
# Main inspection
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Driveway Spatial Inspector"
    )

    print(
        "========================================="
    )

    print()

    # --------------------------------------------------------
    # Load bounded driveway data
    # --------------------------------------------------------

    try:
        driveway_data = load_json(
            DRIVEWAYS_FILE
        )

        parking_data = load_json(
            PARKING_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    driveway_features = (
        driveway_data.get(
            "features",
            [],
        )
    )

    parking_features = (
        parking_data.get(
            "features",
            [],
        )
    )

    print(
        f"Driveway file: "
        f"{DRIVEWAYS_FILE}"
    )

    print(
        f"Driveway GeoJSON type: "
        f"{driveway_data.get('type')}"
    )

    print(
        f"Driveway features: "
        f"{len(driveway_features)}"
    )

    print()

    if (
        driveway_data.get("type")
        != "FeatureCollection"
    ):
        print(
            "ERROR: Conway driveway file "
            "is not a FeatureCollection."
        )

        return

    # --------------------------------------------------------
    # Find Conway segment
    # --------------------------------------------------------

    conway_feature = (
        find_segment(
            parking_features,
            TARGET_SEGMENT_ID,
        )
    )

    if conway_feature is None:
        print(
            "ERROR: Conway segment "
            f"{TARGET_SEGMENT_ID} "
            "was not found."
        )

        return

    conway_properties = (
        conway_feature.get(
            "properties",
            {},
        )
    )

    conway_geometry = (
        conway_feature.get(
            "geometry",
            {},
        )
    )

    street_name = str(
        conway_properties.get(
            "street_name"
        )
        or ""
    ).strip()

    restricted_side = str(
        conway_properties.get(
            "no_parking_side"
        )
        or ""
    ).strip().upper()

    street_lines = (
        normalize_street_lines(
            conway_geometry
        )
    )

    if not street_lines:
        print(
            "ERROR: Conway street geometry "
            "could not be normalized."
        )

        return

    reference_coordinate = (
        get_reference_coordinate(
            street_lines
        )
    )

    if reference_coordinate is None:
        print(
            "ERROR: Could not create "
            "Conway reference coordinate."
        )

        return

    (
        reference_longitude,
        reference_latitude,
    ) = reference_coordinate

    (
        street_segments,
        street_length,
    ) = build_local_street_segments(
        street_lines,
        reference_longitude,
        reference_latitude,
    )

    if not street_segments:
        print(
            "ERROR: Conway has no usable "
            "street geometry segments."
        )

        return

    # ========================================================
    # Conway information
    # ========================================================

    print("CONWAY SEGMENT")
    print("==============")
    print()

    print(
        f"Street:           "
        f"{street_name}"
    )

    print(
        f"Segment ID:       "
        f"{TARGET_SEGMENT_ID}"
    )

    print(
        f"Restricted side:  "
        f"{restricted_side}"
    )

    print()

    print(
        f"Centerline pieces:"
        f" {len(street_segments)}"
    )

    print(
        f"Centerline length:"
        f" {street_length:.2f} m"
    )

    print()

    print(
        f"Reference latitude:  "
        f"{reference_latitude}"
    )

    print(
        f"Reference longitude: "
        f"{reference_longitude}"
    )

    print()

    # ========================================================
    # Driveway fields
    # ========================================================

    property_fields = set()

    geometry_types = set()

    for feature in driveway_features:
        properties = feature.get(
            "properties",
            {},
        )

        if isinstance(
            properties,
            dict,
        ):
            property_fields.update(
                properties.keys()
            )

        geometry = feature.get(
            "geometry",
            {},
        )

        if isinstance(
            geometry,
            dict,
        ):
            geometry_type = (
                geometry.get(
                    "type"
                )
            )

            if geometry_type:
                geometry_types.add(
                    geometry_type
                )

    print("DRIVEWAY DATASET")
    print("================")
    print()

    print(
        f"Feature count: "
        f"{len(driveway_features)}"
    )

    print(
        "Geometry types: "
        + (
            ", ".join(
                sorted(
                    geometry_types
                )
            )
            if geometry_types
            else "(NONE)"
        )
    )

    print()

    print(
        "Property fields:"
    )

    for field in sorted(
        property_fields
    ):
        print(
            f"  {field}"
        )

    print()

    # ========================================================
    # Analyze all bounded driveway polygons
    # ========================================================

    analyses = []

    skipped_features = 0

    for feature_number, feature in enumerate(
        driveway_features,
        start=1,
    ):
        result = analyze_driveway(
            feature=feature,
            street_segments=(
                street_segments
            ),
            reference_longitude=(
                reference_longitude
            ),
            reference_latitude=(
                reference_latitude
            ),
        )

        if result is None:
            skipped_features += 1
            continue

        properties = feature.get(
            "properties",
            {},
        )

        analyses.append(
            {
                "feature_number": (
                    feature_number
                ),

                "properties": (
                    properties
                ),

                "analysis": (
                    result
                ),
            }
        )

    analyses.sort(
        key=lambda item: (
            item["analysis"][
                "distance_meters"
            ],
            item["analysis"][
                "distance_along_segment_meters"
            ],
        )
    )

    # ========================================================
    # Candidate filter
    # ========================================================

    candidates = [
        item
        for item in analyses
        if (
            item["analysis"][
                "distance_meters"
            ]
            <= MAX_CANDIDATE_DISTANCE_METERS
        )
    ]

    odd_candidates = [
        item
        for item in candidates
        if (
            item["analysis"][
                "parity_side"
            ]
            == "ODD"
        )
    ]

    even_candidates = [
        item
        for item in candidates
        if (
            item["analysis"][
                "parity_side"
            ]
            == "EVEN"
        )
    ]

    unknown_candidates = [
        item
        for item in candidates
        if (
            item["analysis"][
                "parity_side"
            ]
            == "UNKNOWN"
        )
    ]

    # ========================================================
    # Screening summary
    # ========================================================

    print("SPATIAL SCREENING")
    print("=================")
    print()

    print(
        f"Analyzed driveway polygons: "
        f"{len(analyses)}"
    )

    print(
        f"Skipped driveway polygons:  "
        f"{skipped_features}"
    )

    print()

    print(
        f"Candidate distance:          "
        f"{MAX_CANDIDATE_DISTANCE_METERS:.1f} m"
    )

    print(
        f"Potential Conway driveways:  "
        f"{len(candidates)}"
    )

    print()

    print(
        f"ODD / LEFT candidates:       "
        f"{len(odd_candidates)}"
    )

    print(
        f"EVEN / RIGHT candidates:     "
        f"{len(even_candidates)}"
    )

    print(
        f"Unclassified candidates:     "
        f"{len(unknown_candidates)}"
    )

    print()

    # ========================================================
    # Print candidates
    # ========================================================

    print("CANDIDATE DRIVEWAYS")
    print("===================")
    print()

    if not candidates:
        print(
            "No driveway polygons were found "
            "within the candidate distance of "
            "the Conway centerline."
        )

        print()

    for candidate_number, item in enumerate(
        candidates,
        start=1,
    ):
        analysis = item[
            "analysis"
        ]

        properties = item[
            "properties"
        ]

        print(
            f"Candidate "
            f"{candidate_number}"
        )

        print(
            "-" * 50
        )

        print(
            f"Feature number:       "
            f"{item['feature_number']}"
        )

        print(
            f"OBJECTID:             "
            f"{clean_value(properties.get('OBJECTID'))}"
        )

        print(
            f"DRIVEWAY_ID:          "
            f"{clean_value(properties.get('DRIVEWAY_ID'))}"
        )

        print(
            f"DRIVEWAY_:            "
            f"{clean_value(properties.get('DRIVEWAY_'))}"
        )

        print(
            f"TYPE:                  "
            f"{clean_value(properties.get('TYPE'))}"
        )

        print(
            f"GlobalID:              "
            f"{clean_value(properties.get('GlobalID'))}"
        )

        print()

        print(
            f"Distance to centerline:"
            f" {analysis['distance_meters']:.2f} m"
        )

        print(
            f"Position along Conway: "
            f"{analysis['distance_along_segment_meters']:.2f} m"
        )

        print(
            f"Geometric side:        "
            f"{analysis['geometric_side']}"
        )

        print(
            f"Parity side:           "
            f"{analysis['parity_side']}"
        )

        print()

        print(
            f"Nearest polygon point:"
        )

        print(
            f"  Latitude:  "
            f"{analysis['driveway_latitude']}"
        )

        print(
            f"  Longitude: "
            f"{analysis['driveway_longitude']}"
        )

        print()

    # ========================================================
    # Ordered side-specific list
    # ========================================================

    print("ODD / LEFT DRIVEWAY CANDIDATES")
    print("==============================")
    print()

    if odd_candidates:
        for index, item in enumerate(
            sorted(
                odd_candidates,
                key=lambda candidate: (
                    candidate[
                        "analysis"
                    ][
                        "distance_along_segment_meters"
                    ]
                ),
            ),
            start=1,
        ):
            analysis = item[
                "analysis"
            ]

            properties = item[
                "properties"
            ]

            print(
                f"{index}. "
                f"DRIVEWAY_ID="
                f"{clean_value(properties.get('DRIVEWAY_ID'))}, "
                f"position="
                f"{analysis['distance_along_segment_meters']:.2f} m, "
                f"offset="
                f"{analysis['distance_meters']:.2f} m"
            )

    else:
        print(
            "None"
        )

    print()

    print("EVEN / RIGHT DRIVEWAY CANDIDATES")
    print("================================")
    print()

    if even_candidates:
        for index, item in enumerate(
            sorted(
                even_candidates,
                key=lambda candidate: (
                    candidate[
                        "analysis"
                    ][
                        "distance_along_segment_meters"
                    ]
                ),
            ),
            start=1,
        ):
            analysis = item[
                "analysis"
            ]

            properties = item[
                "properties"
            ]

            print(
                f"{index}. "
                f"DRIVEWAY_ID="
                f"{clean_value(properties.get('DRIVEWAY_ID'))}, "
                f"position="
                f"{analysis['distance_along_segment_meters']:.2f} m, "
                f"offset="
                f"{analysis['distance_meters']:.2f} m"
            )

    else:
        print(
            "None"
        )

    print()

    # ========================================================
    # Critical methodology note
    # ========================================================

    print("METHODOLOGY STATUS")
    print("==================")
    print()

    print(
        "This script classifies driveway polygons "
        "as spatial candidates only."
    )

    print()

    print(
        "A candidate is NOT yet a measured curb "
        "exclusion."
    )

    print()

    print(
        "BanReady still needs to determine the "
        "actual driveway opening width along the "
        "curb before assigning "
        "length_meters in the Conway curb inventory."
    )

    print()

    print(
        "Therefore conway_821528_curb_inventory.json "
        "must remain INCOMPLETE after this script."
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
            "Bounded driveway GeoJSON is FeatureCollection",
            (
                driveway_data.get(
                    "type"
                )
                == "FeatureCollection"
            ),
        )
    )

    checks.append(
        (
            "Conway segment found",
            (
                conway_properties.get(
                    "segment_id"
                )
                == TARGET_SEGMENT_ID
            ),
        )
    )

    checks.append(
        (
            "Street is CONWAY ST",
            (
                street_name
                == EXPECTED_STREET_NAME
            ),
        )
    )

    checks.append(
        (
            "Conway geometry has street pieces",
            (
                len(
                    street_segments
                )
                > 0
            ),
        )
    )

    checks.append(
        (
            "Conway length is approximately 253.31 m",
            (
                abs(
                    street_length
                    - 253.31
                )
                <= 0.50
            ),
        )
    )

    checks.append(
        (
            "All bounded driveway features analyzed",
            (
                len(analyses)
                + skipped_features
                == len(
                    driveway_features
                )
            ),
        )
    )

    checks.append(
        (
            "Candidate side counts reconcile",
            (
                len(odd_candidates)
                + len(even_candidates)
                + len(
                    unknown_candidates
                )
                == len(candidates)
            ),
        )
    )

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

    passed_count = sum(
        1
        for _, passed
        in checks
        if passed
    )

    failed_count = (
        len(checks)
        - passed_count
    )

    print()

    print(
        "========================================="
    )

    print(
        "BANREADY CONWAY DRIVEWAY ANALYSIS SUMMARY"
    )

    print(
        "========================================="
    )

    print()

    print(
        f"Total checks: "
        f"{len(checks)}"
    )

    print(
        f"Passed:       "
        f"{passed_count}"
    )

    print(
        f"Failed:       "
        f"{failed_count}"
    )

    print()

    if failed_count == 0:
        print(
            "CONWAY DRIVEWAY SPATIAL ANALYSIS PASSED"
        )

        print()

        print(
            "Driveway candidates are ready for "
            "curb-opening measurement and evidence "
            "review."
        )

    else:
        print(
            "CONWAY DRIVEWAY SPATIAL ANALYSIS FAILED"
        )

        print()

        print(
            "Do not populate driveway curb "
            "exclusions until the spatial-analysis "
            "issues are resolved."
        )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
