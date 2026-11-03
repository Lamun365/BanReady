import math
from dataclasses import dataclass
from typing import Any, Optional

from backend.app.services.side_engine import (
    normalize_line_coordinates,
)


# ============================================================
# Configuration
# ============================================================

DEFAULT_MAX_MATCH_DISTANCE_METERS = 50.0


# ============================================================
# Result model
# ============================================================

@dataclass
class StreetMatchResult:
    matched: bool
    feature: Optional[dict[str, Any]]
    distance_meters: float

    street_name: str
    segment_id: Optional[int]
    street_id: Optional[int]

    ban_type: str
    ban_zone: str
    restricted_side: str

    reason: str


# ============================================================
# Coordinate conversion
# ============================================================

def lat_lon_to_local_meters(
    latitude,
    longitude,
    reference_latitude,
    reference_longitude,
):
    """
    Convert latitude and longitude differences into
    approximate local X/Y distances in meters.
    """

    earth_radius = 6371000.0

    x = (
        math.radians(longitude - reference_longitude)
        * earth_radius
        * math.cos(
            math.radians(reference_latitude)
        )
    )

    y = (
        math.radians(latitude - reference_latitude)
        * earth_radius
    )

    return x, y


# ============================================================
# Point-to-segment distance
# ============================================================

def point_to_segment_distance(
    point_lat,
    point_lon,
    start_lat,
    start_lon,
    end_lat,
    end_lon,
):
    """
    Calculate the shortest distance in meters between
    a selected point and one street line segment.
    """

    px = 0.0
    py = 0.0

    ax, ay = lat_lon_to_local_meters(
        start_lat,
        start_lon,
        point_lat,
        point_lon,
    )

    bx, by = lat_lon_to_local_meters(
        end_lat,
        end_lon,
        point_lat,
        point_lon,
    )

    ab_x = bx - ax
    ab_y = by - ay

    ap_x = px - ax
    ap_y = py - ay

    length_squared = (
        ab_x * ab_x
        + ab_y * ab_y
    )

    if length_squared == 0:
        return math.sqrt(
            (px - ax) ** 2
            + (py - ay) ** 2
        )

    t = (
        ap_x * ab_x
        + ap_y * ab_y
    ) / length_squared

    t = max(
        0.0,
        min(1.0, t),
    )

    closest_x = ax + t * ab_x
    closest_y = ay + t * ab_y

    distance = math.sqrt(
        (px - closest_x) ** 2
        + (py - closest_y) ** 2
    )

    return distance


# ============================================================
# Distance to street geometry
# ============================================================

def distance_to_street_geometry(
    latitude,
    longitude,
    coordinates,
):
    """
    Calculate the minimum distance from a point to a
    LineString or MultiLineString.

    normalize_line_coordinates() converts either geometry
    structure into individual simple lines.
    """

    lines = normalize_line_coordinates(
        coordinates
    )

    if not lines:
        return None

    minimum_distance = float("inf")

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

            distance = point_to_segment_distance(
                latitude,
                longitude,
                start_lat,
                start_lon,
                end_lat,
                end_lon,
            )

            if distance < minimum_distance:
                minimum_distance = distance

    if minimum_distance == float("inf"):
        return None

    return minimum_distance


# ============================================================
# Find nearest Worcester parking-ban segment
# ============================================================

