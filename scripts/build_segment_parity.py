"""
Precompute the ODD/EVEN address side for every Worcester
winter-ban street segment.

Run once from the project folder (whenever the parking-ban
or address-point data changes):

    python -m scripts.build_segment_parity

Input:
    data/processed/winter_parking_ban.geojson
    data/raw/worcester/address_points/Address_Points.geojson  (163 MB)

Output:
    data/processed/segment_parity.json  (small)

After this file exists, the API no longer needs to load the
163 MB address-point file at startup.
"""

import json
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from backend.app.services.parity_engine import (
    infer_address_parity_mapping,
    normalize_street_name,
)


PARKING_FILE = Path("data/processed/winter_parking_ban.geojson")
ADDRESS_FILE = Path("data/raw/worcester/address_points/Address_Points.geojson")
OUTPUT_FILE = Path("data/processed/segment_parity.json")


def main():
    start = time.time()

    with open(PARKING_FILE, encoding="utf-8") as file:
        parking_features = json.load(file)["features"]

    with open(ADDRESS_FILE, encoding="utf-8") as file:
        address_features = json.load(file)["features"]

    print(f"Street segments: {len(parking_features):,}")
    print(f"Address points:  {len(address_features):,}")

    # Group address points by street name so each segment only
    # looks at addresses on its own street. The parity engine
    # filters by the same normalized name, so the result is
    # identical to searching all address points.
    addresses_by_street = defaultdict(list)

    for feature in address_features:
        name = normalize_street_name(
            feature.get("properties", {}).get("cmpltstreetname")
        )
        addresses_by_street[name].append(feature)

    segments = {}
    confidence_counts = defaultdict(int)

    for index, feature in enumerate(parking_features, start=1):
        properties = feature.get("properties", {})
        segment_id = properties.get("segment_id")
        street_name = properties.get("street_name")
        coordinates = feature.get("geometry", {}).get("coordinates", [])

        if segment_id is None or not coordinates:
            continue

        mapping = infer_address_parity_mapping(
            street_name=street_name,
            street_coordinates=coordinates,
            address_features=addresses_by_street.get(
                normalize_street_name(street_name), []
            ),
        )

        segments[str(segment_id)] = {
            "street_name": street_name,
            "left_parity": mapping.left_parity,
            "right_parity": mapping.right_parity,
            "left_odd_count": mapping.left_odd_count,
            "left_even_count": mapping.left_even_count,
            "right_odd_count": mapping.right_odd_count,
            "right_even_count": mapping.right_even_count,
            "usable_address_count": mapping.usable_address_count,
            "confidence": mapping.confidence,
        }

        confidence_counts[mapping.confidence] += 1

        if index % 500 == 0:
            print(f"  processed {index:,} segments...")

    output = {
        "dataset_name": "BanReady Segment Address Parity",
        "city": "Worcester",
        "state": "MA",
        "built_at": datetime.now(timezone.utc).isoformat(),
        "source_files": [str(PARKING_FILE), str(ADDRESS_FILE)],
        "segment_count": len(segments),
        "confidence_counts": dict(confidence_counts),
        "segments": segments,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=1)

    print()
    print(f"Saved {OUTPUT_FILE} ({OUTPUT_FILE.stat().st_size / 1024:.0f} KB)")
    print(f"Confidence: {dict(confidence_counts)}")
    print(f"Done in {time.time() - start:.1f} s")


if __name__ == "__main__":
    main()
