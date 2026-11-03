import json
import math
import sys
from collections import Counter
from pathlib import Path


# ============================================================
# Project setup
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.models.parking_destination import (
    MUNICIPAL_GARAGE,
    MUNICIPAL_LOT,
    PARTNER_LOT,
    STREET,
    VERIFIED,
    UNVERIFIED,
    AVAILABLE,
    UNAVAILABLE,
    UNKNOWN,
)


# ============================================================
# Configuration
# ============================================================

DATA_FILE = Path(
    "data/processed/parking_destinations.json"
)


EXPECTED_DESTINATION_COUNT = 12
EXPECTED_GARAGE_COUNT = 5
EXPECTED_LOT_COUNT = 7
EXPECTED_HISTORICAL_BAN_COUNT = 5


ALLOWED_DESTINATION_TYPES = {
    MUNICIPAL_GARAGE,
    MUNICIPAL_LOT,
    STREET,
    PARTNER_LOT,
}


ALLOWED_VERIFICATION_STATES = {
    VERIFIED,
    UNVERIFIED,
}


ALLOWED_AVAILABILITY_STATES = {
    AVAILABLE,
    UNAVAILABLE,
    UNKNOWN,
}


# ============================================================
# Validation helpers
# ============================================================

def is_number(value):
    """
    Return True for usable numeric values while excluding
    booleans, NaN and infinity.
    """

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


def is_non_empty_string(value):
    return (
        isinstance(value, str)
        and value.strip() != ""
    )


def add_error(
    errors,
    parking_id,
    message,
):
    errors.append(
        f"{parking_id}: {message}"
    )


def add_warning(
    warnings,
    parking_id,
    message,
):
    warnings.append(
        f"{parking_id}: {message}"
    )


# ============================================================
# Validate one destination
# ============================================================