def find_nearest_street(
    latitude,
    longitude,
    parking_features,
    max_match_distance_meters=DEFAULT_MAX_MATCH_DISTANCE_METERS,
):
    """
    Find the Worcester parking-ban street feature nearest
    to the supplied latitude/longitude.

    Supports:
        LineString
        MultiLineString

    Returns a StreetMatchResult.
    """

    # --------------------------------------------------------
    # Validate coordinates
    # --------------------------------------------------------

    if not isinstance(
        latitude,
        (int, float),
    ):
        return StreetMatchResult(
            matched=False,
            feature=None,
            distance_meters=float("inf"),
            street_name="",
            segment_id=None,
            street_id=None,
            ban_type="",
            ban_zone="",
            restricted_side="",
            reason="Latitude must be numeric.",
        )

    if not isinstance(
        longitude,
        (int, float),
    ):
        return StreetMatchResult(
            matched=False,
            feature=None,
            distance_meters=float("inf"),
            street_name="",
            segment_id=None,
            street_id=None,
            ban_type="",
            ban_zone="",
            restricted_side="",
            reason="Longitude must be numeric.",
        )

    if latitude < -90 or latitude > 90:
        return StreetMatchResult(
            matched=False,
            feature=None,
            distance_meters=float("inf"),
            street_name="",
            segment_id=None,
            street_id=None,
            ban_type="",
            ban_zone="",
            restricted_side="",
            reason=(
                "Latitude must be between "
                "-90 and 90."
            ),
        )

    if longitude < -180 or longitude > 180:
        return StreetMatchResult(
            matched=False,
            feature=None,
            distance_meters=float("inf"),
            street_name="",
            segment_id=None,
            street_id=None,
            ban_type="",
            ban_zone="",
            restricted_side="",
            reason=(
                "Longitude must be between "
                "-180 and 180."
            ),
        )

    # --------------------------------------------------------
    # Search street features
    # --------------------------------------------------------

    nearest_feature = None
    nearest_distance = float("inf")

    for feature in parking_features:
        geometry = feature.get(
            "geometry",
            {},
        )

        if not geometry:
            continue

        geometry_type = geometry.get(
            "type"
        )

        if geometry_type not in {
            "LineString",
            "MultiLineString",
        }:
            continue

        coordinates = geometry.get(
            "coordinates",
            [],
        )

        distance = distance_to_street_geometry(
            latitude,
            longitude,
            coordinates,
        )

        if distance is None:
            continue

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_feature = feature

    # --------------------------------------------------------
    # No street geometry found
    # --------------------------------------------------------

    if nearest_feature is None:
        return StreetMatchResult(
            matched=False,
            feature=None,
            distance_meters=float("inf"),
            street_name="",
            segment_id=None,
            street_id=None,
            ban_type="",
            ban_zone="",
            restricted_side="",
            reason=(
                "BanReady could not find a usable "
                "Worcester street segment."
            ),
        )

    properties = nearest_feature.get(
        "properties",
        {},
    )

    street_name = str(
        properties.get("street_name")
        or ""
    ).strip()

    segment_id = properties.get(
        "segment_id"
    )

    street_id = properties.get(
        "street_id"
    )

    ban_type = str(
        properties.get("ban_type")
        or ""
    ).strip().upper()

    ban_zone = str(
        properties.get("ban_zone")
        or ""
    ).strip().upper()

    restricted_side = str(
        properties.get("no_parking_side")
        or ""
    ).strip().upper()

    # --------------------------------------------------------
    # Reject unreliable match
    # --------------------------------------------------------

    if (
        nearest_distance
        > max_match_distance_meters
    ):
        return StreetMatchResult(
            matched=False,
            feature=nearest_feature,
            distance_meters=nearest_distance,
            street_name=street_name,
            segment_id=segment_id,
            street_id=street_id,
            ban_type=ban_type,
            ban_zone=ban_zone,
            restricted_side=restricted_side,
            reason=(
                "The nearest Worcester street is "
                f"{nearest_distance:.2f} meters away, "
                "which exceeds BanReady's current "
                f"{max_match_distance_meters:.0f}-meter "
                "matching threshold."
            ),
        )

    # --------------------------------------------------------
    # Successful street match
    # --------------------------------------------------------

    return StreetMatchResult(
        matched=True,
        feature=nearest_feature,
        distance_meters=nearest_distance,
        street_name=street_name,
        segment_id=segment_id,
        street_id=street_id,
        ban_type=ban_type,
        ban_zone=ban_zone,
        restricted_side=restricted_side,
        reason=(
            "A Worcester parking-ban street "
            "segment was matched successfully."
        ),
    )