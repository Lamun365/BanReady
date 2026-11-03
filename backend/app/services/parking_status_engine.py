from dataclasses import asdict, dataclass
from typing import Optional

from backend.app.services.ban_engine import (
    VERIFY_RULE,
    evaluate_parking_status,
)

from backend.app.services.parity_engine import (
    UNSURE,
    infer_address_parity_mapping,
    resolve_parked_side,
    unknown_parity_mapping,
)

from backend.app.services.side_engine import (
    LEFT,
    RIGHT,
    UNKNOWN,
    determine_side_of_linestring,
)


# ============================================================
# Result returned by the combined parking-status engine
# ============================================================

@dataclass
class ParkingStatusResult:
    street_name: str
    segment_id: Optional[int]

    ban_type: str
    ban_zone: str
    restricted_side: str

    geometric_side: str
    parked_side: str

    left_parity: str
    right_parity: str
    parity_confidence: str

    distance_to_street_meters: float

    status: str
    reason: str

    def to_dict(self):
        return asdict(self)


# ============================================================
# Safe string helper
# ============================================================

def normalize_text(value) -> str:
    if value is None:
        return ""

    return str(value).strip()


# ============================================================
# Create VERIFY_RULE result
# ============================================================

def create_verify_result(
    street_name,
    segment_id,
    ban_type,
    ban_zone,
    restricted_side,
    geometric_side,
    parked_side,
    left_parity,
    right_parity,
    parity_confidence,
    distance_to_street_meters,
    reason,
):
    return ParkingStatusResult(
        street_name=street_name,
        segment_id=segment_id,
        ban_type=ban_type,
        ban_zone=ban_zone,
        restricted_side=restricted_side,
        geometric_side=geometric_side,
        parked_side=parked_side,
        left_parity=left_parity,
        right_parity=right_parity,
        parity_confidence=parity_confidence,
        distance_to_street_meters=distance_to_street_meters,
        status=VERIFY_RULE,
        reason=reason,
    )


# ============================================================
# Main parking status engine
# ============================================================

