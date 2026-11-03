import json
import sys
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
    UNKNOWN,
    VERIFIED,
    ParkingDestination,
)


# ============================================================
# Data paths
# ============================================================

INPUT_FILE = Path(
    "data/raw/worcester/municipal_parking/"
    "Municipal_Parking.geojson"
)

OUTPUT_FILE = Path(
    "data/processed/parking_destinations.json"
)


# ============================================================
# Source information
# ============================================================

MUNICIPAL_PARKING_SOURCE_NAME = (
    "City of Worcester Municipal Parking GIS"
)

MUNICIPAL_PARKING_SOURCE_URL = (
    "https://opendata.worcesterma.gov/"
    "maps/worcesterma::municipal-parking/explore"
)

WINTER_BAN_SOURCE_NAME = (
    "City of Worcester Declared Winter Parking Ban"
)

WINTER_BAN_SOURCE_URL = (
    "https://new.worcesterma.gov/announcements/"
    "declared-winter-parking-ban-take-effect-10-am-sunday"
)


# ============================================================
# Garages with verified historical winter-ban evidence
#
# These names correspond to garages identified in the
# municipal parking GIS and the City winter-ban announcement.
#
# This means BanReady has evidence that these facilities
# were designated for resident use for that historical
# declared-ban event.
#
# This does NOT mean live availability is guaranteed today.
# ============================================================

VERIFIED_WINTER_BAN_GARAGES = {
    "WORCESTER COMMON GARAGE",
    "MAJOR TAYLOR GARAGE",
    "UNION STATION GARAGE",
    "FEDERAL PLAZA GARAGE",
    "PEARL-ELM GARAGE",
}


# ============================================================
# Helper: clean value
# ============================================================

def clean_value(value):
    if value is None:
        return None

    text = str(value).strip()

    if text == "":
        return None

    return text


# ============================================================
# Helper: normalize facility type
# ============================================================

def normalize_destination_type(pk_type):
    value = str(pk_type or "").strip().upper()

    if value == "GARAGE":
        return MUNICIPAL_GARAGE

    if value == "LOT":
        return MUNICIPAL_LOT

    return None


# ============================================================
# Geometry helpers
# ============================================================

def collect_polygon_points(coordinates):
    """
    Recursively collect longitude/latitude coordinate pairs
    from Polygon or nested polygon coordinate structures.

    Returns:
        [
            [longitude, latitude],
            ...
        ]
    """

    points = []

    if not coordinates:
        return points

    first = coordinates[0]

    # Coordinate pair:
    # [longitude, latitude]
    if (
        isinstance(first, (int, float))
        and len(coordinates) >= 2
        and isinstance(coordinates[1], (int, float))
    ):
        points.append(
            [
                float(coordinates[0]),
                float(coordinates[1]),
            ]
        )

        return points

    for item in coordinates:
        if isinstance(item, (list, tuple)):
            points.extend(
                collect_polygon_points(item)
            )

    return points


def representative_coordinate(geometry):
    """
    Calculate a simple representative coordinate from all
    polygon vertices.

    For Milestone 8 this coordinate is used for approximate
    destination search.

    This is not a routing entrance coordinate. A later
    routing milestone can replace it with an actual facility
    entrance location.
    """

    if not geometry:
        return None

    geometry_type = geometry.get("type")

    if geometry_type not in {
        "Polygon",
        "MultiPolygon",
    }:
        return None

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    points = collect_polygon_points(
        coordinates
    )

    if not points:
        return None

    longitude_sum = 0.0
    latitude_sum = 0.0

    for point in points:
        longitude_sum += point[0]
        latitude_sum += point[1]

    count = len(points)

    longitude = longitude_sum / count
    latitude = latitude_sum / count

    return latitude, longitude


# ============================================================
# Stable BanReady parking ID
# ============================================================

def build_parking_id(properties):
    parking_type = str(
        properties.get("PK_TYPE") or ""
    ).strip().lower()

    parking_id = clean_value(
        properties.get("PARKING_ID")
    )

    object_id = clean_value(
        properties.get("OBJECTID")
    )

    building_id = clean_value(
        properties.get("BLDG_ID")
    )

    if parking_type == "lot" and parking_id:
        return (
            "worcester-municipal-lot-"
            f"{parking_id}"
        )

    if parking_type == "garage" and building_id:
        return (
            "worcester-municipal-garage-"
            f"{building_id}"
        )

    if object_id:
        return (
            "worcester-municipal-"
            f"{object_id}"
        )

    return None


