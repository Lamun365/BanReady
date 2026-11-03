from __future__ import annotations
from math import cos, hypot, radians

import hashlib
from typing import Any


def stable_number(
    seed: str | int,
    minimum: int,
    maximum: int,
    salt: str,
) -> int:
    """
    Return a deterministic synthetic integer.

    The same segment ID and salt always produce
    the same value.
    """

    if maximum < minimum:
        raise ValueError(
            "maximum must be greater than "
            "or equal to minimum"
        )

    seed_text = str(seed)

    digest = hashlib.sha256(
        f"{seed_text}:{salt}".encode("utf-8")
    ).hexdigest()

    numeric_value = int(
        digest[:12],
        16,
    )

    value_range = (
        maximum
        - minimum
        + 1
    )

    return (
        minimum
        + numeric_value
        % value_range
    )


def normalize_side(
    value: str | None,
) -> str:
    if value is None:
        return "UNKNOWN"

    normalized = (
        value
        .strip()
        .upper()
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )

    mappings = {
        "LEFT": "LEFT",
        "RIGHT": "RIGHT",
        "ODD": "ODD",
        "EVEN": "EVEN",
        "BOTH": "BOTH",
        "ALL": "BOTH",
        "NONE": "NONE",
        "NO_RESTRICTION": "NONE",
        "UNKNOWN": "UNKNOWN",
        "UNSURE": "UNKNOWN",
    }

    return mappings.get(
        normalized,
        normalized or "UNKNOWN",
    )


def derive_legal_side(
    restricted_side: str,
) -> str:
    """
    Convert the real modeled restricted side into
    the side potentially legal during the ban.
    """

    side = normalize_side(
        restricted_side
    )

    if side == "ODD":
        return "EVEN"

    if side == "EVEN":
        return "ODD"

    if side == "LEFT":
        return "RIGHT"

    if side == "RIGHT":
        return "LEFT"

    if side == "BOTH":
        return "NONE"

    if side == "NONE":
        return "BOTH"

    return "VERIFY"


def chance_level(
    chance_percent: int,
) -> str:
    if chance_percent < 35:
        return "LOW"

    if chance_percent < 65:
        return "MEDIUM"

    return "HIGH"


def chance_message(
    level: str,
) -> str:
    messages = {
        "LOW": (
            "Low modeled chance here. "
            "Explore nearby streets."
        ),
        "MEDIUM": (
            "Moderate modeled chance here. "
            "Nearby streets may offer alternatives."
        ),
        "HIGH": (
            "Higher modeled chance under this "
            "prototype scenario."
        ),
    }

    return messages[level]


def generate_segment_metrics(
    segment_id: int | None,
    street_name: str,
) -> dict[str, int | str]:
    """
    Generate repeatable synthetic supply,
    demand, request, and chance values.
    """

    seed: str | int

    if segment_id is not None:
        seed = segment_id
    else:
        seed = (
            street_name
            .strip()
            .upper()
        )

    legal_spaces = stable_number(
        seed=seed,
        minimum=18,
        maximum=55,
        salt="legal-spaces",
    )

    expected_vehicles = stable_number(
        seed=seed,
        minimum=20,
        maximum=65,
        salt="expected-vehicles",
    )

    prototype_requests = stable_number(
        seed=seed,
        minimum=2,
        maximum=18,
        salt="prototype-requests",
    )

    raw_chance = round(
        70
        + (
            legal_spaces
            - expected_vehicles
        )
        * 4
        - prototype_requests
        * 2.5
    )

    modeled_chance_percent = max(
        5,
        min(
            92,
            raw_chance,
        ),
    )

    level = chance_level(
        modeled_chance_percent
    )

    return {
        "legal_spaces": legal_spaces,
        "expected_vehicles": (
            expected_vehicles
        ),
        "prototype_requests": (
            prototype_requests
        ),
        "modeled_chance_percent": (
            modeled_chance_percent
        ),
        "chance_level": level,
        "message": chance_message(
            level
        ),
    }