def evaluate_vehicle_parking_status(
    latitude,
    longitude,
    street_feature,
    address_features,
    declared_ban_active=False,
    snow_emergency_active=False,
    permanent_time_restriction_active=False,
    max_car_distance_meters=50.0,
    precomputed_parity=None,
):
    """
    Evaluate the winter parking status of a vehicle after
    a Worcester parking-ban street feature has been matched.

    Pipeline:

        car coordinate
            ↓
        street geometry
            ↓
        geometric LEFT / RIGHT
            ↓
        Worcester address-point parity
            ↓
        ODD / EVEN / UNSURE
            ↓
        BanReady ban engine
            ↓
        final parking status

    The function deliberately returns VERIFY_RULE when a
    reliable side/parity decision cannot be made.
    """

    # --------------------------------------------------------
    # Validate street feature
    # --------------------------------------------------------

    if not street_feature:
        return create_verify_result(
            street_name="",
            segment_id=None,
            ban_type="",
            ban_zone="",
            restricted_side="",
            geometric_side=UNKNOWN,
            parked_side=UNSURE,
            left_parity=UNSURE,
            right_parity=UNSURE,
            parity_confidence="LOW",
            distance_to_street_meters=float("inf"),
            reason=(
                "BanReady does not have a matched Worcester "
                "street segment for this location."
            ),
        )

    properties = street_feature.get(
        "properties",
        {},
    )

    geometry = street_feature.get(
        "geometry",
        {},
    )

    street_name = normalize_text(
        properties.get("street_name")
    )

    segment_id = properties.get(
        "segment_id"
    )

    ban_type = normalize_text(
        properties.get("ban_type")
    ).upper()

    ban_zone = normalize_text(
        properties.get("ban_zone")
    ).upper()

    restricted_side = normalize_text(
        properties.get("no_parking_side")
    ).upper()

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    # --------------------------------------------------------
    # Validate geometry
    # --------------------------------------------------------

    if not coordinates:
        return create_verify_result(
            street_name=street_name,
            segment_id=segment_id,
            ban_type=ban_type,
            ban_zone=ban_zone,
            restricted_side=restricted_side,
            geometric_side=UNKNOWN,
            parked_side=UNSURE,
            left_parity=UNSURE,
            right_parity=UNSURE,
            parity_confidence="LOW",
            distance_to_street_meters=float("inf"),
            reason=(
                "The matched Worcester street segment does "
                "not contain usable geometry."
            ),
        )

    # --------------------------------------------------------
    # Determine geometric side of street
    # --------------------------------------------------------

    side_result = determine_side_of_linestring(
        latitude,
        longitude,
        coordinates,
    )

    geometric_side = (
        side_result.geometric_side
    )

    street_distance = (
        side_result.distance_meters
    )

    # --------------------------------------------------------
    # Reject a car that is too far from the street
    # --------------------------------------------------------

    if street_distance > max_car_distance_meters:
        return create_verify_result(
            street_name=street_name,
            segment_id=segment_id,
            ban_type=ban_type,
            ban_zone=ban_zone,
            restricted_side=restricted_side,
            geometric_side=geometric_side,
            parked_side=UNSURE,
            left_parity=UNSURE,
            right_parity=UNSURE,
            parity_confidence="LOW",
            distance_to_street_meters=street_distance,
            reason=(
                "The selected vehicle location is too far "
                "from the matched Worcester street segment."
            ),
        )

    # --------------------------------------------------------
    # If BOTH sides are prohibited, address parity is not
    # necessary to determine that the active rule affects
    # either side.
    #
    # However, we still run parity inference below when
    # possible because the result is useful diagnostic data.
    # --------------------------------------------------------

    # --------------------------------------------------------
    # Infer LEFT / RIGHT address parity
    # --------------------------------------------------------

    # Use the precomputed ODD/EVEN mapping for this segment
    # when available (data/processed/segment_parity.json).
    # Otherwise fall back to the full address-point search.

    if precomputed_parity is not None:
        parity_mapping = precomputed_parity

    elif address_features:
        parity_mapping = infer_address_parity_mapping(
            street_name=street_name,
            street_coordinates=coordinates,
            address_features=address_features,
        )

    else:
        parity_mapping = unknown_parity_mapping()

    # --------------------------------------------------------
    # Resolve geometric LEFT / RIGHT into ODD / EVEN
    # --------------------------------------------------------

    parked_side = resolve_parked_side(
        geometric_side,
        parity_mapping,
    )

    # --------------------------------------------------------
    # Special handling when BOTH sides are restricted
    #
    # The ban engine does not need ODD / EVEN to determine
    # the result when the GIS explicitly says BOTH.
    # --------------------------------------------------------

    if restricted_side == "BOTH":
        ban_result = evaluate_parking_status(
            ban_type=ban_type,
            no_parking_side=restricted_side,
            parked_side=parked_side,
            declared_ban_active=declared_ban_active,
            snow_emergency_active=snow_emergency_active,
            permanent_time_restriction_active=(
                permanent_time_restriction_active
            ),
        )

        return ParkingStatusResult(
            street_name=street_name,
            segment_id=segment_id,
            ban_type=ban_type,
            ban_zone=ban_zone,
            restricted_side=restricted_side,
            geometric_side=geometric_side,
            parked_side=parked_side,
            left_parity=parity_mapping.left_parity,
            right_parity=parity_mapping.right_parity,
            parity_confidence=parity_mapping.confidence,
            distance_to_street_meters=street_distance,
            status=ban_result.status,
            reason=ban_result.reason,
        )

    # --------------------------------------------------------
    # NON-APPLICABLE and NONE do not require knowing
    # whether the car is ODD or EVEN.
    # --------------------------------------------------------

    if (
        ban_type == "NON-APPLICABLE"
        or restricted_side == "NONE"
        or ban_type
        == "STATE OWNED - NO WORCESTER WINTER PARKING BAN"
    ):
        ban_result = evaluate_parking_status(
            ban_type=ban_type,
            no_parking_side=restricted_side,
            parked_side=parked_side,
            declared_ban_active=declared_ban_active,
            snow_emergency_active=snow_emergency_active,
            permanent_time_restriction_active=(
                permanent_time_restriction_active
            ),
        )

        return ParkingStatusResult(
            street_name=street_name,
            segment_id=segment_id,
            ban_type=ban_type,
            ban_zone=ban_zone,
            restricted_side=restricted_side,
            geometric_side=geometric_side,
            parked_side=parked_side,
            left_parity=parity_mapping.left_parity,
            right_parity=parity_mapping.right_parity,
            parity_confidence=parity_mapping.confidence,
            distance_to_street_meters=street_distance,
            status=ban_result.status,
            reason=ban_result.reason,
        )

    # --------------------------------------------------------
    # For ODD / EVEN restrictions, parity must be known.
    # --------------------------------------------------------

    if parked_side == UNSURE:
        return create_verify_result(
            street_name=street_name,
            segment_id=segment_id,
            ban_type=ban_type,
            ban_zone=ban_zone,
            restricted_side=restricted_side,
            geometric_side=geometric_side,
            parked_side=UNSURE,
            left_parity=parity_mapping.left_parity,
            right_parity=parity_mapping.right_parity,
            parity_confidence=parity_mapping.confidence,
            distance_to_street_meters=street_distance,
            reason=(
                "BanReady could determine the vehicle's "
                "geometric side of the street but could not "
                "reliably map that side to an ODD or EVEN "
                "address-numbered side."
            ),
        )

    # --------------------------------------------------------
    # Evaluate Worcester winter parking rule
    # --------------------------------------------------------

    ban_result = evaluate_parking_status(
        ban_type=ban_type,
        no_parking_side=restricted_side,
        parked_side=parked_side,
        declared_ban_active=declared_ban_active,
        snow_emergency_active=snow_emergency_active,
        permanent_time_restriction_active=(
            permanent_time_restriction_active
        ),
    )

    # --------------------------------------------------------
    # Final combined result
    # --------------------------------------------------------

    return ParkingStatusResult(
        street_name=street_name,
        segment_id=segment_id,
        ban_type=ban_type,
        ban_zone=ban_zone,
        restricted_side=restricted_side,
        geometric_side=geometric_side,
        parked_side=parked_side,
        left_parity=parity_mapping.left_parity,
        right_parity=parity_mapping.right_parity,
        parity_confidence=parity_mapping.confidence,
        distance_to_street_meters=street_distance,
        status=ban_result.status,
        reason=ban_result.reason,
    )