def validate_destination(
    destination,
    index,
    errors,
    warnings,
):
    parking_id = destination.get(
        "parking_id"
    )

    if not is_non_empty_string(
        parking_id
    ):
        parking_id = (
            f"record-{index}"
        )

        add_error(
            errors,
            parking_id,
            "parking_id is missing or empty.",
        )

    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    name = destination.get(
        "name"
    )

    if not is_non_empty_string(
        name
    ):
        add_error(
            errors,
            parking_id,
            "name is missing or empty.",
        )

    # --------------------------------------------------------
    # Destination type
    # --------------------------------------------------------

    destination_type = destination.get(
        "destination_type"
    )

    if (
        destination_type
        not in ALLOWED_DESTINATION_TYPES
    ):
        add_error(
            errors,
            parking_id,
            (
                "destination_type is invalid: "
                f"{destination_type}"
            ),
        )

    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    latitude = destination.get(
        "latitude"
    )

    longitude = destination.get(
        "longitude"
    )

    if not is_number(latitude):
        add_error(
            errors,
            parking_id,
            "latitude is missing or invalid.",
        )

    elif not (
        -90 <= latitude <= 90
    ):
        add_error(
            errors,
            parking_id,
            (
                "latitude is outside the "
                "valid -90 to 90 range."
            ),
        )

    if not is_number(longitude):
        add_error(
            errors,
            parking_id,
            "longitude is missing or invalid.",
        )

    elif not (
        -180 <= longitude <= 180
    ):
        add_error(
            errors,
            parking_id,
            (
                "longitude is outside the "
                "valid -180 to 180 range."
            ),
        )

    # --------------------------------------------------------
    # Worcester-area sanity check
    #
    # This is not a legal city-boundary test.
    # It only catches obviously incorrect coordinates.
    # --------------------------------------------------------

    if (
        is_number(latitude)
        and is_number(longitude)
    ):
        if not (
            42.0 <= latitude <= 42.5
            and -72.1 <= longitude <= -71.5
        ):
            add_warning(
                warnings,
                parking_id,
                (
                    "coordinates appear far outside "
                    "the expected Worcester area."
                ),
            )

    # --------------------------------------------------------
    # Address
    # --------------------------------------------------------

    address = destination.get(
        "address"
    )

    if not is_non_empty_string(
        address
    ):
        add_warning(
            warnings,
            parking_id,
            "address is missing.",
        )

    # --------------------------------------------------------
    # Verification
    # --------------------------------------------------------

    verification_status = (
        destination.get(
            "verification_status"
        )
    )

    if (
        verification_status
        not in ALLOWED_VERIFICATION_STATES
    ):
        add_error(
            errors,
            parking_id,
            (
                "verification_status is invalid: "
                f"{verification_status}"
            ),
        )

    source_name = destination.get(
        "source_name"
    )

    source_url = destination.get(
        "source_url"
    )

    if (
        verification_status == VERIFIED
        and not is_non_empty_string(
            source_name
        )
    ):
        add_error(
            errors,
            parking_id,
            (
                "verified destination does not "
                "have a source_name."
            ),
        )

    if (
        verification_status == VERIFIED
        and not is_non_empty_string(
            source_url
        )
    ):
        add_warning(
            warnings,
            parking_id,
            (
                "verified destination does not "
                "have a source_url."
            ),
        )

    # --------------------------------------------------------
    # Ban availability
    # --------------------------------------------------------

    ban_available = destination.get(
        "ban_available"
    )

    if ban_available not in {
        True,
        False,
        None,
    }:
        add_error(
            errors,
            parking_id,
            (
                "ban_available must be "
                "true, false, or null."
            ),
        )

    # --------------------------------------------------------
    # Live availability
    # --------------------------------------------------------

    availability_status = (
        destination.get(
            "availability_status"
        )
    )

    if (
        availability_status
        not in ALLOWED_AVAILABILITY_STATES
    ):
        add_error(
            errors,
            parking_id,
            (
                "availability_status is invalid: "
                f"{availability_status}"
            ),
        )

    # --------------------------------------------------------
    # Capacity
    # --------------------------------------------------------

    total_capacity = destination.get(
        "total_capacity"
    )

    ban_capacity = destination.get(
        "ban_capacity"
    )

    if total_capacity is not None:
        if (
            not isinstance(
                total_capacity,
                int,
            )
            or isinstance(
                total_capacity,
                bool,
            )
        ):
            add_error(
                errors,
                parking_id,
                (
                    "total_capacity must be "
                    "an integer or null."
                ),
            )

        elif total_capacity < 0:
            add_error(
                errors,
                parking_id,
                (
                    "total_capacity cannot "
                    "be negative."
                ),
            )

    if ban_capacity is not None:
        if (
            not isinstance(
                ban_capacity,
                int,
            )
            or isinstance(
                ban_capacity,
                bool,
            )
        ):
            add_error(
                errors,
                parking_id,
                (
                    "ban_capacity must be "
                    "an integer or null."
                ),
            )

        elif ban_capacity < 0:
            add_error(
                errors,
                parking_id,
                (
                    "ban_capacity cannot "
                    "be negative."
                ),
            )

    if (
        isinstance(total_capacity, int)
        and not isinstance(
            total_capacity,
            bool,
        )
        and isinstance(
            ban_capacity,
            int,
        )
        and not isinstance(
            ban_capacity,
            bool,
        )
        and ban_capacity > total_capacity
    ):
        add_error(
            errors,
            parking_id,
            (
                "ban_capacity cannot exceed "
                "total_capacity."
            ),
        )

    # --------------------------------------------------------
    # Milestone 8 safety check
    #
    # We intentionally have not populated capacities yet.
    # --------------------------------------------------------

    if total_capacity is not None:
        add_warning(
            warnings,
            parking_id,
            (
                "total_capacity is populated. "
                "Confirm that the value has a "
                "verified source before Milestone 9."
            ),
        )

    if ban_capacity is not None:
        add_warning(
            warnings,
            parking_id,
            (
                "ban_capacity is populated. "
                "Confirm that the value has a "
                "verified source before Milestone 9."
            ),
        )

    # --------------------------------------------------------
    # Operating fields
    # --------------------------------------------------------

    overnight_allowed = (
        destination.get(
            "overnight_allowed"
        )
    )

    if overnight_allowed not in {
        True,
        False,
        None,
    }:
        add_error(
            errors,
            parking_id,
            (
                "overnight_allowed must be "
                "true, false, or null."
            ),
        )

    # --------------------------------------------------------
    # Price
    # --------------------------------------------------------

    price_amount = destination.get(
        "price_amount"
    )

    if price_amount is not None:
        if not is_number(
            price_amount
        ):
            add_error(
                errors,
                parking_id,
                (
                    "price_amount must be "
                    "numeric or null."
                ),
            )

        elif price_amount < 0:
            add_error(
                errors,
                parking_id,
                (
                    "price_amount cannot "
                    "be negative."
                ),
            )


