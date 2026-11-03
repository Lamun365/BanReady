import json
import math
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from backend.app.services.location_engine import (
    find_nearest_street,
)

from backend.app.services.side_engine import (
    determine_side_of_linestring,
    normalize_line_coordinates,
)


PARKING_FILE = Path(
    "data/processed/winter_parking_ban.geojson"
)

TARGET_SEGMENT_ID = 821528

OFFSET_METERS = 8.0


def find_segment(features, segment_id):
    for feature in features:
        properties = feature.get(
            "properties",
            {},
        )

        if (
            properties.get("segment_id")
            == segment_id
        ):
            return feature

    return None


def create_offset_point(
    start_lat,
    start_lon,
    end_lat,
    end_lon,
    side,
    offset_meters,
):
    earth_radius = 6371000.0

    reference_lat = (
        start_lat + end_lat
    ) / 2.0

    reference_lon = (
        start_lon + end_lon
    ) / 2.0

    start_x = (
        math.radians(
            start_lon - reference_lon
        )
        * earth_radius
        * math.cos(
            math.radians(reference_lat)
        )
    )

    start_y = (
        math.radians(
            start_lat - reference_lat
        )
        * earth_radius
    )

    end_x = (
        math.radians(
            end_lon - reference_lon
        )
        * earth_radius
        * math.cos(
            math.radians(reference_lat)
        )
    )

    end_y = (
        math.radians(
            end_lat - reference_lat
        )
        * earth_radius
    )

    direction_x = end_x - start_x
    direction_y = end_y - start_y

    length = math.sqrt(
        direction_x * direction_x
        + direction_y * direction_y
    )

    if length == 0:
        return None

    direction_x = direction_x / length
    direction_y = direction_y / length

    perpendicular_x = -direction_y
    perpendicular_y = direction_x

    if side == "RIGHT":
        perpendicular_x = -perpendicular_x
        perpendicular_y = -perpendicular_y

    elif side != "LEFT":
        return None

    offset_x = (
        perpendicular_x
        * offset_meters
    )

    offset_y = (
        perpendicular_y
        * offset_meters
    )

    latitude = (
        reference_lat
        + math.degrees(
            offset_y / earth_radius
        )
    )

    longitude = (
        reference_lon
        + math.degrees(
            offset_x
            / (
                earth_radius
                * math.cos(
                    math.radians(reference_lat)
                )
            )
        )
    )

    return latitude, longitude


def find_verified_test_point(
    side,
    target_feature,
    all_features,
):
    geometry = target_feature.get(
        "geometry",
        {},
    )

    coordinates = geometry.get(
        "coordinates",
        [],
    )

    lines = normalize_line_coordinates(
        coordinates
    )

    for line in lines:
        if len(line) < 2:
            continue

        for index in range(
            len(line) - 1
        ):
            start = line[index]
            end = line[index + 1]

            if (
                len(start) < 2
                or len(end) < 2
            ):
                continue

            start_lon = start[0]
            start_lat = start[1]

            end_lon = end[0]
            end_lat = end[1]

            values = (
                start_lon,
                start_lat,
                end_lon,
                end_lat,
            )

            if not all(
                isinstance(value, (int, float))
                for value in values
            ):
                continue

            point = create_offset_point(
                start_lat,
                start_lon,
                end_lat,
                end_lon,
                side,
                OFFSET_METERS,
            )

            if point is None:
                continue

            latitude = point[0]
            longitude = point[1]

            match = find_nearest_street(
                latitude=latitude,
                longitude=longitude,
                parking_features=all_features,
            )

            if not match.matched:
                continue

            if (
                match.segment_id
                != TARGET_SEGMENT_ID
            ):
                continue

            side_result = (
                determine_side_of_linestring(
                    latitude,
                    longitude,
                    coordinates,
                )
            )

            if (
                side_result.geometric_side
                != side
            ):
                continue

            return {
                "latitude": latitude,
                "longitude": longitude,
                "side": side,
                "distance": (
                    side_result.distance_meters
                ),
                "matched_street": (
                    match.street_name
                ),
                "matched_segment": (
                    match.segment_id
                ),
            }

    return None


