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

HYDRANTS_FILE = Path(
    "data/raw/worcester/hydrants/"
    "Conway_Hydrants.geojson"
)

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_hydrant_inspection.json"
)


TARGET_SEGMENT_ID = 821528

EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_STREET_ID = 753050

EXPECTED_RESTRICTED_SIDE = "EVEN"

EXPECTED_SEGMENT_LENGTH_METERS = 253.31


EARTH_RADIUS_METERS = 6371000.0


# ============================================================
# Candidate distance
#
# This is a GIS screening distance only.
#
# It is NOT the legal no-parking clearance around a hydrant.
# ============================================================

MAX_CANDIDATE_DISTANCE_METERS = 20.0


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
# Feature point extraction
# ============================================================

def get_point_coordinate(
    feature,
):
    geometry = feature.get(
        "geometry"
    )

    if not isinstance(
        geometry,
        dict,
    ):
        return None

    if geometry.get(
        "type"
    ) != "Point":
        return None

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    if (
        not isinstance(
            coordinates,
            (list, tuple),
        )
        or len(coordinates) < 2
    ):
        return None

    longitude = coordinates[0]
    latitude = coordinates[1]

    if not (
        is_number(longitude)
        and is_number(latitude)
    ):
        return None

    if not (
        -180 <= longitude <= 180
        and -90 <= latitude <= 90
    ):
        return None

    return {
        "longitude": float(
            longitude
        ),

        "latitude": float(
            latitude
        ),
    }


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
# Build local Conway centerline
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
# Point-to-centerline relationship
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

        "distance_along_meters": (
            distance_along
        ),

        "cross_product": (
            cross_product
        ),

        "nearest_x": (
            nearest_x
        ),

        "nearest_y": (
            nearest_y
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


# ============================================================
# Analyze one hydrant
# ============================================================

def analyze_hydrant(
    feature,
    feature_number,
    street_segments,
    reference_longitude,
    reference_latitude,
):
    point = get_point_coordinate(
        feature
    )

    if point is None:
        return None

    (
        point_x,
        point_y,
    ) = lonlat_to_local_xy(
        point[
            "longitude"
        ],
        point[
            "latitude"
        ],
        reference_longitude,
        reference_latitude,
    )

    best_result = None

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
            best_result = relationship

    if best_result is None:
        return None

    cross_product = best_result[
        "cross_product"
    ]

    if cross_product > 0:
        geometric_side = "LEFT"
        parity_side = "ODD"

    elif cross_product < 0:
        geometric_side = "RIGHT"
        parity_side = "EVEN"

    else:
        geometric_side = "ON_LINE"
        parity_side = "UNKNOWN"

    properties = feature.get(
        "properties",
        {},
    )

    asset_id = clean_value(
        properties.get(
            "wASSET_ID"
        )
    )

    object_id = properties.get(
        "OBJECTID_1"
    )

    if asset_id is not None:
        candidate_id = (
            f"hydrant-{asset_id}"
        )

    elif object_id is not None:
        candidate_id = (
            f"hydrant-object-{object_id}"
        )

    else:
        candidate_id = (
            f"hydrant-feature-{feature_number}"
        )

    street_name = clean_value(
        properties.get(
            "STREET_NAME"
        )
    )

    street_match = (
        street_name is not None
        and street_name.upper()
        == EXPECTED_STREET_NAME
    )

    candidate_by_distance = (
        best_result[
            "distance_meters"
        ]
        <= MAX_CANDIDATE_DISTANCE_METERS
    )

    candidate_evidence = []

    if candidate_by_distance:
        candidate_evidence.append(
            "WITHIN_DISTANCE"
        )

    if street_match:
        candidate_evidence.append(
            "STREET_NAME_MATCH"
        )

    is_candidate = (
        candidate_by_distance
        or street_match
    )

    return {
        "candidate_id": (
            candidate_id
        ),

        "feature_number": (
            feature_number
        ),

        "object_id": (
            object_id
        ),

        "global_id": (
            properties.get(
                "GlobalID"
            )
        ),

        "asset_id": (
            asset_id
        ),

        "kind": clean_value(
            properties.get(
                "KIND"
            )
        ),

        "street_name": (
            street_name
        ),

        "hydrant_location": clean_value(
            properties.get(
                "HYD_LOCATION"
            )
        ),

        "nearest_house": clean_value(
            properties.get(
                "NEAREST_HOUSE"
            )
        ),

        "longitude": (
            point[
                "longitude"
            ]
        ),

        "latitude": (
            point[
                "latitude"
            ]
        ),

        "distance_to_centerline_meters": (
            round(
                best_result[
                    "distance_meters"
                ],
                2,
            )
        ),

        "position_along_segment_meters": (
            round(
                best_result[
                    "distance_along_meters"
                ],
                2,
            )
        ),

        "geometric_side": (
            geometric_side
        ),

        "parity_side": (
            parity_side
        ),

        "street_name_matches_conway": (
            street_match
        ),

        "within_candidate_distance": (
            candidate_by_distance
        ),

        "candidate_evidence": (
            candidate_evidence
        ),

        "is_conway_candidate": (
            is_candidate
        ),

        "measurement_status": (
            "GIS_POINT_INSPECTION"
        ),

        "source": (
            "City of Worcester Hydrant GIS"
        ),
    }


# ============================================================
# Print candidate
# ============================================================

def print_candidate(
    index,
    candidate,
):
    print(
        f"Candidate {index}"
    )

    print(
        "-" * 50
    )

    print(
        f"Candidate ID:       "
        f"{candidate['candidate_id']}"
    )

    print(
        f"OBJECTID:           "
        f"{candidate['object_id']}"
    )

    print(
        f"Asset ID:           "
        f"{candidate['asset_id']}"
    )

    print(
        f"Kind:               "
        f"{candidate['kind']}"
    )

    print(
        f"GIS street name:    "
        f"{candidate['street_name']}"
    )

    print(
        f"Hydrant location:   "
        f"{candidate['hydrant_location']}"
    )

    print(
        f"Nearest house:      "
        f"{candidate['nearest_house']}"
    )

    print()

    print(
        f"Distance to Conway: "
        f"{candidate['distance_to_centerline_meters']:.2f} m"
    )

    print(
        f"Position on Conway: "
        f"{candidate['position_along_segment_meters']:.2f} m"
    )

    print(
        f"Geometric side:     "
        f"{candidate['geometric_side']}"
    )

    print(
        f"Parity side:        "
        f"{candidate['parity_side']}"
    )

    print()

    print(
        f"Street name match:  "
        f"{candidate['street_name_matches_conway']}"
    )

    print(
        f"Within distance:    "
        f"{candidate['within_candidate_distance']}"
    )

    print(
        f"Candidate evidence: "
        f"{', '.join(candidate['candidate_evidence'])}"
    )

    print()

    print(
        "Coordinate:"
    )

    print(
        f"  Latitude:  "
        f"{candidate['latitude']}"
    )

    print(
        f"  Longitude: "
        f"{candidate['longitude']}"
    )

    print()


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Hydrant Spatial Inspector"
    )

    print(
        "========================================"
    )

    print()

    # --------------------------------------------------------
    # Load inputs
    # --------------------------------------------------------

    try:
        hydrant_data = load_json(
            HYDRANTS_FILE
        )

        parking_data = load_json(
            PARKING_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    hydrant_features = (
        hydrant_data.get(
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
        f"Hydrant file: "
        f"{HYDRANTS_FILE}"
    )

    print(
        f"Hydrant GeoJSON type: "
        f"{hydrant_data.get('type')}"
    )

    print(
        f"Hydrant features: "
        f"{len(hydrant_features)}"
    )

    print()

    if (
        hydrant_data.get("type")
        != "FeatureCollection"
    ):
        print(
            "ERROR: Hydrant file is not "
            "a GeoJSON FeatureCollection."
        )

        return

    # --------------------------------------------------------
    # Locate Conway segment
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

    street_id = conway_properties.get(
        "street_id"
    )

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
            "ERROR: Conway has no usable "
            "street geometry pieces."
        )

        return

    # --------------------------------------------------------
    # Analyze hydrants
    # --------------------------------------------------------

    analyses = []

    skipped_features = 0

    for feature_number, feature in enumerate(
        hydrant_features,
        start=1,
    ):
        analysis = analyze_hydrant(
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

        if analysis is None:
            skipped_features += 1
            continue

        analyses.append(
            analysis
        )

    analyses.sort(
        key=lambda item: (
            item[
                "distance_to_centerline_meters"
            ],
            item[
                "position_along_segment_meters"
            ],
        )
    )

    candidates = [
        item
        for item in analyses
        if item[
            "is_conway_candidate"
        ]
    ]

    candidates.sort(
        key=lambda item: (
            item[
                "position_along_segment_meters"
            ],
            item[
                "distance_to_centerline_meters"
            ],
        )
    )

    odd_candidates = [
        item
        for item in candidates
        if item[
            "parity_side"
        ] == "ODD"
    ]

    even_candidates = [
        item
        for item in candidates
        if item[
            "parity_side"
        ] == "EVEN"
    ]

    unknown_candidates = [
        item
        for item in candidates
        if item[
            "parity_side"
        ] == "UNKNOWN"
    ]

    street_name_matches = [
        item
        for item in analyses
        if item[
            "street_name_matches_conway"
        ]
    ]

    # ========================================================
    # Print segment details
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
        f"Street ID:        "
        f"{street_id}"
    )

    print(
        f"Centerline pieces:"
        f" {len(street_segments)}"
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

    # ========================================================
    # Dataset fields and geometry
    # ========================================================

    property_fields = set()

    geometry_types = set()

    for feature in hydrant_features:
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
            geometry_type = geometry.get(
                "type"
            )

            if geometry_type:
                geometry_types.add(
                    geometry_type
                )

    print("HYDRANT DATASET")
    print("===============")
    print()

    print(
        f"Feature count: "
        f"{len(hydrant_features)}"
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
    # Screening summary
    # ========================================================

    print("SPATIAL SCREENING")
    print("=================")
    print()

    print(
        f"Analyzed hydrants:           "
        f"{len(analyses)}"
    )

    print(
        f"Skipped hydrants:            "
        f"{skipped_features}"
    )

    print(
        f"Candidate distance:          "
        f"{MAX_CANDIDATE_DISTANCE_METERS:.2f} m"
    )

    print()

    print(
        f"Conway hydrant candidates:   "
        f"{len(candidates)}"
    )

    print(
        f"ODD / LEFT candidates:       "
        f"{len(odd_candidates)}"
    )

    print(
        f"EVEN / RIGHT candidates:     "
        f"{len(even_candidates)}"
    )

    print(
        f"Unknown-side candidates:     "
        f"{len(unknown_candidates)}"
    )

    print(
        f"STREET_NAME matches Conway:  "
        f"{len(street_name_matches)}"
    )

    print()

    # ========================================================
    # Candidate details
    # ========================================================

    print("CONWAY HYDRANT CANDIDATES")
    print("=========================")
    print()

    if not candidates:
        print(
            "No Conway hydrant candidates "
            "were identified."
        )

        print()

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):
        print_candidate(
            index,
            candidate,
        )

    # ========================================================
    # Ordered side summaries
    # ========================================================

    print("ODD / LEFT HYDRANT CANDIDATES")
    print("=============================")
    print()

    if odd_candidates:
        for index, candidate in enumerate(
            odd_candidates,
            start=1,
        ):
            print(
                f"{index}. "
                f"{candidate['candidate_id']}, "
                f"position="
                f"{candidate['position_along_segment_meters']:.2f} m, "
                f"offset="
                f"{candidate['distance_to_centerline_meters']:.2f} m"
            )
    else:
        print(
            "None"
        )

    print()

    print("EVEN / RIGHT HYDRANT CANDIDATES")
    print("===============================")
    print()

    if even_candidates:
        for index, candidate in enumerate(
            even_candidates,
            start=1,
        ):
            print(
                f"{index}. "
                f"{candidate['candidate_id']}, "
                f"position="
                f"{candidate['position_along_segment_meters']:.2f} m, "
                f"offset="
                f"{candidate['distance_to_centerline_meters']:.2f} m"
            )
    else:
        print(
            "None"
        )

    print()

    # ========================================================
    # Save inspection results
    # ========================================================

    output = {
        "dataset_name": (
            "BanReady Conway Hydrant Inspection"
        ),

        "street_name": (
            street_name
        ),

        "segment_id": (
            TARGET_SEGMENT_ID
        ),

        "street_id": (
            street_id
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

        "inspection_status": (
            "HYDRANT_CANDIDATES_ONLY"
        ),

        "inventory_status": (
            "INCOMPLETE"
        ),

        "legal_clearance_status": (
            "NOT_APPLIED"
        ),

        "candidate_distance_meters": (
            MAX_CANDIDATE_DISTANCE_METERS
        ),

        "summary": {
            "source_feature_count": (
                len(hydrant_features)
            ),

            "analyzed_count": (
                len(analyses)
            ),

            "skipped_count": (
                skipped_features
            ),

            "candidate_count": (
                len(candidates)
            ),

            "odd_candidate_count": (
                len(odd_candidates)
            ),

            "even_candidate_count": (
                len(even_candidates)
            ),

            "unknown_side_count": (
                len(unknown_candidates)
            ),

            "street_name_match_count": (
                len(street_name_matches)
            ),
        },

        "methodology": (
            "Each official Worcester hydrant point is "
            "compared with every centerline piece in "
            "Conway segment 821528. The nearest point "
            "relationship establishes distance, position "
            "along the segment, and geometric side. A "
            "hydrant is retained as a candidate when it "
            "is within the GIS screening distance or "
            "when its official STREET_NAME value matches "
            "CONWAY ST."
        ),

        "limitations": [
            (
                "Candidate status does not automatically "
                "establish that the hydrant controls "
                "parking on segment 821528."
            ),
            (
                "No legal hydrant-clearance distance is "
                "applied by this inspection script."
            ),
            (
                "The hydrant GIS point may not lie exactly "
                "on the curb line."
            ),
            (
                "The Conway curb inventory remains "
                "INCOMPLETE."
            ),
        ],

        "candidates": (
            candidates
        ),

        "all_analyses": (
            analyses
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
    # Methodology notice
    # ========================================================

    print("METHODOLOGY STATUS")
    print("==================")
    print()

    print(
        "This script identifies hydrant candidates "
        "and their positions only."
    )

    print()

    print(
        "No curb-exclusion interval has been created."
    )

    print()

    print(
        "A legally supported hydrant-clearance distance "
        "must be established before hydrant intervals "
        "can enter the Conway curb inventory."
    )

    print()

    print(
        "Therefore the Conway curb inventory must "
        "remain INCOMPLETE."
    )

    print()

    # ========================================================
    # Consistency checks
    # ========================================================

    checks = []

    checks.append(
        (
            "Hydrant GeoJSON is FeatureCollection",
            (
                hydrant_data.get(
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
            "Street ID is 753050",
            (
                street_id
                == EXPECTED_STREET_ID
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
                    - EXPECTED_SEGMENT_LENGTH_METERS
                )
                <= 0.50
            ),
        )
    )

    checks.append(
        (
            "All source hydrants accounted for",
            (
                len(analyses)
                + skipped_features
                == len(
                    hydrant_features
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
                + len(unknown_candidates)
                == len(candidates)
            ),
        )
    )

    checks.append(
        (
            "Candidate positions within segment",
            all(
                0
                <= candidate[
                    "position_along_segment_meters"
                ]
                <= street_length
                for candidate in candidates
            ),
        )
    )

    checks.append(
        (
            "Candidate distances nonnegative",
            all(
                candidate[
                    "distance_to_centerline_meters"
                ]
                >= 0
                for candidate in candidates
            ),
        )
    )

    checks.append(
        (
            "No hydrant clearance invented",
            (
                output[
                    "legal_clearance_status"
                ]
                == "NOT_APPLIED"
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
        "======================================"
    )

    print(
        "BANREADY HYDRANT INSPECTION SUMMARY"
    )

    print(
        "======================================"
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
            "CONWAY HYDRANT INSPECTION PASSED"
        )
    else:
        print(
            "CONWAY HYDRANT INSPECTION FAILED"
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
        "Hydrant candidates are not yet curb "
        "exclusion intervals."
    )

    print()

    print(
        "Do not update the Conway curb inventory "
        "until candidate relevance and a legally "
        "supported clearance distance are established."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