# ============================================================
# Determine historical ban evidence
# ============================================================

def has_verified_winter_ban_evidence(
    facility_name,
    destination_type,
):
    if destination_type != MUNICIPAL_GARAGE:
        return False

    normalized_name = str(
        facility_name or ""
    ).strip().upper()

    return (
        normalized_name
        in VERIFIED_WINTER_BAN_GARAGES
    )


# ============================================================
# Build one BanReady destination
# ============================================================

def build_destination(feature):
    properties = feature.get(
        "properties",
        {},
    )

    geometry = feature.get(
        "geometry",
        {},
    )

    name = clean_value(
        properties.get("PK_NAME")
    )

    address = clean_value(
        properties.get("PK_ADDR")
    )

    destination_type = normalize_destination_type(
        properties.get("PK_TYPE")
    )

    parking_id = build_parking_id(
        properties
    )

    if not name:
        return None

    if not parking_id:
        return None

    if not destination_type:
        return None

    coordinate = representative_coordinate(
        geometry
    )

    if coordinate is None:
        return None

    latitude = coordinate[0]
    longitude = coordinate[1]

    winter_ban_evidence = (
        has_verified_winter_ban_evidence(
            name,
            destination_type,
        )
    )

    # --------------------------------------------------------
    # Important semantics
    #
    # Municipal identity is verified from the official GIS.
    #
    # ban_available=True means historical official evidence
    # exists that the garage was designated during the
    # verified declared-ban event.
    #
    # It does NOT mean the garage is confirmed available for
    # the current live event.
    # --------------------------------------------------------

    if winter_ban_evidence:
        ban_available = True

        source_name = (
            MUNICIPAL_PARKING_SOURCE_NAME
            + " | "
            + WINTER_BAN_SOURCE_NAME
        )

        source_url = (
            WINTER_BAN_SOURCE_URL
        )

        notes = (
            "Official municipal garage. "
            "Historical City of Worcester evidence "
            "confirms this garage was designated for "
            "resident parking during the referenced "
            "Declared Winter Parking Ban. "
            "Live event availability must still be "
            "verified before production recommendation."
        )

    else:
        ban_available = None

        source_name = (
            MUNICIPAL_PARKING_SOURCE_NAME
        )

        source_url = (
            MUNICIPAL_PARKING_SOURCE_URL
        )

        notes = (
            "Official municipal parking facility. "
            "Winter-ban availability has not yet been "
            "verified for BanReady."
        )

    # --------------------------------------------------------
    # Do not infer capacity from polygon size.
    # Do not interpret PK_MNTH yet.
    # Do not infer overnight access or live availability.
    # --------------------------------------------------------

    destination = ParkingDestination(
        parking_id=parking_id,

        name=name,

        destination_type=destination_type,

        latitude=latitude,
        longitude=longitude,

        address=address,

        verification_status=VERIFIED,

        source_name=source_name,
        source_url=source_url,

        ban_available=ban_available,

        availability_status=UNKNOWN,

        total_capacity=None,
        ban_capacity=None,

        overnight_allowed=None,

        opens_at=None,
        closes_at=None,

        price_type=None,
        price_amount=None,

        notes=notes,
    )

    return destination


# ============================================================
# Main builder
# ============================================================

