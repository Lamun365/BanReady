import math
from dataclasses import asdict, dataclass
from typing import Optional


# ============================================================
# Configuration
# ============================================================

EARTH_RADIUS_METERS = 6371000.0


# ============================================================
# Side constants
# ============================================================

ODD = "ODD"
EVEN = "EVEN"

NONE = "NONE"
BOTH = "BOTH"

UNKNOWN = "UNKNOWN"


# ============================================================
# Evidence constants
# ============================================================

ESTIMATED = "ESTIMATED"


# ============================================================
# Street-side capacity result
# ============================================================

@dataclass
class StreetSideCapacity:
    side: str

    segment_length_meters: float

    usable_length_meters: float

    assumed_space_length_meters: float

    normal_capacity: int

    ban_capacity: int

    normal_capacity_status: str

    ban_capacity_status: str

    restricted_during_ban: bool

    methodology: str

    def to_dict(self):
        return asdict(self)


# ============================================================
# Street supply result
# ============================================================

@dataclass
class StreetSupplyResult:
    street_name: str

    segment_id: Optional[int]

    ban_type: str

    restricted_side: str

    segment_length_meters: float

    odd: StreetSideCapacity

    even: StreetSideCapacity

    total_normal_capacity: int

    total_ban_capacity: int

    displaced_capacity: int

    capacity_status: str

    methodology: str

    def to_dict(self):
        return {
            "street_name": self.street_name,
            "segment_id": self.segment_id,
            "ban_type": self.ban_type,
            "restricted_side": self.restricted_side,
            "segment_length_meters": (
                self.segment_length_meters
            ),
            "odd": self.odd.to_dict(),
            "even": self.even.to_dict(),
            "total_normal_capacity": (
                self.total_normal_capacity
            ),
            "total_ban_capacity": (
                self.total_ban_capacity
            ),
            "displaced_capacity": (
                self.displaced_capacity
            ),
            "capacity_status": (
                self.capacity_status
            ),
            "methodology": self.methodology,
        }


# ============================================================
# Coordinate validation
# ============================================================

def valid_coordinate_pair(
    longitude,
    latitude,
):
    if isinstance(longitude, bool):
        return False

    if isinstance(latitude, bool):
        return False

    if not isinstance(
        longitude,
        (int, float),
    ):
        return False

    if not isinstance(
        latitude,
        (int, float),
    ):
        return False

    if not math.isfinite(
        float(longitude)
    ):
        return False

    if not math.isfinite(
        float(latitude)
    ):
        return False

    if not (
        -180 <= longitude <= 180
    ):
        return False

    if not (
        -90 <= latitude <= 90
    ):
        return False

    return True


# ============================================================
# Haversine distance
# ============================================================

