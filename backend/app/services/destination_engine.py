import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


# ============================================================
# Configuration
# ============================================================

DESTINATION_FILE = Path(
    "data/processed/parking_destinations.json"
)

EARTH_RADIUS_METERS = 6371000.0


# ============================================================
# Destination result
# ============================================================

@dataclass
class DestinationOption:
    parking_id: str
    name: str
    destination_type: str

    latitude: float
    longitude: float

    address: Optional[str]

    distance_meters: float
    distance_km: float

    verification_status: str

    ban_available: Optional[bool]
    availability_status: str

    total_capacity: Optional[int]
    ban_capacity: Optional[int]

    overnight_allowed: Optional[bool]

    price_type: Optional[str]
    price_amount: Optional[float]

    source_name: Optional[str]
    source_url: Optional[str]

    notes: Optional[str]

    ban_availability_note: Optional[str] = None

    def to_dict(self):
        return asdict(self)


# ============================================================
# Destination search result
# ============================================================

@dataclass
class DestinationSearchResult:
    origin_latitude: float
    origin_longitude: float

    candidate_count: int
    returned_count: int

    options: list[DestinationOption]

    reason: str

    def to_dict(self):
        return {
            "origin_latitude": self.origin_latitude,
            "origin_longitude": self.origin_longitude,
            "candidate_count": self.candidate_count,
            "returned_count": self.returned_count,
            "options": [
                option.to_dict()
                for option in self.options
            ],
            "reason": self.reason,
        }


# ============================================================
# Load processed destination data
# ============================================================

def load_parking_destinations(
    data_file=DESTINATION_FILE,
):
    """
    Load BanReady's validated processed parking
    destination dataset.
    """

    if not data_file.exists():
        raise RuntimeError(
            "BanReady parking destination dataset "
            f"was not found: {data_file}"
        )

    try:
        with open(
            data_file,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            "BanReady parking destination dataset "
            "could not be read."
        ) from error

    destinations = data.get(
        "destinations",
        [],
    )

    if not destinations:
        raise RuntimeError(
            "BanReady parking destination dataset "
            "contains no destinations."
        )

    return destinations


# ============================================================
# Coordinate validation
# ============================================================

def valid_coordinate(
    latitude,
    longitude,
):
    """
    Validate a latitude/longitude pair.
    """

    if isinstance(latitude, bool):
        return False

    if isinstance(longitude, bool):
        return False

    if not isinstance(
        latitude,
        (int, float),
    ):
        return False

    if not isinstance(
        longitude,
        (int, float),
    ):
        return False

    if not math.isfinite(
        float(latitude)
    ):
        return False

    if not math.isfinite(
        float(longitude)
    ):
        return False

    if not (
        -90 <= latitude <= 90
    ):
        return False

    if not (
        -180 <= longitude <= 180
    ):
        return False

    return True


# ============================================================
# Haversine distance
# ============================================================