def build_modeled_street_analytics(
    *,
    street_name: str,
    segment_id: int | None,
    parked_side: str,
    restricted_side: str,
    ban_type: str,
) -> dict[str, Any]:
    """
    Combine real BanReady street and side values
    with deterministic synthetic prototype metrics.
    """

    cleaned_street_name = (
        street_name
        .strip()
        .upper()
        or "UNKNOWN STREET"
    )

    metrics = generate_segment_metrics(
        segment_id=segment_id,
        street_name=cleaned_street_name,
    )

    return {
        "data_status": (
            "SYNTHETIC_PROTOTYPE"
        ),
        "street_name": (
            cleaned_street_name
        ),
        "segment_id": segment_id,
        "ban_type": (
            ban_type
            .strip()
            .upper()
        ),
        "parked_side": normalize_side(
            parked_side
        ),
        "restricted_side": normalize_side(
            restricted_side
        ),
        "legal_side": derive_legal_side(
            restricted_side
        ),
        **metrics,
        "disclosure": (
            "Synthetic prototype estimate "
            "using the real matched Worcester "
            "street and modeled ban side. "
            "Not live parking availability."
        ),
    }

def normalize_street_name(
    value: str | None,
) -> str:
    if value is None:
        return "UNKNOWN STREET"

    cleaned = " ".join(
        value
        .strip()
        .upper()
        .split()
    )

    return cleaned or "UNKNOWN STREET"


def feature_properties(
    feature: dict[str, Any],
) -> dict[str, Any]:
    properties = feature.get(
        "properties"
    )

    if isinstance(properties, dict):
        return properties

    return feature


def get_first_value(
    data: dict[str, Any],
    names: tuple[str, ...],
    default: Any = None,
) -> Any:
    for name in names:
        if name in data:
            value = data[name]

            if value is not None and value != "":
                return value

    return default


def extract_segment_id(
    feature: dict[str, Any],
) -> int | None:
    properties = feature_properties(
        feature
    )

    raw_value = get_first_value(
        properties,
        (
            "segment_id",
            "SEGMENT_ID",
            "segmentid",
            "SEGMENTID",
            "OBJECTID",
            "objectid",
        ),
    )

    if raw_value is None:
        return None

    try:
        return int(raw_value)
    except (
        TypeError,
        ValueError,
    ):
        return None


def extract_street_name(
    feature: dict[str, Any],
) -> str:
    properties = feature_properties(
        feature
    )

    value = get_first_value(
        properties,
        (
            "street_name",
            "STREET_NAME",
            "street",
            "STREET",
            "full_street_name",
            "FULL_STREET_NAME",
            "name",
            "NAME",
        ),
        "UNKNOWN STREET",
    )

    return normalize_street_name(
        str(value)
    )


def extract_restricted_side(
    feature: dict[str, Any],
) -> str:
    properties = feature_properties(
        feature
    )

    value = get_first_value(
        properties,
        (
            "no_parking_side",
            "NO_PARKING_SIDE",
            "restricted_side",
            "RESTRICTED_SIDE",
            "side",
            "SIDE",
            "ban_side",
            "BAN_SIDE",
        ),
        "UNKNOWN",
    )

    return normalize_side(
        str(value)
    )


def extract_geometry(
    feature: dict[str, Any],
) -> dict[str, Any] | None:
    geometry = feature.get(
        "geometry"
    )

    if isinstance(geometry, dict):
        return geometry

    return None


def iter_coordinate_lines(
    geometry: dict[str, Any],
) -> list[list[list[float]]]:
    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates"
    )

    if not isinstance(
        coordinates,
        list,
    ):
        return []

    if geometry_type == "LineString":
        return [coordinates]

    if geometry_type == "MultiLineString":
        return coordinates

    return []


def local_xy_meters(
    *,
    latitude: float,
    longitude: float,
    origin_latitude: float,
    origin_longitude: float,
) -> tuple[float, float]:
    """
    Convert latitude and longitude to local
    planar meters around the requested origin.

    This accuracy is sufficient for the
    500-meter prototype search.
    """

    meters_per_degree_latitude = (
        111_320.0
    )

    meters_per_degree_longitude = (
        111_320.0
        * cos(
            radians(
                origin_latitude
            )
        )
    )

    x = (
        longitude
        - origin_longitude
    ) * meters_per_degree_longitude

    y = (
        latitude
        - origin_latitude
    ) * meters_per_degree_latitude

    return x, y


