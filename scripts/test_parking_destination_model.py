import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.models.parking_destination import (
    AVAILABLE,
    MUNICIPAL_GARAGE,
    VERIFIED,
    ParkingDestination,
)


def main():
    print()
    print("BanReady Parking Destination Model Test")
    print("=======================================")
    print()

    destination = ParkingDestination(
        parking_id="test-garage-001",
        name="Test Municipal Garage",
        destination_type=MUNICIPAL_GARAGE,
        latitude=42.26,
        longitude=-71.80,
        address="Test Address",
        verification_status=VERIFIED,
        source_name="TEST SOURCE",
        source_url=None,
        ban_available=True,
        availability_status=AVAILABLE,
        total_capacity=None,
        ban_capacity=None,
        overnight_allowed=True,
        opens_at=None,
        closes_at=None,
        price_type=None,
        price_amount=None,
        notes=(
            "Synthetic record used only to test "
            "the BanReady destination model."
        ),
    )

    data = destination.to_dict()

    print(f"Parking ID:       {data['parking_id']}")
    print(f"Name:             {data['name']}")
    print(f"Type:             {data['destination_type']}")

    print(
        f"Coordinates:      "
        f"{data['latitude']}, "
        f"{data['longitude']}"
    )

    print(
        f"Verification:     "
        f"{data['verification_status']}"
    )

    print(
        f"Ban available:    "
        f"{data['ban_available']}"
    )

    print(
        f"Availability:     "
        f"{data['availability_status']}"
    )

    print(
        f"Total capacity:   "
        f"{data['total_capacity']}"
    )

    print(
        f"Ban capacity:     "
        f"{data['ban_capacity']}"
    )

    print()

    checks = [
        data["parking_id"] == "test-garage-001",
        data["destination_type"] == MUNICIPAL_GARAGE,
        data["verification_status"] == VERIFIED,
        data["ban_available"] is True,
        data["total_capacity"] is None,
        data["ban_capacity"] is None,
    ]

    if all(checks):
        print("MODEL TEST PASSED")
    else:
        print("MODEL TEST FAILED")


if __name__ == "__main__":
    main()