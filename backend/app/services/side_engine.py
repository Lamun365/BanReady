import math
from dataclasses import dataclass
from typing import Optional


# ============================================================
# Side constants
# ============================================================

LEFT = "LEFT"
RIGHT = "RIGHT"
ON_CENTERLINE = "ON_CENTERLINE"
UNKNOWN = "UNKNOWN"


# ============================================================
# Result model
# ============================================================

@dataclass
class SideResult:
    geometric_side: str
    distance_meters: float
    segment_index: Optional[int]
    closest_latitude: Optional[float]
    closest_longitude: Optional[float]


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
    Convert latitude/longitude into approximate local
    Cartesian coordinates in meters around a reference point.
    """

    earth_radius = 6371000.0

    x = (
        math.radians(longitude - reference_longitude)
        * earth_radius
        * math.cos(math.radians(reference_latitude))
    )

    y = (
        math.radians(latitude - reference_latitude)
        * earth_radius
    )

    return x, y


# ============================================================
# Find closest point on one street segment
# ============================================================

def closest_point_on_segment(
    point_lat,
    point_lon,
    start_lat,
    start_lon,
    end_lat,
    end_lon,
):
    """
    Find the closest point on one street segment.

    Coordinates are converted into a local meter-based
    coordinate system centered on the selected point.
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

    length_squared = (
        ab_x * ab_x
        + ab_y * ab_y
    )

    # Handle a zero-length segment.
    if length_squared == 0:
        distance = math.sqrt(
            ax * ax + ay * ay
        )

        return {
            "distance": distance,
            "t": 0.0,
            "ax": ax,
            "ay": ay,
            "bx": bx,
            "by": by,
            "closest_x": ax,
            "closest_y": ay,
        }

    ap_x = px - ax
    ap_y = py - ay

    t = (
        ap_x * ab_x
        + ap_y * ab_y
    ) / length_squared

    # Restrict projection to the actual segment.
    t = max(
        0.0,
        min(1.0, t),
    )

    closest_x = ax + t * ab_x
    closest_y = ay + t * ab_y

    distance = math.sqrt(
        closest_x * closest_x
        + closest_y * closest_y
    )

    return {
        "distance": distance,
        "t": t,
        "ax": ax,
        "ay": ay,
        "bx": bx,
        "by": by,
        "closest_x": closest_x,
        "closest_y": closest_y,
    }


# ============================================================
# Determine geometric LEFT / RIGHT
# ============================================================

def determine_geometric_side(
    point_lat,
    point_lon,
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    centerline_tolerance_meters=1.0,
):
    """
    Determine whether a selected point is geometrically
    LEFT or RIGHT of a directed street segment.

    IMPORTANT:
    LEFT / RIGHT does not mean ODD / EVEN.
    """

    segment = closest_point_on_segment(
        point_lat,
        point_lon,
        start_lat,
        start_lon,
        end_lat,
        end_lon,
    )

    # If the selected location is extremely close to the
    # centerline, avoid pretending that a side is known.
    if (
        segment["distance"]
        <= centerline_tolerance_meters
    ):
        return ON_CENTERLINE

    ax = segment["ax"]
    ay = segment["ay"]

    bx = segment["bx"]
    by = segment["by"]

    # Selected location is local origin.
    px = 0.0
    py = 0.0

    street_x = bx - ax
    street_y = by - ay

    point_x = px - ax
    point_y = py - ay

    # 2D cross product determines whether the point
    # is left or right of the directed street segment.
    cross_product = (
        street_x * point_y
        - street_y * point_x
    )

    if cross_product > 0:
        return LEFT

    if cross_product < 0:
        return RIGHT

    return ON_CENTERLINE


# ============================================================
# Convert local meters back to latitude / longitude
# ============================================================

def local_meters_to_lat_lon(
    x,
    y,
    reference_latitude,
    reference_longitude,
):
    """
    Convert local meter coordinates back into approximate
    latitude/longitude coordinates.
    """

    earth_radius = 6371000.0

    latitude = (
        reference_latitude
        + math.degrees(
            y / earth_radius
        )
    )

    longitude = (
        reference_longitude
        + math.degrees(
            x
            / (
                earth_radius
                * math.cos(
                    math.radians(reference_latitude)
                )
            )
        )
    )

    return latitude, longitude


# ============================================================
# Normalize LineString / MultiLineString coordinates
# ============================================================

