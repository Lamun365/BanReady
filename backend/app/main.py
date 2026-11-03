import json
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel, Field

from backend.app.services.destination_engine import (
    find_winter_ban_parking_options,
)

from backend.app.services.location_engine import (
    find_nearest_street,
)

from backend.app.services.parking_status_engine import (
    evaluate_vehicle_parking_status,
)

from backend.app.services.parity_engine import (
    parity_mapping_from_record,
)

from backend.app.services.time_engine import (
    is_permanent_ban_time,
    to_worcester_time,
)

from backend.app.models.prototype_analytics import (
    ModeledStreetRequest,
)

from backend.app.services.prototype_analytics_engine import (
    build_modeled_street_analytics,
)


# ============================================================
# Data locations
# ============================================================

PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

ADDRESS_FILE = Path(
    "data/raw/worcester/address_points/Address_Points.geojson"
)

# Small precomputed ODD/EVEN file built by
# scripts/build_segment_parity.py. When it exists, the
# 163 MB address-point file is not needed at startup.
SEGMENT_PARITY_FILE = Path(
    "data/processed/segment_parity.json"
)


# ============================================================
# Load JSON / GeoJSON helper
# ============================================================

def load_json_file(path: Path):
    if not path.exists():
        raise RuntimeError(
            f"Required BanReady data file not found: {path}"
        )

    try:
        with open(
            path,
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"BanReady could not read data file: {path}"
        ) from error


# ============================================================
# Load Worcester datasets once when API starts
# ============================================================

parking_data = load_json_file(
    PARKING_FILE
)

PARKING_FEATURES = parking_data.get(
    "features",
    [],
)


if not PARKING_FEATURES:
    raise RuntimeError(
        "No Worcester parking-ban features were loaded."
    )


# ------------------------------------------------------------
# ODD / EVEN side data
#
# Preferred: small precomputed file (fast, cloud-friendly).
# Fallback:  the full 163 MB address-point file.
# ------------------------------------------------------------

if SEGMENT_PARITY_FILE.exists():
    segment_parity_data = load_json_file(
        SEGMENT_PARITY_FILE
    )

    SEGMENT_PARITY = {
        str(segment_id): parity_mapping_from_record(record)
        for segment_id, record in segment_parity_data.get(
            "segments",
            {},
        ).items()
    }

    ADDRESS_FEATURES = []

    PARITY_SOURCE = "precomputed_segment_parity"

    if not SEGMENT_PARITY:
        raise RuntimeError(
            "The segment parity file contains no segments."
        )

else:
    address_data = load_json_file(
        ADDRESS_FILE
    )

    ADDRESS_FEATURES = address_data.get(
        "features",
        [],
    )

    SEGMENT_PARITY = {}

    PARITY_SOURCE = "address_points"

    if not ADDRESS_FEATURES:
        raise RuntimeError(
            "No Worcester address-point features were loaded."
        )


# ============================================================
# FastAPI application
# ============================================================

app = FastAPI(
    title="BanReady API",
    description=(
        "Backend API for BanReady Worcester "
        "winter parking decisions and "
        "parking destination search."
    ),
    version="0.4.0",
)


# ============================================================
# Parking-check request model
# ============================================================

class ParkingCheckRequest(BaseModel):
    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    declared_ban_active: bool = False

    snow_emergency_active: bool = False

    permanent_time_restriction_active: bool = False

    # Optional: pretend it is a different date/time (for testing
    # and demos). Leave empty to use the current Worcester time.
    check_time: datetime | None = None


# ============================================================
# Parking-options request model
# ============================================================

class ParkingOptionsRequest(BaseModel):
    latitude: float = Field(
        ge=-90,
        le=90,
    )

    longitude: float = Field(
        ge=-180,
        le=180,
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=20,
    )

    max_distance_meters: float | None = Field(
        default=None,
        ge=0,
    )


# ============================================================
# Root endpoint
# ============================================================

@app.get("/")
def root():
    return {
        "name": "BanReady API",
        "version": "0.4.0",
        "status": "running",

        "parking_segments": len(
            PARKING_FEATURES
        ),

        "parity_source": PARITY_SOURCE,

        "precomputed_parity_segments": len(
            SEGMENT_PARITY
        ),

        "address_points": len(
            ADDRESS_FEATURES
        ),

        "endpoints": [
            "/health",
            "/parking/check",
            "/parking/options",
        ],
    }


# ============================================================
# Health endpoint
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "banready-api",

        "parking_segments": len(
            PARKING_FEATURES
        ),

        "parity_source": PARITY_SOURCE,

        "precomputed_parity_segments": len(
            SEGMENT_PARITY
        ),

        "address_points": len(
            ADDRESS_FEATURES
        ),
    }


