from dataclasses import asdict, dataclass
from typing import Optional


# ============================================================
# BanReady parking status constants
# ============================================================

MUST_MOVE = "MUST_MOVE"
CAN_STAY_DURING_BAN = "CAN_STAY_DURING_BAN" #The vehicle isn't prohibited by the winter-ban rule being evaluated.
NOT_AFFECTED = "NOT_AFFECTED"
VERIFY_RULE = "VERIFY_RULE"


# ============================================================
# Result returned by the rule engine
# ============================================================

@dataclass
class BanDecision:
    status: str
    reason: str
    ban_type: str
    restricted_side: str
    parked_side: str
    restriction_active: bool

    def to_dict(self):
        return asdict(self)


# ============================================================
# Normalize text coming from Worcester GIS / mobile input
# ============================================================

def normalize_value(value: Optional[str]) -> str:
    if value is None:
        return ""

    return str(value).strip().upper()


# ============================================================
# Check whether the parked side is valid
# ============================================================

def valid_parked_side(parked_side: str) -> bool:
    return parked_side in {
        "ODD",
        "EVEN",
        "UNSURE",
    }


# ============================================================
# Main BanReady parking-rule engine
# ============================================================

def evaluate_parking_status(
    ban_type: Optional[str],
    no_parking_side: Optional[str],
    parked_side: Optional[str],
    declared_ban_active: bool = False,
    snow_emergency_active: bool = False,
    permanent_time_restriction_active: bool = False,
) -> BanDecision:
    """
    Evaluate whether a vehicle must move because of a
    Worcester winter parking-ban rule.

    Parameters
    ----------
    ban_type:
        Worcester GIS BanType value.

        Expected values include:
        DECLARED
        PERMANENT
        NON-APPLICABLE
        STATE OWNED - NO WORCESTER WINTER PARKING BAN

    no_parking_side:
        Worcester GIS Side value.

        Expected values include:
        EVEN
        ODD
        BOTH
        NONE
        SPEC

    parked_side:
        Side selected by the resident.

        Expected values:
        EVEN
        ODD
        UNSURE

    declared_ban_active:
        True when a Declared Winter Parking Ban
        is currently active.

    snow_emergency_active:
        True when a snow emergency is active.

    permanent_time_restriction_active:
        True when the applicable permanent-ban
        time restriction is currently active.

        Later the backend can calculate this
        automatically from date and time.

    Returns
    -------
    BanDecision
        Structured BanReady parking decision.
    """

    ban_type = normalize_value(ban_type)
    restricted_side = normalize_value(no_parking_side)
    parked_side = normalize_value(parked_side)

    # ========================================================
    # 1. Missing data
    # ========================================================

    if not ban_type:
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "The street segment does not contain a "
                "usable winter parking-ban type."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=False,
        )

    # ========================================================
    # 2. Non-applicable Worcester winter-ban segments
    # ========================================================

    if ban_type == "NON-APPLICABLE":
        return BanDecision(
            status=NOT_AFFECTED,
            reason=(
                "This street segment is marked as "
                "NON-APPLICABLE in the Worcester winter "
                "parking-ban dataset."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=False,
        )

    # ========================================================
    # 3. State-owned road with no Worcester winter ban
    # ========================================================

    if ban_type == (
        "STATE OWNED - NO WORCESTER WINTER PARKING BAN"
    ):
        return BanDecision(
            status=NOT_AFFECTED,
            reason=(
                "The Worcester dataset identifies this "
                "segment as state owned with no Worcester "
                "winter parking ban."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=False,
        )

    # ========================================================
    # 4. Determine whether the restriction is active
    # ========================================================

    if ban_type == "DECLARED":
        restriction_active = declared_ban_active

    elif ban_type == "PERMANENT":
        restriction_active = (
            permanent_time_restriction_active
            or snow_emergency_active
        )

    else:
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "BanReady does not recognize this "
                "winter parking-ban type."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=False,
        )

    # ========================================================
    # 5. Restriction exists but is not currently active
    # ========================================================

    if not restriction_active:
        return BanDecision(
            status=NOT_AFFECTED,
            reason=(
                "This street has a winter parking restriction, "
                "but the relevant restriction is not currently "
                "active."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=False,
        )

    # ========================================================
    # 6. Missing / special side rules
    # ========================================================

    if not restricted_side:
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "The active restriction does not contain "
                "a usable no-parking side."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    if restricted_side == "SPEC":
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "This street has a special winter parking "
                "restriction that requires separate verification."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    # ========================================================
    # 7. No restricted side
    # ========================================================

    if restricted_side == "NONE":
        return BanDecision(
            status=NOT_AFFECTED,
            reason=(
                "The Worcester winter parking-ban dataset "
                "does not identify a prohibited side for "
                "this segment."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    # ========================================================
    # 8. Both sides prohibited
    # ========================================================

    if restricted_side == "BOTH":
        return BanDecision(
            status=MUST_MOVE,
            reason=(
                "Both sides of this street segment are "
                "restricted while the winter parking "
                "restriction is active."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    # ========================================================
    # 9. Validate side-specific rules
    # ========================================================

    if restricted_side not in {"ODD", "EVEN"}:
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "BanReady does not recognize the "
                "no-parking side value for this segment."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    if not valid_parked_side(parked_side):
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "The selected parked side is missing "
                "or invalid."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    # ========================================================
    # 10. Resident does not know parked side
    # ========================================================

    if parked_side == "UNSURE":
        return BanDecision(
            status=VERIFY_RULE,
            reason=(
                "BanReady needs to know whether the vehicle "
                "is parked on the odd-numbered or "
                "even-numbered side of the street."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    # ========================================================
    # 11. Vehicle is on prohibited side
    # ========================================================

    if parked_side == restricted_side:
        return BanDecision(
            status=MUST_MOVE,
            reason=(
                f"The {parked_side} side of this street "
                "is restricted while the winter parking "
                "restriction is active."
            ),
            ban_type=ban_type,
            restricted_side=restricted_side,
            parked_side=parked_side,
            restriction_active=True,
        )

    # ========================================================
    # 12. Opposite side is not prohibited by this rule
    # ========================================================

    return BanDecision(
        status=CAN_STAY_DURING_BAN,
        reason=(
            f"The Worcester winter parking-ban record "
            f"prohibits the {restricted_side} side, while "
            f"the vehicle is marked as parked on the "
            f"{parked_side} side."
        ),
        ban_type=ban_type,
        restricted_side=restricted_side,
        parked_side=parked_side,
        restriction_active=True,
    )