def normalize_line_coordinates(coordinates):
    """
    Convert supported GeoJSON street coordinate structures
    into a list of simple LineStrings.

    A LineString:

        [
            [lon, lat],
            [lon, lat],
            [lon, lat]
        ]

    becomes:

        [
            [
                [lon, lat],
                [lon, lat],
                [lon, lat]
            ]
        ]

    A MultiLineString:

        [
            [
                [lon, lat],
                [lon, lat]
            ],
            [
                [lon, lat],
                [lon, lat]
            ]
        ]

    becomes a list containing both individual line parts.
    """

    if not coordinates:
        return []

    first = coordinates[0]

    # --------------------------------------------------------
    # Standard LineString
    # --------------------------------------------------------

    if (
        isinstance(first, (list, tuple))
        and len(first) >= 2
        and isinstance(first[0], (int, float))
        and isinstance(first[1], (int, float))
    ):
        return [coordinates]

    # --------------------------------------------------------
    # Nested coordinates, including MultiLineString
    # --------------------------------------------------------

    lines = []

    for item in coordinates:
        if not isinstance(item, (list, tuple)):
            continue

        lines.extend(
            normalize_line_coordinates(item)
        )

    return lines


# ============================================================
# Determine side of complete street geometry
# ============================================================

def determine_side_of_linestring(
    latitude,
    longitude,
    coordinates,
):
    """
    Find the closest portion of the supplied street geometry
    and determine whether the selected point is geometrically
    LEFT or RIGHT of that portion.

    Supports both:

        LineString
        MultiLineString

    The function accepts only the geometry coordinates because
    the caller already extracts those from the GeoJSON feature.

    IMPORTANT:
    geometric LEFT / RIGHT does not automatically mean
    address ODD / EVEN.
    """

    # Normalize simple and nested street geometry into
    # individual LineStrings.
    lines = normalize_line_coordinates(
        coordinates
    )

    if not lines:
        return SideResult(
            geometric_side=UNKNOWN,
            distance_meters=float("inf"),
            segment_index=None,
            closest_latitude=None,
            closest_longitude=None,
        )

    best_segment = None

    best_segment_index = None

    best_start = None
    best_end = None

    global_segment_index = 0

    # --------------------------------------------------------
    # Search every line part
    # --------------------------------------------------------

    for line in lines:

        if len(line) < 2:
            continue

        # ----------------------------------------------------
        # Search every segment inside this LineString
        # ----------------------------------------------------

        for index in range(
            len(line) - 1
        ):
            start = line[index]
            end = line[index + 1]

            # Validate basic GeoJSON coordinate structure.
            if (
                len(start) < 2
                or len(end) < 2
            ):
                global_segment_index += 1
                continue

            start_lon = start[0]
            start_lat = start[1]

            end_lon = end[0]
            end_lat = end[1]

            # Extra protection from malformed/nested
            # coordinates reaching the math functions.
            if not all(
                isinstance(value, (int, float))
                for value in (
                    start_lon,
                    start_lat,
                    end_lon,
                    end_lat,
                )
            ):
                global_segment_index += 1
                continue

            segment = closest_point_on_segment(
                latitude,
                longitude,
                start_lat,
                start_lon,
                end_lat,
                end_lon,
            )

            if (
                best_segment is None
                or segment["distance"]
                < best_segment["distance"]
            ):
                best_segment = segment

                best_segment_index = (
                    global_segment_index
                )

                best_start = start
                best_end = end

            global_segment_index += 1

    # --------------------------------------------------------
    # No usable geometry
    # --------------------------------------------------------

    if (
        best_segment is None
        or best_start is None
        or best_end is None
    ):
        return SideResult(
            geometric_side=UNKNOWN,
            distance_meters=float("inf"),
            segment_index=None,
            closest_latitude=None,
            closest_longitude=None,
        )

    # --------------------------------------------------------
    # Determine LEFT / RIGHT on the closest street segment
    # --------------------------------------------------------

    geometric_side = determine_geometric_side(
        latitude,
        longitude,
        best_start[1],
        best_start[0],
        best_end[1],
        best_end[0],
    )

    # --------------------------------------------------------
    # Calculate approximate closest geographic point
    # --------------------------------------------------------

    closest_lat, closest_lon = (
        local_meters_to_lat_lon(
            best_segment["closest_x"],
            best_segment["closest_y"],
            latitude,
            longitude,
        )
    )

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return SideResult(
        geometric_side=geometric_side,
        distance_meters=best_segment["distance"],
        segment_index=best_segment_index,
        closest_latitude=closest_lat,
        closest_longitude=closest_lon,
    )