# ============================================================
# Main validator
# ============================================================

def main():
    print()
    print(
        "BanReady Parking Destination Validator"
    )
    print(
        "======================================"
    )
    print()

    # --------------------------------------------------------
    # File
    # --------------------------------------------------------

    if not DATA_FILE.exists():
        print(
            "ERROR: Processed destination "
            "dataset was not found."
        )

        print()
        print("Expected file:")
        print(DATA_FILE)

        return

    # --------------------------------------------------------
    # Load JSON
    # --------------------------------------------------------

    try:
        with open(
            DATA_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError:
        print(
            "ERROR: parking_destinations.json "
            "could not be read."
        )

        return

    destinations = data.get(
        "destinations",
        [],
    )

    declared_count = data.get(
        "destination_count"
    )

    print(
        f"Dataset name: "
        f"{data.get('dataset_name')}"
    )

    print(
        f"City:         "
        f"{data.get('city')}"
    )

    print(
        f"State:        "
        f"{data.get('state')}"
    )

    print()

    print(
        f"Declared destination count: "
        f"{declared_count}"
    )

    print(
        f"Actual destination count:   "
        f"{len(destinations)}"
    )

    print()

    if not destinations:
        print(
            "ERROR: No parking destinations "
            "were found."
        )

        return

    errors = []
    warnings = []

    # --------------------------------------------------------
    # Validate individual records
    # --------------------------------------------------------

    for index, destination in enumerate(
        destinations,
        start=1,
    ):
        validate_destination(
            destination=destination,
            index=index,
            errors=errors,
            warnings=warnings,
        )

    # --------------------------------------------------------
    # Duplicate IDs
    # --------------------------------------------------------

    parking_ids = [
        destination.get(
            "parking_id"
        )
        for destination in destinations
    ]

    id_counts = Counter(
        parking_ids
    )

    duplicate_ids = [
        parking_id
        for parking_id, count
        in id_counts.items()
        if (
            parking_id is not None
            and count > 1
        )
    ]

    for parking_id in duplicate_ids:
        add_error(
            errors,
            parking_id,
            "duplicate parking_id found.",
        )

    # --------------------------------------------------------
    # Duplicate names + addresses
    # --------------------------------------------------------

    identity_keys = []

    for destination in destinations:
        name = str(
            destination.get("name")
            or ""
        ).strip().upper()

        address = str(
            destination.get("address")
            or ""
        ).strip().upper()

        identity_keys.append(
            (
                name,
                address,
            )
        )

    identity_counts = Counter(
        identity_keys
    )

    duplicate_identities = [
        identity
        for identity, count
        in identity_counts.items()
        if (
            identity != ("", "")
            and count > 1
        )
    ]

    for name, address in duplicate_identities:
        errors.append(
            (
                "Duplicate destination identity: "
                f"{name} | {address}"
            )
        )

    # --------------------------------------------------------
    # Counts
    # --------------------------------------------------------

    type_counts = Counter(
        destination.get(
            "destination_type"
        )
        for destination in destinations
    )

    garage_count = type_counts[
        MUNICIPAL_GARAGE
    ]

    lot_count = type_counts[
        MUNICIPAL_LOT
    ]

    historical_ban_count = sum(
        1
        for destination in destinations
        if (
            destination.get(
                "ban_available"
            )
            is True
        )
    )

    verified_count = sum(
        1
        for destination in destinations
        if (
            destination.get(
                "verification_status"
            )
            == VERIFIED
        )
    )

    unknown_live_count = sum(
        1
        for destination in destinations
        if (
            destination.get(
                "availability_status"
            )
            == UNKNOWN
        )
    )

    # --------------------------------------------------------
    # Dataset-level consistency checks
    # --------------------------------------------------------

    if (
        declared_count
        != len(destinations)
    ):
        errors.append(
            (
                "destination_count does not "
                "match actual records."
            )
        )

    if (
        len(destinations)
        != EXPECTED_DESTINATION_COUNT
    ):
        errors.append(
            (
                "Expected "
                f"{EXPECTED_DESTINATION_COUNT} "
                "destinations, found "
                f"{len(destinations)}."
            )
        )

    if (
        garage_count
        != EXPECTED_GARAGE_COUNT
    ):
        errors.append(
            (
                "Expected "
                f"{EXPECTED_GARAGE_COUNT} "
                "municipal garages, found "
                f"{garage_count}."
            )
        )

    if (
        lot_count
        != EXPECTED_LOT_COUNT
    ):
        errors.append(
            (
                "Expected "
                f"{EXPECTED_LOT_COUNT} "
                "municipal lots, found "
                f"{lot_count}."
            )
        )

    if (
        historical_ban_count
        != EXPECTED_HISTORICAL_BAN_COUNT
    ):
        errors.append(
            (
                "Expected "
                f"{EXPECTED_HISTORICAL_BAN_COUNT} "
                "destinations with historical "
                "ban evidence, found "
                f"{historical_ban_count}."
            )
        )

    # --------------------------------------------------------
    # No invented capacity check
    # --------------------------------------------------------

    populated_total_capacity = sum(
        1
        for destination in destinations
        if (
            destination.get(
                "total_capacity"
            )
            is not None
        )
    )

    populated_ban_capacity = sum(
        1
        for destination in destinations
        if (
            destination.get(
                "ban_capacity"
            )
            is not None
        )
    )

    if populated_total_capacity != 0:
        errors.append(
            (
                "Milestone 8 expects total_capacity "
                "to remain null for all records."
            )
        )

    if populated_ban_capacity != 0:
        errors.append(
            (
                "Milestone 8 expects ban_capacity "
                "to remain null for all records."
            )
        )

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("DATASET SUMMARY")
    print("===============")
    print()

    print(
        f"Destinations:             "
        f"{len(destinations)}"
    )

    print(
        f"Municipal garages:        "
        f"{garage_count}"
    )

    print(
        f"Municipal lots:           "
        f"{lot_count}"
    )

    print(
        f"Verified facilities:      "
        f"{verified_count}"
    )

    print(
        f"Historical ban evidence:  "
        f"{historical_ban_count}"
    )

    print(
        f"Live availability UNKNOWN:"
        f" {unknown_live_count}"
    )

    print(
        f"Total capacities entered: "
        f"{populated_total_capacity}"
    )

    print(
        f"Ban capacities entered:   "
        f"{populated_ban_capacity}"
    )

    print()

    # --------------------------------------------------------
    # Validation errors
    # --------------------------------------------------------

    print("ERRORS")
    print("======")
    print()

    if errors:
        for number, error in enumerate(
            errors,
            start=1,
        ):
            print(
                f"{number}. {error}"
            )
    else:
        print("None")

    print()

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    print("WARNINGS")
    print("========")
    print()

    if warnings:
        for number, warning in enumerate(
            warnings,
            start=1,
        ):
            print(
                f"{number}. {warning}"
            )
    else:
        print("None")

    print()

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("VALIDATION RESULT")
    print("=================")
    print()

    if errors:
        print("FAILED")
        print()
        print(
            "Do not use this destination dataset "
            "in destination_engine.py until all "
            "validation errors are resolved."
        )

        return

    print("PASSED")
    print()

    print(
        "BanReady parking destinations are "
        "ready for the destination engine."
    )


if __name__ == "__main__":
    main()