def coordinate_distance_meters(
    longitude_1,
    latitude_1,
    longitude_2,
    latitude_2,
):
    """
    Calculate great-circle distance between two
    longitude/latitude points.
    """

    if not valid_coordinate_pair(
        longitude_1,
        latitude_1,
    ):
        return 0.0

    if not valid_coordinate_pair(
        longitude_2,
        latitude_2,
    ):
        return 0.0

    lat_1 = math.radians(
        latitude_1
    )

    lat_2 = math.radians(
        latitude_2
    )

    delta_lat = math.radians(
        latitude_2 - latitude_1
    )

    delta_lon = math.radians(
        longitude_2 - longitude_1
    )

    a = (
        math.sin(
            delta_lat / 2.0
        ) ** 2
        + math.cos(lat_1)
        * math.cos(lat_2)
        * math.sin(
            delta_lon / 2.0
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
    """
    Convert a GeoJSON LineString or MultiLineString into
    a list of simple coordinate lines.

    Output:

    [
        [
            [longitude, latitude],
            [longitude, latitude],
            ...
        ],
        ...
    ]
    """

    if not geometry:
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
# Geometry length
# ============================================================

def calculate_geometry_length_meters(
    geometry,
):
    """
    Calculate the total centerline length represented by
    a GeoJSON LineString or MultiLineString.
    """

    lines = normalize_geometry_lines(
        geometry
    )

    total_length = 0.0

    for line in lines:
        if len(line) < 2:
            continue

        for index in range(
            len(line) - 1
        ):
            start = line[index]
            end = line[index + 1]

            if (
                not isinstance(
                    start,
                    (list, tuple),
                )
                or not isinstance(
                    end,
                    (list, tuple),
                )
            ):
                continue

            if (
                len(start) < 2
                or len(end) < 2
            ):
                continue

            start_longitude = start[0]
            start_latitude = start[1]

            end_longitude = end[0]
            end_latitude = end[1]

            distance = (
                coordinate_distance_meters(
                    start_longitude,
                    start_latitude,
                    end_longitude,
                    end_latitude,
                )
            )

            total_length += distance

    return round(
        total_length,
        2,
    )


# ============================================================
# Usable curb validation
# ============================================================

def validate_usable_length(
    segment_length_meters,
    usable_length_meters,
):
    """
    Validate externally supplied usable curb length.

    BanReady does not yet derive usable curb length
    automatically because complete curb-level exclusion
    data is not available.
    """

    if isinstance(
        usable_length_meters,
        bool,
    ):
        return False

    if not isinstance(
        usable_length_meters,
        (int, float),
    ):
        return False

    if not math.isfinite(
        float(
            usable_length_meters
        )
    ):
        return False

    if usable_length_meters < 0:
        return False

    if (
        usable_length_meters
        > segment_length_meters
    ):
        return False

    return True


# ============================================================
# Capacity estimate
# ============================================================

def estimate_capacity_from_length(
    usable_length_meters,
    assumed_space_length_meters,
):
    """
    Estimate how many vehicles can fit along a validated
    usable curb length.

    This is an ESTIMATE, not an official space count.
    """

    if isinstance(
        usable_length_meters,
        bool,
    ):
        raise ValueError(
            "Usable curb length must be numeric."
        )

    if not isinstance(
        usable_length_meters,
        (int, float),
    ):
        raise ValueError(
            "Usable curb length must be numeric."
        )

    if usable_length_meters < 0:
        raise ValueError(
            "Usable curb length cannot be negative."
        )

    if isinstance(
        assumed_space_length_meters,
        bool,
    ):
        raise ValueError(
            "Space-length assumption must be numeric."
        )

    if not isinstance(
        assumed_space_length_meters,
        (int, float),
    ):
        raise ValueError(
            "Space-length assumption must be numeric."
        )

    if assumed_space_length_meters <= 0:
        raise ValueError(
            "Space-length assumption must be positive."
        )

    return math.floor(
        usable_length_meters
        / assumed_space_length_meters
    )


# ============================================================
# Ban restriction
# ============================================================

def side_is_restricted(
    side,
    restricted_side,
):
    """
    Determine whether an ODD or EVEN side is eliminated
    under the modeled active winter-ban scenario.
    """

    side_value = str(
        side or ""
    ).strip().upper()

    restriction = str(
        restricted_side or ""
    ).strip().upper()

    if side_value not in {
        ODD,
        EVEN,
    }:
        return False

    if restriction == BOTH:
        return True

    if restriction == side_value:
        return True

    if restriction == NONE:
        return False

    return False


# ============================================================
# Ban capacity transformation
# ============================================================

def calculate_ban_capacity(
    normal_capacity,
    side,
    restricted_side,
):
    """
    Transform normal side capacity into the capacity
    remaining during the modeled active ban.

    If one side is restricted, that side contributes zero.
    """

    if normal_capacity < 0:
        raise ValueError(
            "Normal capacity cannot be negative."
        )

    if side_is_restricted(
        side,
        restricted_side,
    ):
        return 0

    return normal_capacity


# ============================================================
# Build side capacity
# ============================================================

def build_side_capacity(
    side,
    segment_length_meters,
    usable_length_meters,
    assumed_space_length_meters,
    restricted_side,
):
    if not validate_usable_length(
        segment_length_meters,
        usable_length_meters,
    ):
        raise ValueError(
            f"{side} usable curb length is invalid."
        )

    normal_capacity = (
        estimate_capacity_from_length(
            usable_length_meters,
            assumed_space_length_meters,
        )
    )

    restricted = (
        side_is_restricted(
            side,
            restricted_side,
        )
    )

    ban_capacity = (
        calculate_ban_capacity(
            normal_capacity,
            side,
            restricted_side,
        )
    )

    methodology = (
        "Capacity is estimated from validated usable curb "
        "length divided by a documented modeled curb length "
        "per parked vehicle. Winter-ban capacity is then "
        "calculated by setting the restricted side to zero "
        "for the modeled active-ban scenario. This is an "
        "ESTIMATED capacity and not an official marked-space "
        "count."
    )

    return StreetSideCapacity(
        side=side,

        segment_length_meters=(
            round(
                segment_length_meters,
                2,
            )
        ),

        usable_length_meters=(
            round(
                usable_length_meters,
                2,
            )
        ),

        assumed_space_length_meters=(
            assumed_space_length_meters
        ),

        normal_capacity=(
            normal_capacity
        ),

        ban_capacity=(
            ban_capacity
        ),

        normal_capacity_status=(
            ESTIMATED
        ),

        ban_capacity_status=(
            ESTIMATED
        ),

        restricted_during_ban=(
            restricted
        ),

        methodology=methodology,
    )


# ============================================================
# Calculate street supply
# ============================================================

def estimate_street_supply(
    street_name,
    segment_id,
    geometry,
    ban_type,
    restricted_side,
    odd_usable_length_meters,
    even_usable_length_meters,
    assumed_space_length_meters,
):
    """
    Estimate normal and active-ban curb capacity for one
    Worcester street segment.

    IMPORTANT:

    odd_usable_length_meters and even_usable_length_meters
    must be supplied from a separate curb-inventory or
    documented study process.

    This function deliberately does not claim that the full
    street centerline length is legal parking curb.
    """

    segment_length = (
        calculate_geometry_length_meters(
            geometry
        )
    )

    if segment_length <= 0:
        raise ValueError(
            "Street geometry has no usable length."
        )

    odd_result = (
        build_side_capacity(
            side=ODD,
            segment_length_meters=(
                segment_length
            ),
            usable_length_meters=(
                odd_usable_length_meters
            ),
            assumed_space_length_meters=(
                assumed_space_length_meters
            ),
            restricted_side=(
                restricted_side
            ),
        )
    )

    even_result = (
        build_side_capacity(
            side=EVEN,
            segment_length_meters=(
                segment_length
            ),
            usable_length_meters=(
                even_usable_length_meters
            ),
            assumed_space_length_meters=(
                assumed_space_length_meters
            ),
            restricted_side=(
                restricted_side
            ),
        )
    )

    total_normal_capacity = (
        odd_result.normal_capacity
        + even_result.normal_capacity
    )

    total_ban_capacity = (
        odd_result.ban_capacity
        + even_result.ban_capacity
    )

    displaced_capacity = max(
        0,
        total_normal_capacity
        - total_ban_capacity,
    )

    methodology = (
        "Street supply is modeled side by side. "
        "ODD and EVEN usable curb lengths are supplied by "
        "a documented curb-inventory process. Normal "
        "capacity is estimated independently for each side. "
        "The active winter-ban restriction is then applied "
        "to the side identified by Worcester's winter "
        "parking-ban data. Results remain ESTIMATED until "
        "validated against field observations or an "
        "authoritative curb-space inventory."
    )

    return StreetSupplyResult(
        street_name=street_name,

        segment_id=segment_id,

        ban_type=str(
            ban_type or UNKNOWN
        ).strip().upper(),

        restricted_side=str(
            restricted_side or UNKNOWN
        ).strip().upper(),

        segment_length_meters=(
            segment_length
        ),

        odd=odd_result,

        even=even_result,

        total_normal_capacity=(
            total_normal_capacity
        ),

        total_ban_capacity=(
            total_ban_capacity
        ),

        displaced_capacity=(
            displaced_capacity
        ),

        capacity_status=(
            ESTIMATED
        ),

        methodology=methodology,
    )
