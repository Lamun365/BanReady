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

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_driveway_measurements.json"
)


TARGET_SEGMENT_ID = 821528

EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_RESTRICTED_SIDE = "EVEN"

EARTH_RADIUS_METERS = 6371000.0


# ============================================================
# Measurement configuration
#
# These are spatial-analysis controls.
# They are not Worcester parking-law distances.
# ============================================================

MAX_CANDIDATE_DISTANCE_METERS = 20.0

MIN_REASONABLE_WIDTH_METERS = 1.5

MAX_REASONABLE_WIDTH_METERS = 20.0


# ============================================================
# Basic helpers
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
        return None

    text = str(value).strip()

    if text == "":
        return None

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
# Street lookup
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
# Polygon coordinate extraction
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
# Local meter coordinate system
# ============================================================

def lonlat_to_local_xy(
    longitude,
    latitude,
    reference_longitude,
    reference_latitude,
):
    reference_latitude_radians = (
        math.radians(
            reference_latitude
        )
    )

    x = (
        math.radians(
            longitude
            - reference_longitude
        )
        * EARTH_RADIUS_METERS
        * math.cos(
            reference_latitude_radians
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
# Reference coordinate
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
                float(longitude)
            )

            latitudes.append(
                float(latitude)
            )

    if not longitudes:
        return None

    return (
        sum(longitudes)
        / len(longitudes),

        sum(latitudes)
        / len(latitudes),
    )


# ============================================================
# Build local Conway geometry
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
                not isinstance(
                    start,
                    (list, tuple),
                )
                or not isinstance(
                    end,
                    (list, tuple),
                )
                or len(start) < 2
                or len(end) < 2
            ):
                continue

            if not all(
                is_number(value)
                for value in (
                    start[0],
                    start[1],
                    end[0],
                    end[1],
                )
            ):
                continue

            (
                start_x,
                start_y,
            ) = lonlat_to_local_xy(
                start[0],
                start[1],
                reference_longitude,
                reference_latitude,
            )

            (
                end_x,
                end_y,
            ) = lonlat_to_local_xy(
                end[0],
                end[1],
                reference_longitude,
                reference_latitude,
            )

            direction_x = (
                end_x
                - start_x
            )

            direction_y = (
                end_y
                - start_y
            )

            length = math.hypot(
                direction_x,
                direction_y,
            )

            if length <= 0:
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

                    "unit_x": (
                        direction_x
                        / length
                    ),

                    "unit_y": (
                        direction_y
                        / length
                    ),

                    "length_meters": (
                        length
                    ),

                    "start_distance_meters": (
                        cumulative_length
                    ),

                    "end_distance_meters": (
                        cumulative_length
                        + length
                    ),
                }
            )

            cumulative_length += length

    return (
        segments,
        cumulative_length,
    )


# ============================================================
# Point-to-street relationship
# ============================================================