def print_point(
    label,
    result,
    expected_parity,
    expected_status,
):
    print()
    print(label)
    print("-" * len(label))

    if result is None:
        print(
            "NO VERIFIED TEST POINT FOUND"
        )

        return

    print(
        f"Latitude:        "
        f"{result['latitude']:.12f}"
    )

    print(
        f"Longitude:       "
        f"{result['longitude']:.12f}"
    )

    print(
        f"Detected side:   "
        f"{result['side']}"
    )

    print(
        f"Street distance: "
        f"{result['distance']:.2f} m"
    )

    print(
        f"Matched street:  "
        f"{result['matched_street']}"
    )

    print(
        f"Matched segment: "
        f"{result['matched_segment']}"
    )

    print(
        f"Expected parity: "
        f"{expected_parity}"
    )

    print(
        f"Expected status: "
        f"{expected_status}"
    )


def main():
    print()
    print(
        "BanReady Verified Mobile Test "
        "Point Generator"
    )

    print(
        "========================================"
    )

    print()

    if not PARKING_FILE.exists():
        print(
            "ERROR: Processed parking-ban "
            "GeoJSON not found."
        )

        return

    try:
        with open(
            PARKING_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            parking_data = json.load(file)

    except json.JSONDecodeError:
        print(
            "ERROR: Parking-ban GeoJSON "
            "could not be read."
        )

        return

    features = parking_data.get(
        "features",
        [],
    )

    target_feature = find_segment(
        features,
        TARGET_SEGMENT_ID,
    )

    if target_feature is None:
        print(
            "ERROR: Target Conway Street "
            "segment was not found."
        )

        return

    properties = target_feature.get(
        "properties",
        {},
    )

    print(
        f"Target street:   "
        f"{properties.get('street_name')}"
    )

    print(
        f"Target segment:  "
        f"{properties.get('segment_id')}"
    )

    print(
        f"Ban type:        "
        f"{properties.get('ban_type')}"
    )

    print(
        f"Restricted side: "
        f"{properties.get('no_parking_side')}"
    )

    print()

    print(
        "Searching for points that independently "
        "match back to Conway Street..."
    )

    left_result = find_verified_test_point(
        side="LEFT",
        target_feature=target_feature,
        all_features=features,
    )

    right_result = find_verified_test_point(
        side="RIGHT",
        target_feature=target_feature,
        all_features=features,
    )

    print_point(
        label="VERIFIED LEFT TEST POINT",
        result=left_result,
        expected_parity="ODD",
        expected_status=(
            "CAN_STAY_DURING_BAN"
        ),
    )

    print_point(
        label="VERIFIED RIGHT TEST POINT",
        result=right_result,
        expected_parity="EVEN",
        expected_status="MUST_MOVE",
    )

    print()
    print(
        "========================================"
    )

    print("IPHONE TEST PLAN")

    print(
        "========================================"
    )

    if left_result is not None:
        print()
        print("TEST A")
        print("------")
        print("Street: CONWAY ST")

        print(
            "Latitude:  "
            f"{left_result['latitude']:.12f}"
        )

        print(
            "Longitude: "
            f"{left_result['longitude']:.12f}"
        )

        print("Snow Ban: ACTIVE")
        print("Expected: CAN STAY")

    if right_result is not None:
        print()
        print("TEST B")
        print("------")
        print("Street: CONWAY ST")

        print(
            "Latitude:  "
            f"{right_result['latitude']:.12f}"
        )

        print(
            "Longitude: "
            f"{right_result['longitude']:.12f}"
        )

        print("Snow Ban: ACTIVE")
        print("Expected: MUST MOVE")


if __name__ == "__main__":
    main()