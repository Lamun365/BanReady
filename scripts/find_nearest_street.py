import json
import math
from pathlib import Path


DATA_FILE = Path("data/processed/winter_parking_ban.geojson")
MAX_MATCH_DISTANCE_METERS = 50.0


def lat_lon_to_local_meters(
    latitude,
    longitude,
    reference_latitude,
    reference_longitude
):
    earth_radius = 6371000.0

    x = (
        math.radians(longitude - reference_longitude)
        * earth_radius
        * math.cos(math.radians(reference_latitude))
    )

    y = (
        math.radians(latitude - reference_latitude)
        * earth_radius
    )

    return x, y


def point_to_segment_distance(
    point_lat,
    point_lon,
    start_lat,
    start_lon,
    end_lat,
    end_lon
):
    px = 0.0
    py = 0.0

    ax, ay = lat_lon_to_local_meters(
        start_lat,
        start_lon,
        point_lat,
        point_lon
    )

    bx, by = lat_lon_to_local_meters(
        end_lat,
        end_lon,
        point_lat,
        point_lon
    )

    ab_x = bx - ax
    ab_y = by - ay

    ap_x = px - ax
    ap_y = py - ay

    length_squared = (ab_x * ab_x) + (ab_y * ab_y)

    if length_squared == 0:
        return math.sqrt(
            ((px - ax) ** 2)
            + ((py - ay) ** 2)
        )

    t = ((ap_x * ab_x) + (ap_y * ab_y)) / length_squared

    t = max(0.0, min(1.0, t))

    closest_x = ax + (t * ab_x)
    closest_y = ay + (t * ab_y)

    distance = math.sqrt(
        ((px - closest_x) ** 2)
        + ((py - closest_y) ** 2)
    )

    return distance


def distance_to_linestring(latitude, longitude, coordinates):
    if len(coordinates) < 2:
        return None

    minimum_distance = float("inf")

    for index in range(len(coordinates) - 1):
        start = coordinates[index]
        end = coordinates[index + 1]

        # GeoJSON uses [longitude, latitude]
        start_lon = start[0]
        start_lat = start[1]

        end_lon = end[0]
        end_lat = end[1]

        distance = point_to_segment_distance(
            latitude,
            longitude,
            start_lat,
            start_lon,
            end_lat,
            end_lon
        )

        if distance < minimum_distance:
            minimum_distance = distance

    return minimum_distance


def find_nearest_street(latitude, longitude, features):
    nearest_feature = None
    nearest_distance = float("inf")

    for feature in features:
        geometry = feature.get("geometry")

        if not geometry:
            continue

        if geometry.get("type") != "LineString":
            continue

        coordinates = geometry.get("coordinates", [])

        distance = distance_to_linestring(
            latitude,
            longitude,
            coordinates
        )

        if distance is None:
            continue

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_feature = feature

    return nearest_feature, nearest_distance


def main():
    print()
    print("BanReady Nearest Street Finder")
    print("==============================")
    print()

    if not DATA_FILE.exists():
        print("ERROR: Processed GIS data was not found.")
        print(f"Expected file: {DATA_FILE}")
        return

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            geojson = json.load(file)

    except json.JSONDecodeError:
        print("ERROR: GeoJSON could not be read.")
        return

    features = geojson.get("features", [])

    if not features:
        print("ERROR: No Worcester street features found.")
        return

    print(f"Loaded {len(features)} Worcester street features.")
    print()

    try:
        latitude = float(input("Enter latitude: "))
        longitude = float(input("Enter longitude: "))

    except ValueError:
        print()
        print("ERROR: Latitude and longitude must be numbers.")
        return

    if latitude < -90 or latitude > 90:
        print()
        print("ERROR: Latitude must be between -90 and 90.")
        return

    if longitude < -180 or longitude > 180:
        print()
        print("ERROR: Longitude must be between -180 and 180.")
        return

    print()
    print("Searching Worcester streets...")
    print()

    nearest_feature, distance = find_nearest_street(
        latitude,
        longitude,
        features
    )

    if nearest_feature is None:
        print("NO STREET MATCH FOUND")
        print("=====================")
        return

    properties = nearest_feature.get("properties", {})

    street_name = properties.get("street_name") or "Unknown"

    if distance > MAX_MATCH_DISTANCE_METERS:
        print("NO RELIABLE STREET MATCH")
        print("========================")
        print()

        print(f"Nearest street: {street_name}")
        print(f"Distance: {distance:.2f} meters")
        print()

        print(
            f"The selected location is more than "
            f"{MAX_MATCH_DISTANCE_METERS:.0f} meters "
            "from a mapped Worcester street."
        )

        return

    from_location = properties.get("from_location") or "-"
    to_location = properties.get("to_location") or "-"
    ban_type = properties.get("ban_type") or "Unknown"
    ban_zone = properties.get("ban_zone") or "Unknown"
    no_parking_side = properties.get("no_parking_side") or "Unknown"
    segment_id = properties.get("segment_id")
    street_id = properties.get("street_id")

    print("STREET MATCH FOUND")
    print("==================")
    print()

    print(f"Street: {street_name}")
    print()

    print("Street limits:")
    print(f"From: {from_location}")
    print(f"To:   {to_location}")
    print()

    print("Parking ban information:")
    print(f"Ban Type:        {ban_type}")
    print(f"Ban Zone:        {ban_zone}")
    print(f"No Parking Side: {no_parking_side}")
    print()

    print("GIS match:")
    print(f"Distance to street: {distance:.2f} meters")
    print(f"Segment ID: {segment_id}")
    print(f"Street ID: {street_id}")
    print()

    print("Street matching complete.")


if __name__ == "__main__":
    main()