def nearest_point_on_segment(
    point_x,
    point_y,
    street_segment,
):
    start_x = street_segment[
        "start_x"
    ]

    start_y = street_segment[
        "start_y"
    ]

    end_x = street_segment[
        "end_x"
    ]

    end_y = street_segment[
        "end_y"
    ]

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

    if length_squared <= 0:
        return None

    fraction = (
        (
            point_x
            - start_x
        )
        * direction_x
        + (
            point_y
            - start_y
        )
        * direction_y
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

    distance = math.hypot(
        point_x
        - nearest_x,
        point_y
        - nearest_y,
    )

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

    distance_along = (
        street_segment[
            "start_distance_meters"
        ]
        + fraction
        * street_segment[
            "length_meters"
        ]
    )

    return {
        "distance_meters": (
            distance
        ),

        "fraction": (
            fraction
        ),

        "cross_product": (
            cross_product
        ),

        "distance_along_meters": (
            distance_along
        ),

        "nearest_x": (
            nearest_x
        ),

        "nearest_y": (
            nearest_y
        ),
    }


# ============================================================
# Find nearest relationship for one driveway
# ============================================================

def find_driveway_street_relationship(
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

    for (
        longitude,
        latitude,
    ) in coordinate_pairs:

        (
            point_x,
            point_y,
        ) = lonlat_to_local_xy(
            longitude,
            latitude,
            reference_longitude,
            reference_latitude,
        )

        for street_segment in (
            street_segments
        ):
            relationship = (
                nearest_point_on_segment(
                    point_x,
                    point_y,
                    street_segment,
                )
            )

            if relationship is None:
                continue

            if (
                best_result is None
                or relationship[
                    "distance_meters"
                ]
                < best_result[
                    "distance_meters"
                ]
            ):
                best_result = {
                    **relationship,

                    "street_segment": (
                        street_segment
                    ),

                    "driveway_longitude": (
                        longitude
                    ),

                    "driveway_latitude": (
                        latitude
                    ),
                }

    if best_result is None:
        return None

    cross_product = best_result[
        "cross_product"
    ]

    if cross_product > 0:
        best_result[
            "geometric_side"
        ] = "LEFT"

        best_result[
            "parity_side"
        ] = "ODD"

    elif cross_product < 0:
        best_result[
            "geometric_side"
        ] = "RIGHT"

        best_result[
            "parity_side"
        ] = "EVEN"

    else:
        best_result[
            "geometric_side"
        ] = "ON_LINE"

        best_result[
            "parity_side"
        ] = "UNKNOWN"

    return best_result


# ============================================================
# Estimate driveway frontage width
# ============================================================

def estimate_driveway_frontage_width(
    feature,
    relationship,
    reference_longitude,
    reference_latitude,
):
    """
    Estimate driveway frontage by projecting all driveway
    polygon vertices onto the direction of the nearest
    Conway centerline piece.

    This result is ESTIMATED. It is not an official or
    field-surveyed curb-opening measurement.
    """

    coordinate_pairs = (
        get_feature_coordinate_pairs(
            feature
        )
    )

    if not coordinate_pairs:
        return None

    street_segment = relationship[
        "street_segment"
    ]

    unit_x = street_segment[
        "unit_x"
    ]

    unit_y = street_segment[
        "unit_y"
    ]

    normal_x = (
        -unit_y
    )

    normal_y = (
        unit_x
    )

    origin_x = relationship[
        "nearest_x"
    ]

    origin_y = relationship[
        "nearest_y"
    ]

    longitudinal_projections = []

    lateral_projections = []

    for (
        longitude,
        latitude,
    ) in coordinate_pairs:

        (
            point_x,
            point_y,
        ) = lonlat_to_local_xy(
            longitude,
            latitude,
            reference_longitude,
            reference_latitude,
        )

        relative_x = (
            point_x
            - origin_x
        )

        relative_y = (
            point_y
            - origin_y
        )

        longitudinal_projection = (
            relative_x
            * unit_x
            + relative_y
            * unit_y
        )

        lateral_projection = (
            relative_x
            * normal_x
            + relative_y
            * normal_y
        )

        longitudinal_projections.append(
            longitudinal_projection
        )

        lateral_projections.append(
            lateral_projection
        )

    if not longitudinal_projections:
        return None

    minimum_longitudinal = min(
        longitudinal_projections
    )

    maximum_longitudinal = max(
        longitudinal_projections
    )

    minimum_lateral = min(
        lateral_projections
    )

    maximum_lateral = max(
        lateral_projections
    )

    frontage_width = (
        maximum_longitudinal
        - minimum_longitudinal
    )

    polygon_depth = (
        maximum_lateral
        - minimum_lateral
    )

    if frontage_width < 0:
        frontage_width = 0.0

    return {
        "estimated_frontage_width_meters": (
            round(
                frontage_width,
                2,
            )
        ),

        "estimated_polygon_depth_meters": (
            round(
                polygon_depth,
                2,
            )
        ),

        "minimum_longitudinal_projection": (
            round(
                minimum_longitudinal,
                2,
            )
        ),

        "maximum_longitudinal_projection": (
            round(
                maximum_longitudinal,
                2,
            )
        ),

        "minimum_lateral_projection": (
            round(
                minimum_lateral,
                2,
            )
        ),

        "maximum_lateral_projection": (
            round(
                maximum_lateral,
                2,
            )
        ),

        "polygon_vertex_count": (
            len(
                coordinate_pairs
            )
        ),
    }


# ============================================================
# Measurement review status
# ============================================================

def determine_review_status(
    width_meters,
    distance_meters,
    parity_side,
):
    review_reasons = []

    if parity_side not in {
        "ODD",
        "EVEN",
    }:
        review_reasons.append(
            "Side classification is unknown."
        )

    if (
        width_meters
        < MIN_REASONABLE_WIDTH_METERS
    ):
        review_reasons.append(
            "Estimated width is below the "
            "configured reasonable minimum."
        )

    if (
        width_meters
        > MAX_REASONABLE_WIDTH_METERS
    ):
        review_reasons.append(
            "Estimated width exceeds the "
            "configured reasonable maximum."
        )

    if (
        distance_meters
        > 10.0
    ):
        review_reasons.append(
            "Driveway polygon is more than "
            "10 meters from the centerline."
        )

    if review_reasons:
        return (
            "REVIEW_REQUIRED",
            review_reasons,
        )

    return (
        "ESTIMATED",
        [],
    )


# ============================================================
# Analyze one driveway
# ============================================================

def measure_driveway(
    feature,
    feature_number,
    street_segments,
    reference_longitude,
    reference_latitude,
):
    relationship = (
        find_driveway_street_relationship(
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
    )

    if relationship is None:
        return None

    if (
        relationship[
            "distance_meters"
        ]
        > MAX_CANDIDATE_DISTANCE_METERS
    ):
        return None

    width_result = (
        estimate_driveway_frontage_width(
            feature=feature,
            relationship=relationship,
            reference_longitude=(
                reference_longitude
            ),
            reference_latitude=(
                reference_latitude
            ),
        )
    )

    if width_result is None:
        return None

    width_meters = width_result[
        "estimated_frontage_width_meters"
    ]

    (
        review_status,
        review_reasons,
    ) = determine_review_status(
        width_meters=width_meters,
        distance_meters=(
            relationship[
                "distance_meters"
            ]
        ),
        parity_side=(
            relationship[
                "parity_side"
            ]
        ),
    )

    properties = feature.get(
        "properties",
        {},
    )

    driveway_id = properties.get(
        "DRIVEWAY_ID"
    )

    exclusion_id = (
        f"{relationship['parity_side'].lower()}-"
        f"driveway-"
        f"{driveway_id}"
    )

    return {
        "exclusion_id": exclusion_id,

        "exclusion_type": "DRIVEWAY",

        "feature_number": (
            feature_number
        ),

        "object_id": properties.get(
            "OBJECTID"
        ),

        "driveway_id": driveway_id,

        "driveway_record_id": (
            properties.get(
                "DRIVEWAY_"
            )
        ),

        "global_id": properties.get(
            "GlobalID"
        ),

        "driveway_type": clean_value(
            properties.get(
                "TYPE"
            )
        ),

        "geometric_side": (
            relationship[
                "geometric_side"
            ]
        ),

        "parity_side": (
            relationship[
                "parity_side"
            ]
        ),

        "distance_to_centerline_meters": (
            round(
                relationship[
                    "distance_meters"
                ],
                2,
            )
        ),

        "position_along_segment_meters": (
            round(
                relationship[
                    "distance_along_meters"
                ],
                2,
            )
        ),

        "estimated_frontage_width_meters": (
            width_meters
        ),

        "estimated_polygon_depth_meters": (
            width_result[
                "estimated_polygon_depth_meters"
            ]
        ),

        "polygon_vertex_count": (
            width_result[
                "polygon_vertex_count"
            ]
        ),

        "nearest_polygon_latitude": (
            relationship[
                "driveway_latitude"
            ]
        ),

        "nearest_polygon_longitude": (
            relationship[
                "driveway_longitude"
            ]
        ),

        "measurement_status": (
            "ESTIMATED"
        ),

        "review_status": (
            review_status
        ),

        "review_reasons": (
            review_reasons
        ),

        "source": (
            "City of Worcester Driveways GIS"
        ),

        "methodology": (
            "Estimated frontage width is calculated "
            "by projecting driveway polygon vertices "
            "onto the local direction of the nearest "
            "Conway Street centerline piece. The "
            "projection span is used as the estimated "
            "driveway frontage. The result is not a "
            "field-surveyed or official curb-opening "
            "measurement."
        ),
    }


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Driveway Width Estimator"
    )

    print(
        "======================================="
    )

    print()

    # --------------------------------------------------------
    # Load data
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

    if (
        driveway_data.get("type")
        != "FeatureCollection"
    ):
        print(
            "ERROR: Driveway file is not "
            "a GeoJSON FeatureCollection."
        )

        return

    if not driveway_features:
        print(
            "ERROR: No driveway features "
            "were found."
        )

        return

    # --------------------------------------------------------
    # Find Conway
    # --------------------------------------------------------

    conway_feature = find_segment(
        parking_features,
        TARGET_SEGMENT_ID,
    )

    if conway_feature is None:
        print(
            "ERROR: Conway segment "
            f"{TARGET_SEGMENT_ID} "
            "was not found."
        )

        return

    properties = conway_feature.get(
        "properties",
        {},
    )

    geometry = conway_feature.get(
        "geometry",
        {},
    )

    street_name = str(
        properties.get(
            "street_name"
        )
        or ""
    ).strip()

    restricted_side = str(
        properties.get(
            "no_parking_side"
        )
        or ""
    ).strip().upper()

    street_lines = (
        normalize_street_lines(
            geometry
        )
    )

    if not street_lines:
        print(
            "ERROR: Conway geometry could "
            "not be normalized."
        )

        return

    reference_coordinate = (
        get_reference_coordinate(
            street_lines
        )
    )

    if reference_coordinate is None:
        print(
            "ERROR: Conway reference "
            "coordinate could not be created."
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
            "ERROR: Conway geometry contains "
            "no usable centerline pieces."
        )

        return

    # --------------------------------------------------------
    # Measure driveway candidates
    # --------------------------------------------------------

    measurements = []

    for feature_number, feature in enumerate(
        driveway_features,
        start=1,
    ):
        measurement = measure_driveway(
            feature=feature,
            feature_number=feature_number,
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

        if measurement is None:
            continue

        measurements.append(
            measurement
        )

    measurements.sort(
        key=lambda item: (
            item[
                "position_along_segment_meters"
            ],
            item[
                "distance_to_centerline_meters"
            ],
        )
    )

    odd_measurements = [
        item
        for item in measurements
        if (
            item["parity_side"]
            == "ODD"
        )
    ]

    even_measurements = [
        item
        for item in measurements
        if (
            item["parity_side"]
            == "EVEN"
        )
    ]

    unknown_measurements = [
        item
        for item in measurements
        if (
            item["parity_side"]
            == "UNKNOWN"
        )
    ]

    review_required = [
        item
        for item in measurements
        if (
            item["review_status"]
            == "REVIEW_REQUIRED"
        )
    ]

    odd_width_sum = round(
        sum(
            item[
                "estimated_frontage_width_meters"
            ]
            for item in odd_measurements
        ),
        2,
    )

    even_width_sum = round(
        sum(
            item[
                "estimated_frontage_width_meters"
            ]
            for item in even_measurements
        ),
        2,
    )

    total_width_sum = round(
        odd_width_sum
        + even_width_sum,
        2,
    )

    # --------------------------------------------------------
    # Build output file
    # --------------------------------------------------------

    output = {
        "dataset_name": (
            "BanReady Conway Driveway Measurements"
        ),

        "street_name": (
            street_name
        ),

        "segment_id": (
            TARGET_SEGMENT_ID
        ),

        "restricted_side": (
            restricted_side
        ),

        "segment_length_meters": (
            round(
                street_length,
                2,
            )
        ),

        "measurement_status": (
            "ESTIMATED"
        ),

        "inventory_update_status": (
            "REVIEW_REQUIRED"
        ),

        "candidate_distance_meters": (
            MAX_CANDIDATE_DISTANCE_METERS
        ),

        "summary": {
            "measurement_count": (
                len(measurements)
            ),

            "odd_measurement_count": (
                len(odd_measurements)
            ),

            "even_measurement_count": (
                len(even_measurements)
            ),

            "unknown_side_count": (
                len(unknown_measurements)
            ),

            "review_required_count": (
                len(review_required)
            ),

            "odd_estimated_width_sum_meters": (
                odd_width_sum
            ),

            "even_estimated_width_sum_meters": (
                even_width_sum
            ),

            "combined_estimated_width_sum_meters": (
                total_width_sum
            ),
        },

        "methodology": (
            "Each driveway polygon is associated with "
            "the nearest Conway Street centerline piece. "
            "The polygon vertices are projected onto the "
            "local street direction, and the projection "
            "span is used as an estimated driveway "
            "frontage width. Results require evidence "
            "review before entering the Conway curb "
            "inventory."
        ),

        "measurements": (
            measurements
        ),
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
    # Display measurements
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
        f"Centerline length:"
        f" {street_length:.2f} m"
    )

    print(
        f"Restricted side:  "
        f"{restricted_side}"
    )

    print()

    print("MEASUREMENT SUMMARY")
    print("===================")
    print()

    print(
        f"Measured candidates:       "
        f"{len(measurements)}"
    )

    print(
        f"ODD / LEFT candidates:     "
        f"{len(odd_measurements)}"
    )

    print(
        f"EVEN / RIGHT candidates:   "
        f"{len(even_measurements)}"
    )

    print(
        f"Unknown-side candidates:   "
        f"{len(unknown_measurements)}"
    )

    print(
        f"Review required:           "
        f"{len(review_required)}"
    )

    print()

    print(
        f"ODD estimated width sum:   "
        f"{odd_width_sum:.2f} m"
    )

    print(
        f"EVEN estimated width sum:  "
        f"{even_width_sum:.2f} m"
    )

    print(
        f"Combined estimated sum:    "
        f"{total_width_sum:.2f} m"
    )

    print()

    print("DRIVEWAY MEASUREMENTS")
    print("=====================")
    print()

    for index, measurement in enumerate(
        measurements,
        start=1,
    ):
        print(
            f"Measurement {index}"
        )

        print(
            "-" * 50
        )

        print(
            f"Exclusion ID:       "
            f"{measurement['exclusion_id']}"
        )

        print(
            f"Driveway ID:        "
            f"{measurement['driveway_id']}"
        )

        print(
            f"Type:               "
            f"{measurement['driveway_type']}"
        )

        print(
            f"Side:               "
            f"{measurement['parity_side']} / "
            f"{measurement['geometric_side']}"
        )

        print(
            f"Position:           "
            f"{measurement['position_along_segment_meters']:.2f} m"
        )

        print(
            f"Centerline offset:  "
            f"{measurement['distance_to_centerline_meters']:.2f} m"
        )

        print(
            f"Estimated frontage: "
            f"{measurement['estimated_frontage_width_meters']:.2f} m"
        )

        print(
            f"Polygon depth:      "
            f"{measurement['estimated_polygon_depth_meters']:.2f} m"
        )

        print(
            f"Review status:      "
            f"{measurement['review_status']}"
        )

        if measurement[
            "review_reasons"
        ]:
            print(
                "Review reasons:"
            )

            for reason in measurement[
                "review_reasons"
            ]:
                print(
                    f"  - {reason}"
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
            "Street is CONWAY ST",
            (
                street_name
                == EXPECTED_STREET_NAME
            ),
        )
    )

    checks.append(
        (
            "Restricted side is EVEN",
            (
                restricted_side
                == EXPECTED_RESTRICTED_SIDE
            ),
        )
    )

    checks.append(
        (
            "Conway length approximately 253.31 m",
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
            "14 driveway candidates measured",
            (
                len(measurements)
                == 14
            ),
        )
    )

    checks.append(
        (
            "8 ODD driveway measurements",
            (
                len(odd_measurements)
                == 8
            ),
        )
    )

    checks.append(
        (
            "6 EVEN driveway measurements",
            (
                len(even_measurements)
                == 6
            ),
        )
    )

    checks.append(
        (
            "No unknown-side measurements",
            (
                len(unknown_measurements)
                == 0
            ),
        )
    )

    checks.append(
        (
            "All widths are positive",
            all(
                item[
                    "estimated_frontage_width_meters"
                ]
                > 0
                for item in measurements
            ),
        )
    )

    checks.append(
        (
            "ODD width sum does not exceed curb base",
            (
                odd_width_sum
                <= street_length
            ),
        )
    )

    checks.append(
        (
            "EVEN width sum does not exceed curb base",
            (
                even_width_sum
                <= street_length
            ),
        )
    )

    checks.append(
        (
            "Every measurement is ESTIMATED",
            all(
                item[
                    "measurement_status"
                ]
                == "ESTIMATED"
                for item in measurements
            ),
        )
    )

    checks.append(
        (
            "All exclusion IDs are unique",
            (
                len(
                    {
                        item[
                            "exclusion_id"
                        ]
                        for item
                        in measurements
                    }
                )
                == len(measurements)
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
        "========================================="
    )

    print(
        "BANREADY DRIVEWAY MEASUREMENT SUMMARY"
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
        f"{passed_checks}"
    )

    print(
        f"Failed:       "
        f"{failed_checks}"
    )

    print()

    if failed_checks == 0:
        print(
            "DRIVEWAY MEASUREMENT CHECKS PASSED"
        )

    else:
        print(
            "DRIVEWAY MEASUREMENT CHECKS FAILED"
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
        "These frontage widths are ESTIMATED "
        "from GIS polygon geometry."
    )

    print()

    print(
        "Do not automatically copy them into "
        "the Conway curb inventory until the "
        "measurement and overlap review is complete."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
