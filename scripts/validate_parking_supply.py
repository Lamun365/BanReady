import json
import math
import sys
from collections import Counter
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
# BanReady imports
# ============================================================

from backend.app.models.parking_supply import (
    GARAGE,
    LOT,
    ESTIMATED,
    UNKNOWN,
    VERIFIED,
)


# ============================================================
# Configuration
# ============================================================

DATA_FILE = Path(
    "data/processed/parking_supply.json"
)


EXPECTED_SUPPLY_COUNT = 12

EXPECTED_GARAGE_COUNT = 5

EXPECTED_LOT_COUNT = 7

EXPECTED_VERIFIED_TOTAL_COUNT = 8

EXPECTED_UNKNOWN_TOTAL_COUNT = 4

EXPECTED_KNOWN_BAN_COUNT = 0

EXPECTED_UNKNOWN_BAN_COUNT = 12

EXPECTED_VERIFIED_GARAGE_CAPACITY = 500

EXPECTED_VERIFIED_LOT_CAPACITY = 673

EXPECTED_VERIFIED_NORMAL_CAPACITY = 1173


ALLOWED_SUPPLY_TYPES = {
    GARAGE,
    LOT,
    "STREET_SEGMENT",
    "PARTNER_LOT",
}


ALLOWED_EVIDENCE_STATES = {
    VERIFIED,
    ESTIMATED,
    UNKNOWN,
}


# ============================================================
# Helpers
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


def is_positive_integer(value):
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


def is_non_empty_string(value):
    return (
        isinstance(value, str)
        and value.strip() != ""
    )


def add_error(
    errors,
    supply_id,
    message,
):
    errors.append(
        f"{supply_id}: {message}"
    )


def add_warning(
    warnings,
    supply_id,
    message,
):
    warnings.append(
        f"{supply_id}: {message}"
    )


# ============================================================
# Validate one supply record
# ============================================================