def main():
    print()
    print("BanReady Parking Destination Builder")
    print("====================================")
    print()

    # --------------------------------------------------------
    # Check input file
    # --------------------------------------------------------

    if not INPUT_FILE.exists():
        print(
            "ERROR: Municipal Parking GeoJSON "
            "was not found."
        )

        print()
        print("Expected file:")
        print(INPUT_FILE)

        return

    # --------------------------------------------------------
    # Load municipal parking data
    # --------------------------------------------------------

    try:
        with open(
            INPUT_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            municipal_data = json.load(file)

    except json.JSONDecodeError:
        print(
            "ERROR: Municipal Parking GeoJSON "
            "could not be read."
        )

        return

    features = municipal_data.get(
        "features",
        [],
    )

    print(
        f"Municipal parking features: "
        f"{len(features)}"
    )

    print()

    if not features:
        print(
            "ERROR: No municipal parking "
            "features were found."
        )

        return

    # --------------------------------------------------------
    # Build destinations
    # --------------------------------------------------------

    destinations = []
    skipped = 0

    for feature in features:
        destination = build_destination(
            feature
        )

        if destination is None:
            skipped += 1
            continue

        destinations.append(
            destination.to_dict()
        )

    # --------------------------------------------------------
    # Sort for stable output
    # --------------------------------------------------------

    destinations.sort(
        key=lambda item: (
            item["destination_type"],
            item["name"],
        )
    )

    # --------------------------------------------------------
    # Count classifications
    # --------------------------------------------------------

    garage_count = sum(
        1
        for item in destinations
        if item["destination_type"]
        == MUNICIPAL_GARAGE
    )

    lot_count = sum(
        1
        for item in destinations
        if item["destination_type"]
        == MUNICIPAL_LOT
    )

    verified_ban_count = sum(
        1
        for item in destinations
        if item["ban_available"] is True
    )

    unknown_ban_count = sum(
        1
        for item in destinations
        if item["ban_available"] is None
    )

    # --------------------------------------------------------
    # Save processed destination dataset
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output = {
        "dataset_name": "BanReady Parking Destinations",
        "city": "Worcester",
        "state": "MA",
        "destination_count": len(
            destinations
        ),
        "destinations": destinations,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False,
        )

    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print(
        f"Destinations created: "
        f"{len(destinations)}"
    )

    print(
        f"Skipped features:     "
        f"{skipped}"
    )

    print()

    print(
        f"Municipal garages:    "
        f"{garage_count}"
    )

    print(
        f"Municipal lots:       "
        f"{lot_count}"
    )

    print()

    print(
        f"Historical ban evidence: "
        f"{verified_ban_count}"
    )

    print(
        f"Ban availability unknown: "
        f"{unknown_ban_count}"
    )

    print()

    # --------------------------------------------------------
    # Print each generated destination
    # --------------------------------------------------------

    print("GENERATED DESTINATIONS")
    print("======================")
    print()

    for destination in destinations:
        print(
            destination["parking_id"]
        )

        print(
            f"  Name: "
            f"{destination['name']}"
        )

        print(
            f"  Type: "
            f"{destination['destination_type']}"
        )

        print(
            f"  Address: "
            f"{destination['address']}"
        )

        print(
            f"  Latitude: "
            f"{destination['latitude']:.8f}"
        )

        print(
            f"  Longitude: "
            f"{destination['longitude']:.8f}"
        )

        print(
            f"  Verified: "
            f"{destination['verification_status']}"
        )

        print(
            f"  Ban evidence: "
            f"{destination['ban_available']}"
        )

        print(
            f"  Live availability: "
            f"{destination['availability_status']}"
        )

        print(
            f"  Total capacity: "
            f"{destination['total_capacity']}"
        )

        print(
            f"  Ban capacity: "
            f"{destination['ban_capacity']}"
        )

        print()

    # --------------------------------------------------------
    # Consistency checks
    # --------------------------------------------------------

    print("CONSISTENCY CHECK")
    print("=================")
    print()

    total_classified = (
        garage_count
        + lot_count
    )

    print(
        f"Input features:       "
        f"{len(features)}"
    )

    print(
        f"Output destinations:  "
        f"{len(destinations)}"
    )

    print(
        f"Classified total:     "
        f"{total_classified}"
    )

    print()

    if (
        len(destinations) == len(features)
        and total_classified
        == len(destinations)
        and skipped == 0
    ):
        print(
            "PASS: All municipal parking "
            "features were converted."
        )
    else:
        print(
            "WARNING: Some municipal parking "
            "features were not converted."
        )

    print()

    if (
        garage_count == 5
        and lot_count == 7
    ):
        print(
            "PASS: Expected 5 garages and "
            "7 lots were preserved."
        )
    else:
        print(
            "WARNING: Garage/Lot counts differ "
            "from the inspected source dataset."
        )

    print()

    if verified_ban_count == 5:
        print(
            "PASS: Five garage destinations have "
            "historical winter-ban evidence."
        )
    else:
        print(
            "WARNING: Expected five historically "
            "verified winter-ban garages."
        )

    print()

    print("Saved:")
    print(OUTPUT_FILE)

    print()
    print(
        "Parking destination build complete."
    )


if __name__ == "__main__":
    main()