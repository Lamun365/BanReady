import json
import math
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

INVENTORY_FILE = Path(
    "data/research/worcester/"
    "conway_821528_curb_inventory.json"
)


EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_SEGMENT_ID = 821528

EXPECTED_STREET_ID = 753050

EXPECTED_SEGMENT_LENGTH = 253.31

EXPECTED_BAN_TYPE = "DECLARED"

EXPECTED_RESTRICTED_SIDE = "EVEN"


ALLOWED_INVENTORY_STATUSES = {
    "INCOMPLETE",
    "COMPLETE",
}


ALLOWED_EVIDENCE_STATUSES = {
    "UNKNOWN",
    "ESTIMATED",
    "VERIFIED",
}


ALLOWED_MEASUREMENT_STATUSES = {
    "ESTIMATED",
    "VERIFIED",
}


ALLOWED_EXCLUSION_TYPES = {
    "DRIVEWAY",
    "INTERSECTION",
    "FIRE_HYDRANT",
    "CROSSWALK",
    "BUS_STOP",
    "CURB_CUT",
    "LOADING_ZONE",
    "NO_PARKING_ZONE",
    "OTHER",
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


def is_non_empty_string(value):
    return (
        isinstance(value, str)
        and value.strip() != ""
    )


def add_error(
    errors,
    message,
):
    errors.append(
        message
    )


def add_warning(
    warnings,
    message,
):
    warnings.append(
        message
    )


# ============================================================
# Validate exclusion
# ============================================================

def validate_exclusion(
    exclusion,
    side_name,
    index,
    errors,
):
    prefix = (
        f"{side_name} exclusion "
        f"{index}"
    )

    exclusion_id = exclusion.get(
        "exclusion_id"
    )

    if not is_non_empty_string(
        exclusion_id
    ):
        add_error(
            errors,
            (
                f"{prefix}: "
                "exclusion_id is missing."
            ),
        )

    exclusion_type = exclusion.get(
        "type"
    )

    if (
        exclusion_type
        not in ALLOWED_EXCLUSION_TYPES
    ):
        add_error(
            errors,
            (
                f"{prefix}: invalid "
                f"exclusion type "
                f"{exclusion_type}."
            ),
        )

    length_meters = exclusion.get(
        "length_meters"
    )

    if not is_number(
        length_meters
    ):
        add_error(
            errors,
            (
                f"{prefix}: length_meters "
                "must be numeric."
            ),
        )

    elif length_meters <= 0:
        add_error(
            errors,
            (
                f"{prefix}: length_meters "
                "must be positive."
            ),
        )

    measurement_status = exclusion.get(
        "measurement_status"
    )

    if (
        measurement_status
        not in ALLOWED_MEASUREMENT_STATUSES
    ):
        add_error(
            errors,
            (
                f"{prefix}: invalid "
                "measurement_status."
            ),
        )

    source = exclusion.get(
        "source"
    )

    if not is_non_empty_string(
        source
    ):
        add_error(
            errors,
            (
                f"{prefix}: source "
                "is required."
            ),
        )


# ============================================================
# Validate one street side
# ============================================================

def validate_side(
    side_data,
    expected_side,
    expected_geometric_side,
    inventory_status,
    errors,
    warnings,
):
    side_name = expected_side

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    if (
        side_data.get("side")
        != expected_side
    ):
        add_error(
            errors,
            (
                f"{side_name}: expected "
                f"side {expected_side}."
            ),
        )

    if (
        side_data.get(
            "geometric_side"
        )
        != expected_geometric_side
    ):
        add_error(
            errors,
            (
                f"{side_name}: expected "
                "geometric side "
                f"{expected_geometric_side}."
            ),
        )

    # --------------------------------------------------------
    # Base curb length
    # --------------------------------------------------------

    base_length = side_data.get(
        "base_curb_length_meters"
    )

    if not is_number(
        base_length
    ):
        add_error(
            errors,
            (
                f"{side_name}: "
                "base curb length is invalid."
            ),
        )

    elif base_length <= 0:
        add_error(
            errors,
            (
                f"{side_name}: "
                "base curb length must "
                "be positive."
            ),
        )

    # --------------------------------------------------------
    # Evidence status
    # --------------------------------------------------------

    evidence_status = side_data.get(
        "evidence_status"
    )

    if (
        evidence_status
        not in ALLOWED_EVIDENCE_STATUSES
    ):
        add_error(
            errors,
            (
                f"{side_name}: invalid "
                "evidence_status."
            ),
        )

    # --------------------------------------------------------
    # Exclusions
    # --------------------------------------------------------

    exclusions = side_data.get(
        "exclusions"
    )

    if not isinstance(
        exclusions,
        list,
    ):
        add_error(
            errors,
            (
                f"{side_name}: exclusions "
                "must be a list."
            ),
        )

        exclusions = []

    exclusion_ids = set()

    calculated_excluded_length = 0.0

    for index, exclusion in enumerate(
        exclusions,
        start=1,
    ):
        if not isinstance(
            exclusion,
            dict,
        ):
            add_error(
                errors,
                (
                    f"{side_name} exclusion "
                    f"{index} is not an object."
                ),
            )

            continue

        validate_exclusion(
            exclusion=exclusion,
            side_name=side_name,
            index=index,
            errors=errors,
        )

        exclusion_id = exclusion.get(
            "exclusion_id"
        )

        if exclusion_id in exclusion_ids:
            add_error(
                errors,
                (
                    f"{side_name}: duplicate "
                    f"exclusion_id "
                    f"{exclusion_id}."
                ),
            )

        if exclusion_id is not None:
            exclusion_ids.add(
                exclusion_id
            )

        length_meters = exclusion.get(
            "length_meters"
        )

        if (
            is_number(length_meters)
            and length_meters > 0
        ):
            calculated_excluded_length += (
                length_meters
            )

    calculated_excluded_length = round(
        calculated_excluded_length,
        2,
    )

    # --------------------------------------------------------
    # Stored excluded length
    # --------------------------------------------------------

    stored_excluded_length = (
        side_data.get(
            "excluded_length_meters"
        )
    )

    usable_length = side_data.get(
        "usable_length_meters"
    )

    # --------------------------------------------------------
    # INCOMPLETE inventory
    # --------------------------------------------------------

    if inventory_status == "INCOMPLETE":
        if evidence_status != "UNKNOWN":
            add_warning(
                warnings,
                (
                    f"{side_name}: inventory is "
                    "INCOMPLETE but side evidence "
                    f"is {evidence_status}."
                ),
            )

        if usable_length is not None:
            add_warning(
                warnings,
                (
                    f"{side_name}: usable length "
                    "is populated while inventory "
                    "is INCOMPLETE."
                ),
            )

    # --------------------------------------------------------
    # COMPLETE inventory
    # --------------------------------------------------------

    if inventory_status == "COMPLETE":
        if not exclusions:
            add_warning(
                warnings,
                (
                    f"{side_name}: COMPLETE "
                    "inventory contains no "
                    "documented exclusions."
                ),
            )

        if not is_number(
            stored_excluded_length
        ):
            add_error(
                errors,
                (
                    f"{side_name}: COMPLETE "
                    "inventory requires "
                    "excluded_length_meters."
                ),
            )

        if not is_number(
            usable_length
        ):
            add_error(
                errors,
                (
                    f"{side_name}: COMPLETE "
                    "inventory requires "
                    "usable_length_meters."
                ),
            )

        if evidence_status == "UNKNOWN":
            add_error(
                errors,
                (
                    f"{side_name}: COMPLETE "
                    "inventory cannot retain "
                    "UNKNOWN evidence status."
                ),
            )

    # --------------------------------------------------------
    # Relationship checks
    # --------------------------------------------------------

    if (
        is_number(
            stored_excluded_length
        )
        and stored_excluded_length < 0
    ):
        add_error(
            errors,
            (
                f"{side_name}: excluded "
                "length cannot be negative."
            ),
        )

    if (
        is_number(usable_length)
        and usable_length < 0
    ):
        add_error(
            errors,
            (
                f"{side_name}: usable "
                "length cannot be negative."
            ),
        )

    if (
        is_number(base_length)
        and is_number(
            stored_excluded_length
        )
        and stored_excluded_length
        > base_length
    ):
        add_error(
            errors,
            (
                f"{side_name}: excluded "
                "length exceeds base "
                "curb length."
            ),
        )

    if (
        is_number(base_length)
        and is_number(usable_length)
        and usable_length
        > base_length
    ):
        add_error(
            errors,
            (
                f"{side_name}: usable "
                "length exceeds base "
                "curb length."
            ),
        )

    if (
        inventory_status == "COMPLETE"
        and is_number(
            stored_excluded_length
        )
        and abs(
            stored_excluded_length
            - calculated_excluded_length
        )
        > 0.05
    ):
        add_error(
            errors,
            (
                f"{side_name}: stored excluded "
                f"length is "
                f"{stored_excluded_length}, "
                "but exclusion records total "
                f"{calculated_excluded_length}."
            ),
        )

    if (
        inventory_status == "COMPLETE"
        and is_number(base_length)
        and is_number(
            stored_excluded_length
        )
        and is_number(usable_length)
    ):
        expected_usable = round(
            base_length
            - stored_excluded_length,
            2,
        )

        if abs(
            usable_length
            - expected_usable
        ) > 0.05:
            add_error(
                errors,
                (
                    f"{side_name}: usable "
                    f"length is {usable_length}, "
                    "but expected "
                    f"{expected_usable}."
                ),
            )

    return {
        "exclusion_count": len(
            exclusions
        ),
        "calculated_excluded_length": (
            calculated_excluded_length
        ),
    }


# ============================================================
# Main validator
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Curb Inventory Validator"
    )

    print(
        "========================================"
    )

    print()

    # --------------------------------------------------------
    # Load inventory
    # --------------------------------------------------------

    if not INVENTORY_FILE.exists():
        print(
            "ERROR: Conway curb inventory "
            "file was not found."
        )

        print()

        print(
            f"Expected file: "
            f"{INVENTORY_FILE}"
        )

        return

    try:
        with open(
            INVENTORY_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

    except json.JSONDecodeError:
        print(
            "ERROR: Conway curb inventory "
            "could not be parsed."
        )

        return

    errors = []

    warnings = []

    # --------------------------------------------------------
    # Inventory identity
    # --------------------------------------------------------

    inventory_id = data.get(
        "inventory_id"
    )

    street_name = data.get(
        "street_name"
    )

    segment_id = data.get(
        "segment_id"
    )

    street_id = data.get(
        "street_id"
    )

    segment_length = data.get(
        "segment_length_meters"
    )

    ban_type = data.get(
        "ban_type"
    )

    restricted_side = data.get(
        "restricted_side"
    )

    inventory_status = data.get(
        "inventory_status"
    )

    # --------------------------------------------------------
    # Identity validation
    # --------------------------------------------------------

    if not is_non_empty_string(
        inventory_id
    ):
        add_error(
            errors,
            "inventory_id is missing.",
        )

    if (
        street_name
        != EXPECTED_STREET_NAME
    ):
        add_error(
            errors,
            (
                "street_name does not match "
                "CONWAY ST."
            ),
        )

    if (
        segment_id
        != EXPECTED_SEGMENT_ID
    ):
        add_error(
            errors,
            (
                "segment_id does not match "
                "821528."
            ),
        )

    if (
        street_id
        != EXPECTED_STREET_ID
    ):
        add_error(
            errors,
            (
                "street_id does not match "
                "753050."
            ),
        )

    if not is_number(
        segment_length
    ):
        add_error(
            errors,
            (
                "segment_length_meters "
                "is invalid."
            ),
        )

    elif abs(
        segment_length
        - EXPECTED_SEGMENT_LENGTH
    ) > 0.05:
        add_error(
            errors,
            (
                "segment length does not "
                "match inspected Worcester "
                "geometry."
            ),
        )

    if (
        ban_type
        != EXPECTED_BAN_TYPE
    ):
        add_error(
            errors,
            (
                "ban_type does not match "
                "DECLARED."
            ),
        )

    if (
        restricted_side
        != EXPECTED_RESTRICTED_SIDE
    ):
        add_error(
            errors,
            (
                "restricted_side does not "
                "match EVEN."
            ),
        )

    if (
        inventory_status
        not in ALLOWED_INVENTORY_STATUSES
    ):
        add_error(
            errors,
            (
                "inventory_status must be "
                "INCOMPLETE or COMPLETE."
            ),
        )

    # --------------------------------------------------------
    # Side mapping
    # --------------------------------------------------------

    if (
        data.get(
            "odd_geometric_side"
        )
        != "LEFT"
    ):
        add_error(
            errors,
            (
                "ODD geometric side must "
                "be LEFT."
            ),
        )

    if (
        data.get(
            "even_geometric_side"
        )
        != "RIGHT"
    ):
        add_error(
            errors,
            (
                "EVEN geometric side must "
                "be RIGHT."
            ),
        )

    # --------------------------------------------------------
    # Side records
    # --------------------------------------------------------

    odd_side = data.get(
        "odd_side"
    )

    even_side = data.get(
        "even_side"
    )

    if not isinstance(
        odd_side,
        dict,
    ):
        add_error(
            errors,
            "odd_side is missing.",
        )

        odd_side = {}

    if not isinstance(
        even_side,
        dict,
    ):
        add_error(
            errors,
            "even_side is missing.",
        )

        even_side = {}

    odd_summary = validate_side(
        side_data=odd_side,
        expected_side="ODD",
        expected_geometric_side="LEFT",
        inventory_status=inventory_status,
        errors=errors,
        warnings=warnings,
    )

    even_summary = validate_side(
        side_data=even_side,
        expected_side="EVEN",
        expected_geometric_side="RIGHT",
        inventory_status=inventory_status,
        errors=errors,
        warnings=warnings,
    )

    # ========================================================
    # Display inventory
    # ========================================================

    print("INVENTORY")
    print("=========")
    print()

    print(
        f"Inventory ID:     "
        f"{inventory_id}"
    )

    print(
        f"Street:           "
        f"{street_name}"
    )

    print(
        f"Segment ID:       "
        f"{segment_id}"
    )

    print(
        f"Street ID:        "
        f"{street_id}"
    )

    print()

    print(
        f"Segment length:   "
        f"{segment_length} m"
    )

    print(
        f"Ban type:         "
        f"{ban_type}"
    )

    print(
        f"Restricted side:  "
        f"{restricted_side}"
    )

    print(
        f"Inventory status: "
        f"{inventory_status}"
    )

    print()

    print("ODD SIDE")
    print("--------")

    print(
        f"Exclusions:       "
        f"{odd_summary['exclusion_count']}"
    )

    print(
        f"Excluded length:  "
        f"{odd_side.get('excluded_length_meters')}"
    )

    print(
        f"Usable length:    "
        f"{odd_side.get('usable_length_meters')}"
    )

    print(
        f"Evidence:         "
        f"{odd_side.get('evidence_status')}"
    )

    print()

    print("EVEN SIDE")
    print("---------")

    print(
        f"Exclusions:       "
        f"{even_summary['exclusion_count']}"
    )

    print(
        f"Excluded length:  "
        f"{even_side.get('excluded_length_meters')}"
    )

    print(
        f"Usable length:    "
        f"{even_side.get('usable_length_meters')}"
    )

    print(
        f"Evidence:         "
        f"{even_side.get('evidence_status')}"
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
            "Fix the curb-inventory errors "
            "before using it for street "
            "capacity estimation."
        )

        return

    print("PASSED")
    print()

    if (
        inventory_status
        == "INCOMPLETE"
    ):
        print(
            "The Conway curb inventory is "
            "structurally valid but remains "
            "INCOMPLETE."
        )

        print()

        print(
            "No street capacity should be "
            "calculated yet."
        )

    else:
        print(
            "The Conway curb inventory is "
            "COMPLETE and structurally ready "
            "for street-supply estimation."
        )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