def validate_supply_record(
    supply,
    index,
    errors,
    warnings,
):
    supply_id = supply.get(
        "supply_id"
    )

    if not is_non_empty_string(
        supply_id
    ):
        supply_id = (
            f"record-{index}"
        )

        add_error(
            errors,
            supply_id,
            "supply_id is missing or empty.",
        )


    # --------------------------------------------------------
    # Name
    # --------------------------------------------------------

    name = supply.get(
        "name"
    )

    if not is_non_empty_string(
        name
    ):
        add_error(
            errors,
            supply_id,
            "name is missing or empty.",
        )


    # --------------------------------------------------------
    # Supply type
    # --------------------------------------------------------

    supply_type = supply.get(
        "supply_type"
    )

    if (
        supply_type
        not in ALLOWED_SUPPLY_TYPES
    ):
        add_error(
            errors,
            supply_id,
            (
                "invalid supply_type: "
                f"{supply_type}"
            ),
        )


    # --------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------

    latitude = supply.get(
        "latitude"
    )

    longitude = supply.get(
        "longitude"
    )

    if not is_number(
        latitude
    ):
        add_error(
            errors,
            supply_id,
            "latitude is invalid.",
        )

    elif not (
        -90 <= latitude <= 90
    ):
        add_error(
            errors,
            supply_id,
            "latitude is outside valid range.",
        )

    if not is_number(
        longitude
    ):
        add_error(
            errors,
            supply_id,
            "longitude is invalid.",
        )

    elif not (
        -180 <= longitude <= 180
    ):
        add_error(
            errors,
            supply_id,
            "longitude is outside valid range.",
        )


    # --------------------------------------------------------
    # Worcester-area sanity check
    #
    # This is not a municipal boundary test.
    # It only catches obviously incorrect coordinates.
    # --------------------------------------------------------

    if (
        is_number(latitude)
        and is_number(longitude)
    ):
        if not (
            42.0 <= latitude <= 42.5
            and
            -72.1 <= longitude <= -71.5
        ):
            add_warning(
                warnings,
                supply_id,
                (
                    "coordinates appear outside "
                    "the expected Worcester area."
                ),
            )


    # --------------------------------------------------------
    # Address
    # --------------------------------------------------------

    address = supply.get(
        "address"
    )

    if not is_non_empty_string(
        address
    ):
        add_warning(
            warnings,
            supply_id,
            "address is missing.",
        )


    # --------------------------------------------------------
    # Total capacity evidence
    # --------------------------------------------------------

    total_capacity = supply.get(
        "total_capacity"
    )

    total_status = supply.get(
        "total_capacity_status"
    )

    if (
        total_status
        not in ALLOWED_EVIDENCE_STATES
    ):
        add_error(
            errors,
            supply_id,
            (
                "invalid total_capacity_status: "
                f"{total_status}"
            ),
        )

    if total_status == VERIFIED:
        if not is_positive_integer(
            total_capacity
        ):
            add_error(
                errors,
                supply_id,
                (
                    "VERIFIED total capacity "
                    "requires a positive integer."
                ),
            )

    elif total_status == ESTIMATED:
        if not is_positive_integer(
            total_capacity
        ):
            add_error(
                errors,
                supply_id,
                (
                    "ESTIMATED total capacity "
                    "requires a positive integer."
                ),
            )

        methodology = supply.get(
            "methodology"
        )

        if not is_non_empty_string(
            methodology
        ):
            add_error(
                errors,
                supply_id,
                (
                    "ESTIMATED total capacity "
                    "requires methodology."
                ),
            )

    elif total_status == UNKNOWN:
        if total_capacity is not None:
            add_error(
                errors,
                supply_id,
                (
                    "UNKNOWN total capacity "
                    "must have value null."
                ),
            )


    # --------------------------------------------------------
    # Ban capacity evidence
    # --------------------------------------------------------

    ban_capacity = supply.get(
        "ban_capacity"
    )

    ban_status = supply.get(
        "ban_capacity_status"
    )

    if (
        ban_status
        not in ALLOWED_EVIDENCE_STATES
    ):
        add_error(
            errors,
            supply_id,
            (
                "invalid ban_capacity_status: "
                f"{ban_status}"
            ),
        )

    if ban_status == VERIFIED:
        if not is_positive_integer(
            ban_capacity
        ):
            add_error(
                errors,
                supply_id,
                (
                    "VERIFIED ban capacity "
                    "requires a positive integer."
                ),
            )

    elif ban_status == ESTIMATED:
        if not is_positive_integer(
            ban_capacity
        ):
            add_error(
                errors,
                supply_id,
                (
                    "ESTIMATED ban capacity "
                    "requires a positive integer."
                ),
            )

        methodology = supply.get(
            "methodology"
        )

        if not is_non_empty_string(
            methodology
        ):
            add_error(
                errors,
                supply_id,
                (
                    "ESTIMATED ban capacity "
                    "requires methodology."
                ),
            )

    elif ban_status == UNKNOWN:
        if ban_capacity is not None:
            add_error(
                errors,
                supply_id,
                (
                    "UNKNOWN ban capacity "
                    "must have value null."
                ),
            )


    # --------------------------------------------------------
    # Capacity relationship
    # --------------------------------------------------------

    if (
        total_capacity is not None
        and ban_capacity is not None
    ):
        if (
            ban_capacity
            > total_capacity
        ):
            add_error(
                errors,
                supply_id,
                (
                    "ban_capacity cannot exceed "
                    "total_capacity."
                ),
            )


    # --------------------------------------------------------
    # Source evidence
    # --------------------------------------------------------

    source_name = supply.get(
        "source_name"
    )

    source_url = supply.get(
        "source_url"
    )

    if total_status == VERIFIED:
        if not is_non_empty_string(
            source_name
        ):
            add_error(
                errors,
                supply_id,
                (
                    "VERIFIED total capacity "
                    "requires source_name."
                ),
            )

        if not is_non_empty_string(
            source_url
        ):
            add_error(
                errors,
                supply_id,
                (
                    "VERIFIED total capacity "
                    "requires source_url."
                ),
            )


    # --------------------------------------------------------
    # URL sanity check
    # --------------------------------------------------------

    if is_non_empty_string(
        source_url
    ):
        if not (
            source_url.startswith(
                "https://"
            )
            or source_url.startswith(
                "http://"
            )
        ):
            add_error(
                errors,
                supply_id,
                (
                    "source_url is not a plain "
                    "HTTP/HTTPS URL."
                ),
            )


    # --------------------------------------------------------
    # Current facility records should not contain
    # street-specific information.
    # --------------------------------------------------------

    if supply_type in {
        GARAGE,
        LOT,
    }:
        if (
            supply.get(
                "segment_id"
            )
            is not None
        ):
            add_warning(
                warnings,
                supply_id,
                (
                    "facility record unexpectedly "
                    "contains a street segment_id."
                ),
            )