def point_to_segment_distance(
    *,
    point_x: float,
    point_y: float,
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
) -> float:
    delta_x = end_x - start_x
    delta_y = end_y - start_y

    length_squared = (
        delta_x * delta_x
        + delta_y * delta_y
    )

    if length_squared == 0:
        return hypot(
            point_x - start_x,
            point_y - start_y,
        )

    projection = (
        (
            point_x - start_x
        )
        * delta_x
        + (
            point_y - start_y
        )
        * delta_y
    ) / length_squared

    projection = max(
        0.0,
        min(
            1.0,
            projection,
        ),
    )

    nearest_x = (
        start_x
        + projection * delta_x
    )

    nearest_y = (
        start_y
        + projection * delta_y
    )

    return hypot(
        point_x - nearest_x,
        point_y - nearest_y,
    )


def distance_to_feature_meters(
    *,
    latitude: float,
    longitude: float,
    feature: dict[str, Any],
) -> float | None:
    geometry = extract_geometry(
        feature
    )

    if geometry is None:
        return None

    coordinate_lines = (
        iter_coordinate_lines(
            geometry
        )
    )

    if not coordinate_lines:
        return None

    minimum_distance: (
        float | None
    ) = None

    for line in coordinate_lines:
        if len(line) == 1:
            coordinate = line[0]

            if len(coordinate) < 2:
                continue

            point_x, point_y = (
                local_xy_meters(
                    latitude=coordinate[1],
                    longitude=coordinate[0],
                    origin_latitude=latitude,
                    origin_longitude=longitude,
                )
            )

            distance = hypot(
                point_x,
                point_y,
            )

            if (
                minimum_distance is None
                or distance
                < minimum_distance
            ):
                minimum_distance = (
                    distance
                )

            continue

        for index in range(
            len(line) - 1
        ):
            first = line[index]
            second = line[index + 1]

            if (
                len(first) < 2
                or len(second) < 2
            ):
                continue

            start_x, start_y = (
                local_xy_meters(
                    latitude=first[1],
                    longitude=first[0],
                    origin_latitude=latitude,
                    origin_longitude=longitude,
                )
            )

            end_x, end_y = (
                local_xy_meters(
                    latitude=second[1],
                    longitude=second[0],
                    origin_latitude=latitude,
                    origin_longitude=longitude,
                )
            )

            distance = (
                point_to_segment_distance(
                    point_x=0.0,
                    point_y=0.0,
                    start_x=start_x,
                    start_y=start_y,
                    end_x=end_x,
                    end_y=end_y,
                )
            )

            if (
                minimum_distance is None
                or distance
                < minimum_distance
            ):
                minimum_distance = (
                    distance
                )

    return minimum_distance


def approximate_minutes_from_distance(
    distance_meters: float,
) -> int:
    """
    Approximate time using 80 meters per minute.

    This is not pedestrian routing.
    """

    return max(
        1,
        round(
            distance_meters / 80
        ),
    )


def build_zone_street_item(
    *,
    feature: dict[str, Any],
    distance_meters: float,
) -> dict[str, Any] | None:
    street_name = extract_street_name(
        feature
    )

    if street_name == "UNKNOWN STREET":
        return None

    ban_type = extract_ban_type(
        feature
    )

    if ban_type in {
        "NON-APPLICABLE",
        "NON_APPLICABLE",
        "UNKNOWN",
    }:
        return None

    segment_id = extract_segment_id(
        feature
    )

    restricted_side = (
        extract_restricted_side(
            feature
        )
    )

    legal_side = derive_legal_side(
        restricted_side
    )

    if legal_side in {
        "NONE",
        "VERIFY",
    }:
        return None

    metrics = generate_segment_metrics(
        segment_id=segment_id,
        street_name=street_name,
    )

    return {
        "segment_id": segment_id,
        "street_name": street_name,
        "ban_type": ban_type,
        "restricted_side": restricted_side,
        "legal_side": legal_side,
        "distance_meters": round(
            distance_meters,
            2,
        ),
        "approximate_minutes": (
            approximate_minutes_from_distance(
                distance_meters
            )
        ),
        **metrics,
    }