# ============================================================
# Parking-status endpoint
# ============================================================

@app.post("/parking/check")
def check_parking(
    request: ParkingCheckRequest,
):
    # --------------------------------------------------------
    # Find nearest Worcester parking-ban street
    # --------------------------------------------------------

    street_match = find_nearest_street(
        latitude=request.latitude,
        longitude=request.longitude,
        parking_features=PARKING_FEATURES,
    )

    # --------------------------------------------------------
    # No reliable Worcester street match
    # --------------------------------------------------------

    if not street_match.matched:
        distance = None

        if (
            street_match.distance_meters
            != float("inf")
        ):
            distance = round(
                street_match.distance_meters,
                2,
            )

        return {
            "matched": False,

            "status": "VERIFY_RULE",

            "reason": (
                street_match.reason
            ),

            "street_name": (
                street_match.street_name
            ),

            "segment_id": (
                street_match.segment_id
            ),

            "street_id": (
                street_match.street_id
            ),

            "distance_meters": distance,

            "ban_type": (
                street_match.ban_type
            ),

            "ban_zone": (
                street_match.ban_zone
            ),

            "restricted_side": (
                street_match.restricted_side
            ),

            "geometric_side": "UNKNOWN",

            "parked_side": "UNSURE",

            "left_parity": "UNSURE",

            "right_parity": "UNSURE",

            "parity_confidence": "LOW",
        }

    # --------------------------------------------------------
    # Is the permanent 2-6 a.m. winter ban in effect?
    # (Dec 1 - Apr 30, Worcester time; or forced by the app)
    # --------------------------------------------------------

    checked_at = to_worcester_time(request.check_time)

    permanent_active = (
        request.permanent_time_restriction_active
        or is_permanent_ban_time(checked_at)
    )

    # --------------------------------------------------------
    # Run complete BanReady parking-status pipeline
    # --------------------------------------------------------

    parking_result = evaluate_vehicle_parking_status(
        latitude=request.latitude,
        longitude=request.longitude,

        street_feature=(
            street_match.feature
        ),

        address_features=(
            ADDRESS_FEATURES
        ),

        declared_ban_active=(
            request.declared_ban_active
        ),

        snow_emergency_active=(
            request.snow_emergency_active
        ),

        permanent_time_restriction_active=(
            permanent_active
        ),

        precomputed_parity=SEGMENT_PARITY.get(
            str(street_match.segment_id)
        ),
    )

    # --------------------------------------------------------
    # Return parking decision
    # --------------------------------------------------------

    return {
        "matched": True,

        "status": (
            parking_result.status
        ),

        "reason": (
            parking_result.reason
        ),

        "street_name": (
            parking_result.street_name
        ),

        "segment_id": (
            parking_result.segment_id
        ),

        "street_id": (
            street_match.street_id
        ),

        "distance_meters": round(
            parking_result.distance_to_street_meters,
            2,
        ),

        "ban_type": (
            parking_result.ban_type
        ),

        "ban_zone": (
            parking_result.ban_zone
        ),

        "restricted_side": (
            parking_result.restricted_side
        ),

        "geometric_side": (
            parking_result.geometric_side
        ),

        "parked_side": (
            parking_result.parked_side
        ),

        "left_parity": (
            parking_result.left_parity
        ),

        "right_parity": (
            parking_result.right_parity
        ),

        "parity_confidence": (
            parking_result.parity_confidence
        ),

        "permanent_ban_active": permanent_active,

        "checked_at": checked_at.isoformat(),
    }


# ============================================================
# Parking-options endpoint
# ============================================================

@app.post("/parking/options")
def parking_options(
    request: ParkingOptionsRequest,
):
    """
    Return nearby verified winter-ban parking candidates.

    Milestone 8 behavior:

    - verified destinations only
    - historical winter-ban evidence required
    - straight-line distance ranking
    - live availability remains unknown
    - capacity remains unknown
    - walking routes are not calculated yet
    """

    result = find_winter_ban_parking_options(
        latitude=request.latitude,
        longitude=request.longitude,
        limit=request.limit,
        max_distance_meters=(
            request.max_distance_meters
        ),
    )

    return result.to_dict()

@app.post("/parking/modeled-street")
def modeled_street(
    request: ModeledStreetRequest,
):
    """
    Return location-responsive prototype analytics.

    Street, side, ban type, and segment ID come
    from BanReady's real parking-check result.

    Supply, demand, request, and chance values are
    deterministic synthetic prototype values.
    """

    return build_modeled_street_analytics(
        street_name=request.street_name,
        segment_id=request.segment_id,
        parked_side=request.parked_side,
        restricted_side=(
            request.restricted_side
        ),
        ban_type=request.ban_type,
    )