# ============================================================
# Main validator
# ============================================================

def main():
    print()
    print(
        "BanReady Parking Supply Validator"
    )

    print(
        "================================="
    )

    print()


    # --------------------------------------------------------
    # File
    # --------------------------------------------------------

    if not DATA_FILE.exists():
        print(
            "ERROR: parking_supply.json "
            "was not found."
        )

        print()

        print(
            f"Expected file: {DATA_FILE}"
        )

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
            "ERROR: parking_supply.json "
            "could not be parsed."
        )

        return


    supplies = data.get(
        "supplies",
        [],
    )

    declared_count = data.get(
        "supply_count"
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
        f"Declared supply count: "
        f"{declared_count}"
    )

    print(
        f"Actual supply count:   "
        f"{len(supplies)}"
    )

    print()


    if not supplies:
        print(
            "ERROR: No parking supply "
            "records were found."
        )

        return


    errors = []

    warnings = []


    # ========================================================
    # Validate individual records
    # ========================================================

    for index, supply in enumerate(
        supplies,
        start=1,
    ):
        validate_supply_record(
            supply=supply,
            index=index,
            errors=errors,
            warnings=warnings,
        )


    # ========================================================
    # Unique supply IDs
    # ========================================================

    supply_ids = [
        supply.get(
            "supply_id"
        )
        for supply in supplies
    ]

    supply_id_counts = Counter(
        supply_ids
    )

    duplicate_ids = [
        supply_id
        for supply_id, count
        in supply_id_counts.items()
        if (
            supply_id is not None
            and count > 1
        )
    ]

    for supply_id in duplicate_ids:
        add_error(
            errors,
            supply_id,
            "duplicate supply_id found.",
        )


    # ========================================================
    # Duplicate facility identities
    # ========================================================

    identities = []

    for supply in supplies:
        name = str(
            supply.get("name")
            or ""
        ).strip().upper()

        address = str(
            supply.get("address")
            or ""
        ).strip().upper()

        identities.append(
            (
                name,
                address,
            )
        )


    identity_counts = Counter(
        identities
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
                "Duplicate supply facility: "
                f"{name} | {address}"
            )
        )


    # ========================================================
    # Dataset counts
    # ========================================================

    garage_count = sum(
        1
        for supply in supplies
        if (
            supply.get(
                "supply_type"
            )
            == GARAGE
        )
    )


    lot_count = sum(
        1
        for supply in supplies
        if (
            supply.get(
                "supply_type"
            )
            == LOT
        )
    )


    verified_total_count = sum(
        1
        for supply in supplies
        if (
            supply.get(
                "total_capacity_status"
            )
            == VERIFIED
        )
    )


    unknown_total_count = sum(
        1
        for supply in supplies
        if (
            supply.get(
                "total_capacity_status"
            )
            == UNKNOWN
        )
    )


    known_ban_count = sum(
        1
        for supply in supplies
        if (
            supply.get(
                "ban_capacity"
            )
            is not None
        )
    )


    unknown_ban_count = sum(
        1
        for supply in supplies
        if (
            supply.get(
                "ban_capacity_status"
            )
            == UNKNOWN
        )
    )


    # ========================================================
    # Capacity totals
    # ========================================================

    verified_garage_capacity = sum(
        supply["total_capacity"]
        for supply in supplies
        if (
            supply.get(
                "supply_type"
            )
            == GARAGE
            and supply.get(
                "total_capacity_status"
            )
            == VERIFIED
            and supply.get(
                "total_capacity"
            )
            is not None
        )
    )


    verified_lot_capacity = sum(
        supply["total_capacity"]
        for supply in supplies
        if (
            supply.get(
                "supply_type"
            )
            == LOT
            and supply.get(
                "total_capacity_status"
            )
            == VERIFIED
            and supply.get(
                "total_capacity"
            )
            is not None
        )
    )


    verified_normal_capacity = (
        verified_garage_capacity
        + verified_lot_capacity
    )


    # ========================================================
    # Known record-specific assertions
    # ========================================================

    union_station = next(
        (
            supply
            for supply in supplies
            if supply.get("name")
            == "Union Station Garage"
        ),
        None,
    )


    if union_station is None:
        errors.append(
            "Union Station Garage is missing."
        )

    else:
        if (
            union_station.get(
                "total_capacity"
            )
            != 500
        ):
            add_error(
                errors,
                union_station.get(
                    "supply_id",
                    "Union Station Garage",
                ),
                (
                    "expected verified total "
                    "capacity of 500."
                ),
            )

        if (
            union_station.get(
                "total_capacity_status"
            )
            != VERIFIED
        ):
            add_error(
                errors,
                union_station.get(
                    "supply_id",
                    "Union Station Garage",
                ),
                (
                    "expected total capacity "
                    "status VERIFIED."
                ),
            )


    # ========================================================
    # Expected unknown garages
    # ========================================================

    expected_unknown_garages = {
        "Federal Plaza Garage",
        "Major Taylor Garage",
        "Pearl-Elm Garage",
        "Worcester Common Garage",
    }


    for garage_name in (
        expected_unknown_garages
    ):
        garage = next(
            (
                supply
                for supply in supplies
                if (
                    supply.get("name")
                    == garage_name
                )
            ),
            None,
        )

        if garage is None:
            errors.append(
                f"{garage_name} is missing."
            )

            continue

        if (
            garage.get(
                "total_capacity"
            )
            is not None
        ):
            add_error(
                errors,
                garage.get(
                    "supply_id",
                    garage_name,
                ),
                (
                    "capacity should remain "
                    "UNKNOWN/null."
                ),
            )

        if (
            garage.get(
                "total_capacity_status"
            )
            != UNKNOWN
        ):
            add_error(
                errors,
                garage.get(
                    "supply_id",
                    garage_name,
                ),
                (
                    "total capacity status "
                    "should be UNKNOWN."
                ),
            )


    # ========================================================
    # Dataset-level checks
    # ========================================================

    if (
        declared_count
        != len(supplies)
    ):
        errors.append(
            (
                "supply_count does not match "
                "the actual number of records."
            )
        )


    if (
        len(supplies)
        != EXPECTED_SUPPLY_COUNT
    ):
        errors.append(
            (
                f"Expected "
                f"{EXPECTED_SUPPLY_COUNT} "
                f"supply records, found "
                f"{len(supplies)}."
            )
        )


    if (
        garage_count
        != EXPECTED_GARAGE_COUNT
    ):
        errors.append(
            (
                f"Expected "
                f"{EXPECTED_GARAGE_COUNT} "
                f"garages, found "
                f"{garage_count}."
            )
        )


    if (
        lot_count
        != EXPECTED_LOT_COUNT
    ):
        errors.append(
            (
                f"Expected "
                f"{EXPECTED_LOT_COUNT} "
                f"lots, found "
                f"{lot_count}."
            )
        )


    if (
        verified_total_count
        != EXPECTED_VERIFIED_TOTAL_COUNT
    ):
        errors.append(
            (
                f"Expected "
                f"{EXPECTED_VERIFIED_TOTAL_COUNT} "
                "VERIFIED total-capacity records, "
                f"found {verified_total_count}."
            )
        )


    if (
        unknown_total_count
        != EXPECTED_UNKNOWN_TOTAL_COUNT
    ):
        errors.append(
            (
                f"Expected "
                f"{EXPECTED_UNKNOWN_TOTAL_COUNT} "
                "UNKNOWN total-capacity records, "
                f"found {unknown_total_count}."
            )
        )


    if (
        known_ban_count
        != EXPECTED_KNOWN_BAN_COUNT
    ):
        errors.append(
            (
                "No ban capacity should be known "
                "at this stage."
            )
        )


    if (
        unknown_ban_count
        != EXPECTED_UNKNOWN_BAN_COUNT
    ):
        errors.append(
            (
                f"Expected "
                f"{EXPECTED_UNKNOWN_BAN_COUNT} "
                "UNKNOWN ban-capacity records, "
                f"found {unknown_ban_count}."
            )
        )


    if (
        verified_garage_capacity
        != EXPECTED_VERIFIED_GARAGE_CAPACITY
    ):
        errors.append(
            (
                "Expected verified normal garage "
                "capacity sum of 500, found "
                f"{verified_garage_capacity}."
            )
        )


    if (
        verified_lot_capacity
        != EXPECTED_VERIFIED_LOT_CAPACITY
    ):
        errors.append(
            (
                "Expected verified normal lot "
                "capacity sum of 673, found "
                f"{verified_lot_capacity}."
            )
        )


    if (
        verified_normal_capacity
        != EXPECTED_VERIFIED_NORMAL_CAPACITY
    ):
        errors.append(
            (
                "Expected verified normal "
                "capacity sum of 1173, found "
                f"{verified_normal_capacity}."
            )
        )


    # ========================================================
    # Metadata consistency
    # ========================================================

    metadata = data.get(
        "metadata",
        {},
    )


    metadata_checks = {
        "garage_count": (
            garage_count
        ),

        "lot_count": (
            lot_count
        ),

        "verified_total_capacity_records": (
            verified_total_count
        ),

        "unknown_total_capacity_records": (
            unknown_total_count
        ),

        "known_ban_capacity_records": (
            known_ban_count
        ),

        "unknown_ban_capacity_records": (
            unknown_ban_count
        ),

        "verified_normal_capacity_sum": (
            verified_normal_capacity
        ),

        "verified_garage_capacity_sum": (
            verified_garage_capacity
        ),

        "verified_lot_capacity_sum": (
            verified_lot_capacity
        ),
    }


    for field, actual_value in (
        metadata_checks.items()
    ):
        metadata_value = metadata.get(
            field
        )

        if (
            metadata_value
            != actual_value
        ):
            errors.append(
                (
                    f"metadata.{field} "
                    f"is {metadata_value}, "
                    f"but calculated value "
                    f"is {actual_value}."
                )
            )


    # ========================================================
    # Summary
    # ========================================================

    print("DATASET SUMMARY")
    print("===============")
    print()

    print(
        f"Supply records:              "
        f"{len(supplies)}"
    )

    print(
        f"Garages:                     "
        f"{garage_count}"
    )

    print(
        f"Lots:                        "
        f"{lot_count}"
    )

    print()

    print(
        f"Verified total capacities:   "
        f"{verified_total_count}"
    )

    print(
        f"Unknown total capacities:    "
        f"{unknown_total_count}"
    )

    print()

    print(
        f"Known ban capacities:        "
        f"{known_ban_count}"
    )

    print(
        f"Unknown ban capacities:      "
        f"{unknown_ban_count}"
    )

    print()

    print(
        f"Verified garage capacity:    "
        f"{verified_garage_capacity}"
    )

    print(
        f"Verified lot capacity:       "
        f"{verified_lot_capacity}"
    )

    print(
        f"Verified normal capacity:    "
        f"{verified_normal_capacity}"
    )

    print()


    # ========================================================
    # Errors
    # ========================================================

    print("ERRORS")
    print("======")
    print()

    if errors:
        for index, error in enumerate(
            errors,
            start=1,
        ):
            print(
                f"{index}. {error}"
            )

    else:
        print("None")

    print()


    # ========================================================
    # Warnings
    # ========================================================

    print("WARNINGS")
    print("========")
    print()

    if warnings:
        for index, warning in enumerate(
            warnings,
            start=1,
        ):
            print(
                f"{index}. {warning}"
            )

    else:
        print("None")

    print()


    # ========================================================
    # Final result
    # ========================================================

    print("VALIDATION RESULT")
    print("=================")
    print()

    if errors:
        print("FAILED")
        print()

        print(
            "Do not use parking_supply.json "
            "for BanReady supply calculations "
            "until all errors are resolved."
        )

        return


    print("PASSED")
    print()

    print(
        "BanReady's municipal facility "
        "supply dataset is internally valid."
    )

    print()

    print(
        "Verified normal facility capacity: "
        f"{verified_normal_capacity}"
    )

    print()

    print(
        "Verified winter-ban capacity: "
        "UNKNOWN"
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
