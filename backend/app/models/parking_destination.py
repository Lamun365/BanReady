from dataclasses import asdict, dataclass
from typing import Optional


# ============================================================
# Destination types
# ============================================================

MUNICIPAL_GARAGE = "MUNICIPAL_GARAGE"
MUNICIPAL_LOT = "MUNICIPAL_LOT"
STREET = "STREET"
PARTNER_LOT = "PARTNER_LOT"


# ============================================================
# Verification states
# ============================================================

VERIFIED = "VERIFIED"
UNVERIFIED = "UNVERIFIED"


# ============================================================
# Availability states
# ============================================================

AVAILABLE = "AVAILABLE"
UNAVAILABLE = "UNAVAILABLE"
UNKNOWN = "UNKNOWN"


# ============================================================
# Parking destination model
# ============================================================

@dataclass
class ParkingDestination:
    parking_id: str

    name: str

    destination_type: str

    latitude: float
    longitude: float

    address: Optional[str] = None

    # Verification
    verification_status: str = UNVERIFIED

    source_name: Optional[str] = None
    source_url: Optional[str] = None

    # Winter parking ban information
    ban_available: Optional[bool] = None

    availability_status: str = UNKNOWN

    # Capacity
    total_capacity: Optional[int] = None
    ban_capacity: Optional[int] = None

    # Operating information
    overnight_allowed: Optional[bool] = None

    opens_at: Optional[str] = None
    closes_at: Optional[str] = None

    # Pricing
    price_type: Optional[str] = None
    price_amount: Optional[float] = None

    # Additional information
    notes: Optional[str] = None


    def to_dict(self):
        return asdict(self)