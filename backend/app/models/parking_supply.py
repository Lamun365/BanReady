from dataclasses import asdict, dataclass
from typing import Optional


# ============================================================
# Supply types
# ============================================================

GARAGE = "GARAGE"
LOT = "LOT"
STREET_SEGMENT = "STREET_SEGMENT"
PARTNER_LOT = "PARTNER_LOT"


# ============================================================
# Evidence levels
# ============================================================

VERIFIED = "VERIFIED"
ESTIMATED = "ESTIMATED"
UNKNOWN = "UNKNOWN"


# ============================================================
# Parking supply model
# ============================================================

@dataclass
class ParkingSupply:
    supply_id: str

    name: str

    supply_type: str

    latitude: Optional[float] = None
    longitude: Optional[float] = None

    address: Optional[str] = None

    # --------------------------------------------------------
    # Physical / normal legal capacity
    # --------------------------------------------------------

    total_capacity: Optional[int] = None

    # --------------------------------------------------------
    # Legal capacity during the modeled winter ban
    # --------------------------------------------------------

    ban_capacity: Optional[int] = None

    # --------------------------------------------------------
    # Capacity evidence
    # --------------------------------------------------------

    total_capacity_status: str = UNKNOWN
    ban_capacity_status: str = UNKNOWN

    # --------------------------------------------------------
    # Evidence source
    # --------------------------------------------------------

    source_name: Optional[str] = None
    source_url: Optional[str] = None

    # --------------------------------------------------------
    # Street connection
    # --------------------------------------------------------

    street_name: Optional[str] = None
    segment_id: Optional[int] = None

    # --------------------------------------------------------
    # Restriction information
    # --------------------------------------------------------

    ban_type: Optional[str] = None
    restricted_side: Optional[str] = None

    # --------------------------------------------------------
    # Optional geometric information for street supply
    # --------------------------------------------------------

    segment_length_meters: Optional[float] = None

    usable_length_meters: Optional[float] = None

    assumed_space_length_meters: Optional[float] = None

    # --------------------------------------------------------
    # Notes
    # --------------------------------------------------------

    methodology: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self):
        return asdict(self)