def calculate_zone_chance(
    streets: list[dict[str, Any]],
) -> int:
    if not streets:
        return 0

    weighted_total = 0.0
    total_weight = 0.0

    for street in streets:
        distance_meters = float(
            street["distance_meters"]
        )

        weight = 1.0 / max(
            50.0,
            distance_meters,
        )

        weighted_total += (
            int(
                street[
                    "modeled_chance_percent"
                ]
            )
            * weight
        )

        total_weight += weight

    if total_weight == 0:
        return 0

    return round(
        weighted_total
        / total_weight
    )


def recommendation_score(
    street: dict[str, Any],
) -> float:
    return (
        float(
            street[
                "modeled_chance_percent"
            ]
        )
        - float(
            street[
                "approximate_minutes"
            ]
        )
        * 3.0
    )


def build_modeled_zone_analytics(
    *,
    latitude: float,
    longitude: float,
    origin_segment_id: int | None,
    radius_meters: float,
    limit: int,
    parking_segments: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:
    """
    Return nearby real Worcester streets with
    deterministic synthetic analytics.

    Street names, segment IDs, restriction sides,
    and distances are derived from real GIS data.
    """

    candidates: list[
        dict[str, Any]
    ] = []

    for feature in parking_segments:
        distance = (
            distance_to_feature_meters(
                latitude=latitude,
                longitude=longitude,
                feature=feature,
            )
        )

        if distance is None:
            continue

        if distance > radius_meters:
            continue

        item = build_zone_street_item(
            feature=feature,
            distance_meters=distance,
        )

        if item is not None:
            candidates.append(
                item
            )

    candidates.sort(
        key=lambda item: (
            item["distance_meters"],
            item["street_name"],
        )
    )

    unique_streets: list[
        dict[str, Any]
    ] = []

    seen_names: set[str] = set()

    for item in candidates:
        normalized_name = (
            normalize_street_name(
                item["street_name"]
            )
        )

        if normalized_name in seen_names:
            continue

        seen_names.add(
            normalized_name
        )

        unique_streets.append(
            item
        )

        if len(unique_streets) >= limit:
            break

    modeled_zone_chance = (
        calculate_zone_chance(
            unique_streets
        )
    )

    prototype_requests = sum(
        int(
            street[
                "prototype_requests"
            ]
        )
        for street in unique_streets
    )

    recommended_street = None

    if unique_streets:
        recommended_street = max(
            unique_streets,
            key=recommendation_score,
        )

    return {
        "data_status": (
            "SYNTHETIC_PROTOTYPE"
        ),
        "origin": {
            "latitude": latitude,
            "longitude": longitude,
            "segment_id": (
                origin_segment_id
            ),
        },
        "radius_meters": (
            radius_meters
        ),
        "modeled_zone_chance_percent": (
            modeled_zone_chance
        ),
        "analyzed_street_count": len(
            unique_streets
        ),
        "prototype_requests": (
            prototype_requests
        ),
        "recommended_segment_id": (
            recommended_street[
                "segment_id"
            ]
            if recommended_street
            else None
        ),
        "recommended_street": (
            recommended_street
        ),
        "streets": unique_streets,
        "disclosure": (
            "Real Worcester street names, "
            "restriction sides, and straight-line "
            "distances with synthetic prototype "
            "supply and demand. Not live parking "
            "availability or calculated walking "
            "routes."
        ),
    }

def extract_ban_type(
    feature: dict[str, Any],
) -> str:
    properties = feature_properties(
        feature
    )

    value = get_first_value(
        properties,
        (
            "ban_type",
            "BAN_TYPE",
            "type",
            "TYPE",
        ),
        "UNKNOWN",
    )

    return (
        str(value)
        .strip()
        .upper()
        or "UNKNOWN"
    )