from __future__ import annotations

import hashlib
from typing import Any


def stable_number(
    seed: str | int,
    minimum: int,
    maximum: int,
    salt: str,
) -> int:
    """
    Return a deterministic synthetic integer.

    The same segment ID and salt always produce
    the same value.
    """

    if maximum < minimum:
        raise ValueError(
            "maximum must be greater than "
            "or equal to minimum"
        )

    seed_text = str(seed)

    digest = hashlib.sha256(
        f"{seed_text}:{salt}".encode("utf-8")
    ).hexdigest()

    numeric_value = int(
        digest[:12],
        16,
    )

    value_range = (
        maximum
        - minimum
        + 1
    )

    return (
        minimum
        + numeric_value
        % value_range
    )


def normalize_side(
    value: str | None,
) -> str:
    if value is None:
        return "UNKNOWN"

    normalized = (
        value
        .strip()
        .upper()
        .replace("/", "_")
        .replace("-", "_")
        .replace(" ", "_")
    )

    mappings = {
        "LEFT": "LEFT",
        "RIGHT": "RIGHT",
        "ODD": "ODD",
        "EVEN": "EVEN",
        "BOTH": "BOTH",
        "ALL": "BOTH",
        "NONE": "NONE",
        "NO_RESTRICTION": "NONE",
        "UNKNOWN": "UNKNOWN",
        "UNSURE": "UNKNOWN",
    }

    return mappings.get(
        normalized,
        normalized or "UNKNOWN",
    )


def derive_legal_side(
    restricted_side: str,
) -> str:
    """
    Convert the real modeled restricted side into
    the side potentially legal during the ban.
    """

    side = normalize_side(
        restricted_side
    )

    if side == "ODD":
        return "EVEN"

    if side == "EVEN":
        return "ODD"

    if side == "LEFT":
        return "RIGHT"

    if side == "RIGHT":
        return "LEFT"

    if side == "BOTH":
        return "NONE"

    if side == "NONE":
        return "BOTH"

    return "VERIFY"


def chance_level(
    chance_percent: int,
) -> str:
    if chance_percent < 35:
        return "LOW"

    if chance_percent < 65:
        return "MEDIUM"

    return "HIGH"


def chance_message(
    level: str,
) -> str:
    messages = {
        "LOW": (
            "Low modeled chance here. "
            "Explore nearby streets."
        ),
        "MEDIUM": (
            "Moderate modeled chance here. "
            "Nearby streets may offer alternatives."
        ),
        "HIGH": (
            "Higher modeled chance under this "
            "prototype scenario."
        ),
    }

    return messages[level]


def generate_segment_metrics(
    segment_id: int | None,
    street_name: str,
) -> dict[str, int | str]:
    """
    Generate repeatable synthetic supply,
    demand, request, and chance values.
    """

    seed: str | int

    if segment_id is not None:
        seed = segment_id
    else:
        seed = (
            street_name
            .strip()
            .upper()
        )

    legal_spaces = stable_number(
        seed=seed,
        minimum=18,
        maximum=55,
        salt="legal-spaces",
    )

    expected_vehicles = stable_number(
        seed=seed,
        minimum=20,
        maximum=65,
        salt="expected-vehicles",
    )

    prototype_requests = stable_number(
        seed=seed,
        minimum=2,
        maximum=18,
        salt="prototype-requests",
    )

    raw_chance = round(
        70
        + (
            legal_spaces
            - expected_vehicles
        )
        * 4
        - prototype_requests
        * 2.5
    )

    modeled_chance_percent = max(
        5,
        min(
            92,
            raw_chance,
        ),
    )

    level = chance_level(
        modeled_chance_percent
    )

    return {
        "legal_spaces": legal_spaces,
        "expected_vehicles": (
            expected_vehicles
        ),
        "prototype_requests": (
            prototype_requests
        ),
        "modeled_chance_percent": (
            modeled_chance_percent
        ),
        "chance_level": level,
        "message": chance_message(
            level
        ),
    }


def build_modeled_street_analytics(
    *,
    street_name: str,
    segment_id: int | None,
    parked_side: str,
    restricted_side: str,
    ban_type: str,
) -> dict[str, Any]:
    """
    Combine real BanReady street and side values
    with deterministic synthetic prototype metrics.
    """

    cleaned_street_name = (
        street_name
        .strip()
        .upper()
        or "UNKNOWN STREET"
    )

    metrics = generate_segment_metrics(
        segment_id=segment_id,
        street_name=cleaned_street_name,
    )

    return {
        "data_status": (
            "SYNTHETIC_PROTOTYPE"
        ),
        "street_name": (
            cleaned_street_name
        ),
        "segment_id": segment_id,
        "ban_type": (
            ban_type
            .strip()
            .upper()
        ),
        "parked_side": normalize_side(
            parked_side
        ),
        "restricted_side": normalize_side(
            restricted_side
        ),
        "legal_side": derive_legal_side(
            restricted_side
        ),
        **metrics,
        "disclosure": (
            "Synthetic prototype estimate "
            "using the real matched Worcester "
            "street and modeled ban side. "
            "Not live parking availability."
        ),
    }