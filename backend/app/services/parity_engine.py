import re
from dataclasses import dataclass
from typing import Optional

from backend.app.services.side_engine import (
    LEFT,
    RIGHT,
    determine_side_of_linestring,
)


ODD = "ODD"
EVEN = "EVEN"
UNSURE = "UNSURE"


@dataclass
class ParityMapping:
    left_parity: str
    right_parity: str

    left_odd_count: int
    left_even_count: int

    right_odd_count: int
    right_even_count: int

    usable_address_count: int
    confidence: str


def normalize_street_name(value: Optional[str]) -> str:
    if not value:
        return ""

    value = value.upper().strip()

    replacements = {
        " STREET": " ST",
        " AVENUE": " AVE",
        " ROAD": " RD",
        " LANE": " LN",
        " DRIVE": " DR",
        " BOULEVARD": " BLVD",
        " PLACE": " PL",
        " COURT": " CT",
        " TERRACE": " TER",
        " CIRCLE": " CIR",
        " HIGHWAY": " HWY",
        " PARKWAY": " PKWY",
    }

    for old, new in replacements.items():
        if value.endswith(old):
            value = value[:-len(old)] + new

    value = " ".join(value.split())

    return value


def get_numeric_address_number(value):
    if value is None:
        return None

    text = str(value).strip()

    match = re.search(r"\d+", text)

    if not match:
        return None

    try:
        return int(match.group())
    except ValueError:
        return None


def address_parity(address_number):
    if address_number is None:
        return None

    if address_number % 2 == 0:
        return EVEN

    return ODD


def determine_dominant_parity(
    odd_count,
    even_count,
    minimum_count=2,
    minimum_ratio=0.75,
):
    total = odd_count + even_count

    if total < minimum_count:
        return UNSURE

    if odd_count > even_count:
        ratio = odd_count / total

        if ratio >= minimum_ratio:
            return ODD

    if even_count > odd_count:
        ratio = even_count / total

        if ratio >= minimum_ratio:
            return EVEN

    return UNSURE


def infer_address_parity_mapping(
    street_name,
    street_coordinates,
    address_features,
    max_distance_meters=60.0,
):
    target_street = normalize_street_name(
        street_name
    )

    left_odd = 0
    left_even = 0

    right_odd = 0
    right_even = 0

    usable_addresses = 0

    seen_locations = set()

    for feature in address_features:
        properties = feature.get(
            "properties",
            {}
        )

        geometry = feature.get(
            "geometry",
            {}
        )

        if geometry.get("type") != "Point":
            continue

        address_street = normalize_street_name(
            properties.get("cmpltstreetname")
        )

        if address_street != target_street:
            continue

        address_number = get_numeric_address_number(
            properties.get("addrnum")
        )

        parity = address_parity(
            address_number
        )

        if parity is None:
            continue

        coordinates = geometry.get(
            "coordinates",
            []
        )

        if len(coordinates) < 2:
            continue

        longitude = coordinates[0]
        latitude = coordinates[1]

        # Prevent multiple apartment/unit records located at
        # the same address point from artificially increasing
        # the odd/even evidence.
        location_key = (
            round(latitude, 7),
            round(longitude, 7),
            address_number,
        )

        if location_key in seen_locations:
            continue

        seen_locations.add(
            location_key
        )

        side_result = determine_side_of_linestring(
            latitude,
            longitude,
            street_coordinates,
        )

        if (
            side_result.distance_meters
            > max_distance_meters
        ):
            continue

        geometric_side = (
            side_result.geometric_side
        )

        if geometric_side == LEFT:
            if parity == ODD:
                left_odd += 1

            elif parity == EVEN:
                left_even += 1

        elif geometric_side == RIGHT:
            if parity == ODD:
                right_odd += 1

            elif parity == EVEN:
                right_even += 1

        else:
            continue

        usable_addresses += 1

    left_parity = determine_dominant_parity(
        left_odd,
        left_even,
    )

    right_parity = determine_dominant_parity(
        right_odd,
        right_even,
    )

    if (
        left_parity != UNSURE
        and right_parity != UNSURE
        and left_parity != right_parity
    ):
        confidence = "HIGH"

    elif (
        left_parity != UNSURE
        or right_parity != UNSURE
    ):
        confidence = "PARTIAL"

    else:
        confidence = "LOW"

    return ParityMapping(
        left_parity=left_parity,
        right_parity=right_parity,

        left_odd_count=left_odd,
        left_even_count=left_even,

        right_odd_count=right_odd,
        right_even_count=right_even,

        usable_address_count=usable_addresses,
        confidence=confidence,
    )


def parity_mapping_from_record(record):
    """
    Rebuild a ParityMapping from a precomputed record in
    data/processed/segment_parity.json.
    """
    return ParityMapping(
        left_parity=record.get("left_parity", UNSURE),
        right_parity=record.get("right_parity", UNSURE),

        left_odd_count=record.get("left_odd_count", 0),
        left_even_count=record.get("left_even_count", 0),

        right_odd_count=record.get("right_odd_count", 0),
        right_even_count=record.get("right_even_count", 0),

        usable_address_count=record.get("usable_address_count", 0),
        confidence=record.get("confidence", "LOW"),
    )


def unknown_parity_mapping():
    """Parity mapping used when no address evidence is available."""
    return ParityMapping(
        left_parity=UNSURE,
        right_parity=UNSURE,
        left_odd_count=0,
        left_even_count=0,
        right_odd_count=0,
        right_even_count=0,
        usable_address_count=0,
        confidence="LOW",
    )


def resolve_parked_side(
    geometric_side,
    parity_mapping,
):
    if geometric_side == LEFT:
        return parity_mapping.left_parity

    if geometric_side == RIGHT:
        return parity_mapping.right_parity

    return UNSURE