def haversine_distance_meters(
    latitude_1,
    longitude_1,
    latitude_2,
    longitude_2,
):
    """
    Calculate straight-line great-circle distance
    between two coordinates in meters.

    This is suitable for the Milestone 8 proximity
    ranking.

    It is not walking distance.

    Real street-network walking distance belongs to
    Milestone 14.
    """

    lat_1_rad = math.radians(
        latitude_1
    )

    lat_2_rad = math.radians(
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
        + math.cos(lat_1_rad)
        * math.cos(lat_2_rad)
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
# Destination eligibility
# ============================================================

def destination_is_eligible(
    destination,
    require_verified=True,
    require_ban_evidence=True,
):
    """
    Determine whether a parking destination is eligible
    for the current BanReady resident-facing search.

    Current MVP policy:

    verification_status must be VERIFIED

    ban_available must be True

    This intentionally excludes Worcester municipal lots
    whose winter-ban use has not yet been established.
    """

    if require_verified:
        verification_status = (
            destination.get(
                "verification_status"
            )
        )

        if verification_status != "VERIFIED":
            return False

    if require_ban_evidence:
        ban_available = destination.get(
            "ban_available"
        )

        if ban_available is not True:
            return False

    latitude = destination.get(
        "latitude"
    )

    longitude = destination.get(
        "longitude"
    )

    if not valid_coordinate(
        latitude,
        longitude,
    ):
        return False

    return True


# ============================================================
# Convert destination into search result
# ============================================================

def create_destination_option(
    destination,
    distance_meters,
):
    return DestinationOption(
        parking_id=destination[
            "parking_id"
        ],

        name=destination[
            "name"
        ],

        destination_type=destination[
            "destination_type"
        ],

        latitude=destination[
            "latitude"
        ],

        longitude=destination[
            "longitude"
        ],

        address=destination.get(
            "address"
        ),

        distance_meters=round(
            distance_meters,
            2,
        ),

        distance_km=round(
            distance_meters / 1000.0,
            3,
        ),

        verification_status=(
            destination.get(
                "verification_status",
                "UNVERIFIED",
            )
        ),

        ban_available=(
            destination.get(
                "ban_available"
            )
        ),

        availability_status=(
            destination.get(
                "availability_status",
                "UNKNOWN",
            )
        ),

        total_capacity=(
            destination.get(
                "total_capacity"
            )
        ),

        ban_capacity=(
            destination.get(
                "ban_capacity"
            )
        ),

        overnight_allowed=(
            destination.get(
                "overnight_allowed"
            )
        ),

        price_type=(
            destination.get(
                "price_type"
            )
        ),

        price_amount=(
            destination.get(
                "price_amount"
            )
        ),

        source_name=(
            destination.get(
                "source_name"
            )
        ),

        source_url=(
            destination.get(
                "source_url"
            )
        ),

        notes=destination.get(
            "notes"
        ),

        ban_availability_note=destination.get(
            "ban_availability_note"
        ),
    )


# ============================================================
# Find nearby destinations
# ============================================================

def find_nearby_destinations(
    latitude,
    longitude,
    destinations,
    limit=5,
    max_distance_meters=None,
    require_verified=True,
    require_ban_evidence=True,
):
    """
    Find nearby eligible BanReady parking destinations.

    Current ranking:
        straight-line distance ascending

    Current filtering:
        verified facilities
        historical winter-ban evidence

    Capacity is not used yet.

    Live availability is not assumed.
    """

    # --------------------------------------------------------
    # Validate origin
    # --------------------------------------------------------

    if not valid_coordinate(
        latitude,
        longitude,
    ):
        return DestinationSearchResult(
            origin_latitude=latitude,
            origin_longitude=longitude,
            candidate_count=0,
            returned_count=0,
            options=[],
            reason=(
                "The origin latitude or longitude "
                "is invalid."
            ),
        )

    # --------------------------------------------------------
    # Validate result limit
    # --------------------------------------------------------

    if not isinstance(
        limit,
        int,
    ):
        limit = 5

    if limit < 1:
        limit = 1

    # --------------------------------------------------------
    # Validate optional radius
    # --------------------------------------------------------

    if (
        max_distance_meters
        is not None
    ):
        if isinstance(
            max_distance_meters,
            bool,
        ):
            max_distance_meters = None

        elif not isinstance(
            max_distance_meters,
            (int, float),
        ):
            max_distance_meters = None

        elif (
            not math.isfinite(
                float(
                    max_distance_meters
                )
            )
        ):
            max_distance_meters = None

        elif max_distance_meters < 0:
            max_distance_meters = 0

    # --------------------------------------------------------
    # Search eligible destinations
    # --------------------------------------------------------

    candidates = []

    for destination in destinations:
        if not destination_is_eligible(
            destination,
            require_verified=(
                require_verified
            ),
            require_ban_evidence=(
                require_ban_evidence
            ),
        ):
            continue

        destination_latitude = (
            destination.get(
                "latitude"
            )
        )

        destination_longitude = (
            destination.get(
                "longitude"
            )
        )

        distance = (
            haversine_distance_meters(
                latitude,
                longitude,
                destination_latitude,
                destination_longitude,
            )
        )

        # ----------------------------------------------------
        # Optional search radius
        # ----------------------------------------------------

        if (
            max_distance_meters
            is not None
        ):
            if (
                distance
                > max_distance_meters
            ):
                continue

        candidates.append(
            create_destination_option(
                destination,
                distance,
            )
        )

    # --------------------------------------------------------
    # Sort nearest first
    # --------------------------------------------------------

    candidates.sort(
        key=lambda option: (
            option.distance_meters,
            option.name,
        )
    )

    candidate_count = len(
        candidates
    )

    options = candidates[
        :limit
    ]

    # --------------------------------------------------------
    # Search explanation
    # --------------------------------------------------------

    if options:
        reason = (
            "Nearby verified parking options "
            "were found and ranked by "
            "straight-line distance."
        )

    else:
        reason = (
            "No eligible verified parking "
            "destinations were found for "
            "the current filters."
        )

    # --------------------------------------------------------
    # Return search result
    # --------------------------------------------------------

    return DestinationSearchResult(
        origin_latitude=latitude,
        origin_longitude=longitude,
        candidate_count=candidate_count,
        returned_count=len(options),
        options=options,
        reason=reason,
    )


# ============================================================
# Current BanReady winter-ban search
# ============================================================

def find_winter_ban_parking_options(
    latitude,
    longitude,
    limit=5,
    max_distance_meters=None,
):
    """
    Load BanReady's processed destination dataset and
    return resident-facing winter-ban parking candidates.

    Current eligibility rules:

        verification_status == VERIFIED

        ban_available == True

    With the current Milestone 8 dataset, this means
    the five municipal garages with historical
    Worcester winter-ban evidence.

    Important:

    This function does not claim that a parking space
    is currently available.

    This function does not use parking capacity.

    This function does not calculate walking routes.

    Those are handled in later BanReady milestones.
    """

    destinations = (
        load_parking_destinations()
    )

    return find_nearby_destinations(
        latitude=latitude,
        longitude=longitude,
        destinations=destinations,
        limit=limit,
        max_distance_meters=(
            max_distance_meters
        ),
        require_verified=True,
        require_ban_evidence=True,
    )