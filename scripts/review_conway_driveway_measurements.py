import json
import math
from pathlib import Path


# ============================================================
# Configuration
# ============================================================

INPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_driveway_measurements.json"
)

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_driveway_interval_review.json"
)


EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_SEGMENT_ID = 821528

EXPECTED_RESTRICTED_SIDE = "EVEN"

EXPECTED_SEGMENT_LENGTH_METERS = 253.31

EXPECTED_MEASUREMENT_COUNT = 14

EXPECTED_ODD_COUNT = 8

EXPECTED_EVEN_COUNT = 6


ALLOWED_PARITY_SIDES = {
    "ODD",
    "EVEN",
}


# ============================================================
# Helpers
# ============================================================

def is_number(value):
    if isinstance(value, bool):
        return False

    if not isinstance(
        value,
        (int, float),
    ):
        return False

    return math.isfinite(
        float(value)
    )


def is_non_empty_string(value):
    return (
        isinstance(value, str)
        and value.strip() != ""
    )


def load_json(path):
    if not path.exists():
        raise RuntimeError(
            f"Required file not found: {path}"
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
            f"Could not parse JSON file: {path}"
        ) from error


def add_error(
    errors,
    message,
):
    errors.append(
        message
    )


def add_warning(
    warnings,
    message,
):
    warnings.append(
        message
    )


# ============================================================
# Build one driveway interval
# ============================================================

def build_interval(
    measurement,
    segment_length_meters,
    errors,
):
    exclusion_id = measurement.get(
        "exclusion_id"
    )

    if not is_non_empty_string(
        exclusion_id
    ):
        add_error(
            errors,
            "Measurement has no exclusion_id.",
        )

        return None

    parity_side = measurement.get(
        "parity_side"
    )

    if (
        parity_side
        not in ALLOWED_PARITY_SIDES
    ):
        add_error(
            errors,
            (
                f"{exclusion_id}: invalid "
                f"parity_side {parity_side}."
            ),
        )

        return None

    position = measurement.get(
        "position_along_segment_meters"
    )

    width = measurement.get(
        "estimated_frontage_width_meters"
    )

    if not is_number(
        position
    ):
        add_error(
            errors,
            (
                f"{exclusion_id}: invalid "
                "position along segment."
            ),
        )

        return None

    if not is_number(
        width
    ):
        add_error(
            errors,
            (
                f"{exclusion_id}: invalid "
                "estimated frontage width."
            ),
        )

        return None

    if width <= 0:
        add_error(
            errors,
            (
                f"{exclusion_id}: frontage "
                "width must be positive."
            ),
        )

        return None

    if (
        position < 0
        or position
        > segment_length_meters
    ):
        add_error(
            errors,
            (
                f"{exclusion_id}: position "
                "falls outside the Conway segment."
            ),
        )

        return None

    raw_start = (
        position
        - width / 2.0
    )

    raw_end = (
        position
        + width / 2.0
    )

    clamped_start = max(
        0.0,
        raw_start,
    )

    clamped_end = min(
        segment_length_meters,
        raw_end,
    )

    clamped_width = max(
        0.0,
        clamped_end
        - clamped_start,
    )

    was_clamped = (
        abs(
            raw_start
            - clamped_start
        )
        > 0.001
        or abs(
            raw_end
            - clamped_end
        )
        > 0.001
    )

    return {
        "exclusion_id": (
            exclusion_id
        ),

        "driveway_id": (
            measurement.get(
                "driveway_id"
            )
        ),

        "object_id": (
            measurement.get(
                "object_id"
            )
        ),

        "global_id": (
            measurement.get(
                "global_id"
            )
        ),

        "driveway_type": (
            measurement.get(
                "driveway_type"
            )
        ),

        "parity_side": (
            parity_side
        ),

        "geometric_side": (
            measurement.get(
                "geometric_side"
            )
        ),

        "position_along_segment_meters": (
            round(
                position,
                2,
            )
        ),

        "estimated_frontage_width_meters": (
            round(
                width,
                2,
            )
        ),

        "raw_interval_start_meters": (
            round(
                raw_start,
                2,
            )
        ),

        "raw_interval_end_meters": (
            round(
                raw_end,
                2,
            )
        ),

        "interval_start_meters": (
            round(
                clamped_start,
                2,
            )
        ),

        "interval_end_meters": (
            round(
                clamped_end,
                2,
            )
        ),

        "clamped_interval_width_meters": (
            round(
                clamped_width,
                2,
            )
        ),

        "was_clamped": (
            was_clamped
        ),

        "distance_to_centerline_meters": (
            measurement.get(
                "distance_to_centerline_meters"
            )
        ),

        "measurement_status": (
            measurement.get(
                "measurement_status"
            )
        ),

        "review_status": (
            measurement.get(
                "review_status"
            )
        ),
    }


# ============================================================
# Detect pairwise overlaps
# ============================================================

def detect_overlaps(
    intervals,
):
    ordered = sorted(
        intervals,
        key=lambda item: (
            item[
                "interval_start_meters"
            ],
            item[
                "interval_end_meters"
            ],
        ),
    )

    overlaps = []

    for first_index in range(
        len(ordered)
    ):
        first = ordered[
            first_index
        ]

        for second_index in range(
            first_index + 1,
            len(ordered),
        ):
            second = ordered[
                second_index
            ]

            if (
                second[
                    "interval_start_meters"
                ]
                >= first[
                    "interval_end_meters"
                ]
            ):
                break

            overlap_start = max(
                first[
                    "interval_start_meters"
                ],
                second[
                    "interval_start_meters"
                ],
            )

            overlap_end = min(
                first[
                    "interval_end_meters"
                ],
                second[
                    "interval_end_meters"
                ],
            )

            overlap_length = (
                overlap_end
                - overlap_start
            )

            if overlap_length > 0:
                overlaps.append(
                    {
                        "first_exclusion_id": (
                            first[
                                "exclusion_id"
                            ]
                        ),

                        "second_exclusion_id": (
                            second[
                                "exclusion_id"
                            ]
                        ),

                        "overlap_start_meters": (
                            round(
                                overlap_start,
                                2,
                            )
                        ),

                        "overlap_end_meters": (
                            round(
                                overlap_end,
                                2,
                            )
                        ),

                        "overlap_length_meters": (
                            round(
                                overlap_length,
                                2,
                            )
                        ),
                    }
                )

    return overlaps


# ============================================================
# Merge side-specific intervals
# ============================================================

def merge_intervals(
    intervals,
):
    if not intervals:
        return []

    ordered = sorted(
        intervals,
        key=lambda item: (
            item[
                "interval_start_meters"
            ],
            item[
                "interval_end_meters"
            ],
        ),
    )

    merged = []

    for interval in ordered:
        start = interval[
            "interval_start_meters"
        ]

        end = interval[
            "interval_end_meters"
        ]

        exclusion_id = interval[
            "exclusion_id"
        ]

        if not merged:
            merged.append(
                {
                    "interval_start_meters": (
                        start
                    ),

                    "interval_end_meters": (
                        end
                    ),

                    "source_exclusion_ids": [
                        exclusion_id
                    ],
                }
            )

            continue

        current = merged[-1]

        # ----------------------------------------------------
        # Overlapping or directly touching intervals are
        # merged into one continuous exclusion interval.
        # ----------------------------------------------------

        if (
            start
            <= current[
                "interval_end_meters"
            ]
        ):
            current[
                "interval_end_meters"
            ] = max(
                current[
                    "interval_end_meters"
                ],
                end,
            )

            current[
                "source_exclusion_ids"
            ].append(
                exclusion_id
            )

        else:
            merged.append(
                {
                    "interval_start_meters": (
                        start
                    ),

                    "interval_end_meters": (
                        end
                    ),

                    "source_exclusion_ids": [
                        exclusion_id
                    ],
                }
            )

    for index, interval in enumerate(
        merged,
        start=1,
    ):
        interval[
            "merged_interval_id"
        ] = (
            f"merged-{index:02d}"
        )

        interval[
            "interval_start_meters"
        ] = round(
            interval[
                "interval_start_meters"
            ],
            2,
        )

        interval[
            "interval_end_meters"
        ] = round(
            interval[
                "interval_end_meters"
            ],
            2,
        )

        interval[
            "length_meters"
        ] = round(
            interval[
                "interval_end_meters"
            ]
            - interval[
                "interval_start_meters"
            ],
            2,
        )

        interval[
            "source_count"
        ] = len(
            interval[
                "source_exclusion_ids"
            ]
        )

    return merged


# ============================================================
# Review one side
# ============================================================

def review_side(
    intervals,
    segment_length_meters,
):
    raw_width_sum = round(
        sum(
            interval[
                "estimated_frontage_width_meters"
            ]
            for interval in intervals
        ),
        2,
    )

    clamped_width_sum = round(
        sum(
            interval[
                "clamped_interval_width_meters"
            ]
            for interval in intervals
        ),
        2,
    )

    overlaps = detect_overlaps(
        intervals
    )

    merged_intervals = merge_intervals(
        intervals
    )

    merged_exclusion_length = round(
        sum(
            interval[
                "length_meters"
            ]
            for interval
            in merged_intervals
        ),
        2,
    )

    overlap_removed = max(
        0.0,
        round(
            clamped_width_sum
            - merged_exclusion_length,
            2,
        ),
    )

    usable_after_driveways = round(
        segment_length_meters
        - merged_exclusion_length,
        2,
    )

    clamped_count = sum(
        1
        for interval in intervals
        if interval[
            "was_clamped"
        ]
    )

    return {
        "driveway_count": len(
            intervals
        ),

        "raw_width_sum_meters": (
            raw_width_sum
        ),

        "clamped_width_sum_meters": (
            clamped_width_sum
        ),

        "pairwise_overlap_count": (
            len(overlaps)
        ),

        "overlap_removed_meters": (
            overlap_removed
        ),

        "merged_interval_count": (
            len(merged_intervals)
        ),

        "merged_driveway_exclusion_meters": (
            merged_exclusion_length
        ),

        "usable_curb_after_driveways_meters": (
            usable_after_driveways
        ),

        "clamped_interval_count": (
            clamped_count
        ),

        "overlaps": overlaps,

        "merged_intervals": (
            merged_intervals
        ),
    }


# ============================================================
# Print side review
# ============================================================

def print_side_review(
    side_name,
    geometric_side,
    intervals,
    review,
):
    print(
        f"{side_name} / "
        f"{geometric_side}"
    )

    print(
        "-" * 55
    )

    print(
        f"Driveway intervals:              "
        f"{review['driveway_count']}"
    )

    print(
        f"Raw estimated width sum:         "
        f"{review['raw_width_sum_meters']:.2f} m"
    )

    print(
        f"Clamped interval width sum:      "
        f"{review['clamped_width_sum_meters']:.2f} m"
    )

    print(
        f"Pairwise overlaps detected:      "
        f"{review['pairwise_overlap_count']}"
    )

    print(
        f"Overlap removed:                 "
        f"{review['overlap_removed_meters']:.2f} m"
    )

    print(
        f"Merged driveway intervals:       "
        f"{review['merged_interval_count']}"
    )

    print(
        f"Merged driveway exclusion:       "
        f"{review['merged_driveway_exclusion_meters']:.2f} m"
    )

    print(
        f"Usable curb after driveways only:"
        f" "
        f"{review['usable_curb_after_driveways_meters']:.2f} m"
    )

    print(
        f"Intervals clamped to segment:    "
        f"{review['clamped_interval_count']}"
    )

    print()

    print(
        "INDIVIDUAL INTERVALS"
    )

    print(
        "~~~~~~~~~~~~~~~~~~~~"
    )

    print()

    if not intervals:
        print(
            "None"
        )

    for index, interval in enumerate(
        sorted(
            intervals,
            key=lambda item: (
                item[
                    "interval_start_meters"
                ],
                item[
                    "interval_end_meters"
                ],
            ),
        ),
        start=1,
    ):
        print(
            f"{index}. "
            f"{interval['exclusion_id']}"
        )

        print(
            f"   Position: "
            f"{interval['position_along_segment_meters']:.2f} m"
        )

        print(
            f"   Width:    "
            f"{interval['estimated_frontage_width_meters']:.2f} m"
        )

        print(
            f"   Interval: "
            f"{interval['interval_start_meters']:.2f}"
            f" to "
            f"{interval['interval_end_meters']:.2f} m"
        )

        print(
            f"   Clamped:  "
            f"{interval['was_clamped']}"
        )

    print()

    print(
        "MERGED INTERVALS"
    )

    print(
        "~~~~~~~~~~~~~~~~"
    )

    print()

    if not review[
        "merged_intervals"
    ]:
        print(
            "None"
        )

    for index, interval in enumerate(
        review[
            "merged_intervals"
        ],
        start=1,
    ):
        source_ids = ", ".join(
            interval[
                "source_exclusion_ids"
            ]
        )

        print(
            f"{index}. "
            f"{interval['interval_start_meters']:.2f}"
            f" to "
            f"{interval['interval_end_meters']:.2f} m"
        )

        print(
            f"   Length:  "
            f"{interval['length_meters']:.2f} m"
        )

        print(
            f"   Sources: "
            f"{source_ids}"
        )

    print()

    print(
        "OVERLAPS"
    )

    print(
        "~~~~~~~~"
    )

    print()

    if not review[
        "overlaps"
    ]:
        print(
            "None"
        )

    for index, overlap in enumerate(
        review[
            "overlaps"
        ],
        start=1,
    ):
        print(
            f"{index}. "
            f"{overlap['first_exclusion_id']}"
            f" overlaps "
            f"{overlap['second_exclusion_id']}"
        )

        print(
            f"   Range: "
            f"{overlap['overlap_start_meters']:.2f}"
            f" to "
            f"{overlap['overlap_end_meters']:.2f} m"
        )

        print(
            f"   Length: "
            f"{overlap['overlap_length_meters']:.2f} m"
        )

    print()


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Driveway Interval Reviewer"
    )

    print(
        "========================================="
    )

    print()

    # --------------------------------------------------------
    # Load measurements
    # --------------------------------------------------------

    try:
        data = load_json(
            INPUT_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    street_name = data.get(
        "street_name"
    )

    segment_id = data.get(
        "segment_id"
    )

    restricted_side = data.get(
        "restricted_side"
    )

    segment_length = data.get(
        "segment_length_meters"
    )

    measurements = data.get(
        "measurements",
        [],
    )

    if not isinstance(
        measurements,
        list,
    ):
        print(
            "ERROR: measurements must "
            "be a list."
        )

        return

    errors = []

    warnings = []

    # --------------------------------------------------------
    # Dataset validation
    # --------------------------------------------------------

    if (
        street_name
        != EXPECTED_STREET_NAME
    ):
        add_error(
            errors,
            (
                "Expected street_name "
                "CONWAY ST."
            ),
        )

    if (
        segment_id
        != EXPECTED_SEGMENT_ID
    ):
        add_error(
            errors,
            (
                "Expected segment_id "
                "821528."
            ),
        )

    if (
        restricted_side
        != EXPECTED_RESTRICTED_SIDE
    ):
        add_error(
            errors,
            (
                "Expected restricted_side "
                "EVEN."
            ),
        )

    if not is_number(
        segment_length
    ):
        add_error(
            errors,
            (
                "segment_length_meters "
                "must be numeric."
            ),
        )

    elif abs(
        segment_length
        - EXPECTED_SEGMENT_LENGTH_METERS
    ) > 0.50:
        add_error(
            errors,
            (
                "Segment length does not "
                "match the inspected Conway "
                "geometry."
            ),
        )

    if (
        len(measurements)
        != EXPECTED_MEASUREMENT_COUNT
    ):
        add_error(
            errors,
            (
                "Expected 14 driveway "
                "measurements, found "
                f"{len(measurements)}."
            ),
        )

    # --------------------------------------------------------
    # Build intervals
    # --------------------------------------------------------

    intervals = []

    exclusion_ids = set()

    if is_number(
        segment_length
    ):
        for measurement in measurements:
            exclusion_id = (
                measurement.get(
                    "exclusion_id"
                )
            )

            if exclusion_id in exclusion_ids:
                add_error(
                    errors,
                    (
                        "Duplicate exclusion_id: "
                        f"{exclusion_id}."
                    ),
                )

                continue

            if exclusion_id is not None:
                exclusion_ids.add(
                    exclusion_id
                )

            interval = build_interval(
                measurement=measurement,
                segment_length_meters=(
                    segment_length
                ),
                errors=errors,
            )

            if interval is not None:
                intervals.append(
                    interval
                )

    # --------------------------------------------------------
    # Separate by side
    # --------------------------------------------------------

    odd_intervals = [
        interval
        for interval in intervals
        if (
            interval["parity_side"]
            == "ODD"
        )
    ]

    even_intervals = [
        interval
        for interval in intervals
        if (
            interval["parity_side"]
            == "EVEN"
        )
    ]

    if (
        len(odd_intervals)
        != EXPECTED_ODD_COUNT
    ):
        add_error(
            errors,
            (
                "Expected 8 ODD intervals, "
                f"found {len(odd_intervals)}."
            ),
        )

    if (
        len(even_intervals)
        != EXPECTED_EVEN_COUNT
    ):
        add_error(
            errors,
            (
                "Expected 6 EVEN intervals, "
                f"found {len(even_intervals)}."
            ),
        )

    # --------------------------------------------------------
    # Side reviews
    # --------------------------------------------------------

    if is_number(
        segment_length
    ):
        odd_review = review_side(
            intervals=odd_intervals,
            segment_length_meters=(
                segment_length
            ),
        )

        even_review = review_side(
            intervals=even_intervals,
            segment_length_meters=(
                segment_length
            ),
        )

    else:
        odd_review = {}

        even_review = {}

    # --------------------------------------------------------
    # Warnings
    # --------------------------------------------------------

    for interval in intervals:
        if interval[
            "was_clamped"
        ]:
            add_warning(
                warnings,
                (
                    f"{interval['exclusion_id']}: "
                    "interval was clamped to "
                    "the Conway segment boundary."
                ),
            )

        if (
            interval[
                "review_status"
            ]
            == "REVIEW_REQUIRED"
        ):
            add_warning(
                warnings,
                (
                    f"{interval['exclusion_id']}: "
                    "measurement source marked "
                    "REVIEW_REQUIRED."
                ),
            )

    # --------------------------------------------------------
    # Combined summary
    # --------------------------------------------------------

    combined_raw_width = round(
        odd_review.get(
            "raw_width_sum_meters",
            0.0,
        )
        + even_review.get(
            "raw_width_sum_meters",
            0.0,
        ),
        2,
    )

    combined_merged_exclusion = round(
        odd_review.get(
            "merged_driveway_exclusion_meters",
            0.0,
        )
        + even_review.get(
            "merged_driveway_exclusion_meters",
            0.0,
        ),
        2,
    )

    combined_overlap_removed = round(
        combined_raw_width
        - combined_merged_exclusion,
        2,
    )

    # --------------------------------------------------------
    # Output review dataset
    # --------------------------------------------------------

    output = {
        "dataset_name": (
            "BanReady Conway Driveway Interval Review"
        ),

        "street_name": (
            street_name
        ),

        "segment_id": (
            segment_id
        ),

        "restricted_side": (
            restricted_side
        ),

        "segment_length_meters": (
            segment_length
        ),

        "review_status": (
            "DRIVEWAY_STAGE_ONLY"
        ),

        "inventory_status": (
            "INCOMPLETE"
        ),

        "evidence_status": (
            "ESTIMATED"
        ),

        "methodology": (
            "Each estimated driveway frontage is "
            "represented as an interval centered on "
            "its measured position along the Conway "
            "centerline. Intervals are clamped to the "
            "segment extent and merged by parity side "
            "to prevent double-counting overlapping "
            "driveway exclusions. Results represent "
            "driveway exclusions only and do not "
            "include hydrants, intersections, bus "
            "stops, signs, crosswalks or other curb "
            "restrictions."
        ),

        "summary": {
            "measurement_count": (
                len(measurements)
            ),

            "interval_count": (
                len(intervals)
            ),

            "combined_raw_width_meters": (
                combined_raw_width
            ),

            "combined_merged_driveway_exclusion_meters": (
                combined_merged_exclusion
            ),

            "combined_overlap_removed_meters": (
                combined_overlap_removed
            ),
        },

        "odd_side": {
            "side": "ODD",
            "geometric_side": "LEFT",
            "base_curb_length_meters": (
                segment_length
            ),
            "review": odd_review,
            "intervals": (
                sorted(
                    odd_intervals,
                    key=lambda item: (
                        item[
                            "interval_start_meters"
                        ],
                        item[
                            "interval_end_meters"
                        ],
                    ),
                )
            ),
        },

        "even_side": {
            "side": "EVEN",
            "geometric_side": "RIGHT",
            "base_curb_length_meters": (
                segment_length
            ),
            "review": even_review,
            "intervals": (
                sorted(
                    even_intervals,
                    key=lambda item: (
                        item[
                            "interval_start_meters"
                        ],
                        item[
                            "interval_end_meters"
                        ],
                    ),
                )
            ),
        },

        "warnings": warnings,

        "errors": errors,
    }

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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

    # ========================================================
    # Display report
    # ========================================================

    print("CONWAY SEGMENT")
    print("==============")
    print()

    print(
        f"Street:           "
        f"{street_name}"
    )

    print(
        f"Segment ID:       "
        f"{segment_id}"
    )

    print(
        f"Segment length:   "
        f"{segment_length} m"
    )

    print(
        f"Restricted side:  "
        f"{restricted_side}"
    )

    print()

    print_side_review(
        side_name="ODD",
        geometric_side="LEFT",
        intervals=odd_intervals,
        review=odd_review,
    )

    print_side_review(
        side_name="EVEN",
        geometric_side="RIGHT",
        intervals=even_intervals,
        review=even_review,
    )

    # ========================================================
    # Combined summary
    # ========================================================

    print("COMBINED DRIVEWAY REVIEW")
    print("========================")
    print()

    print(
        f"Raw driveway width sum:       "
        f"{combined_raw_width:.2f} m"
    )

    print(
        f"Merged driveway exclusion:    "
        f"{combined_merged_exclusion:.2f} m"
    )

    print(
        f"Overlap/clamping removed:      "
        f"{combined_overlap_removed:.2f} m"
    )

    print()

    print(
        "Inventory status:             "
        "INCOMPLETE"
    )

    print(
        "Evidence status:              "
        "ESTIMATED"
    )

    print(
        "Review stage:                 "
        "DRIVEWAY_STAGE_ONLY"
    )

    print()

    # ========================================================
    # Consistency checks
    # ========================================================

    checks = []

    checks.append(
        (
            "Street is CONWAY ST",
            street_name
            == EXPECTED_STREET_NAME,
        )
    )

    checks.append(
        (
            "Segment ID is 821528",
            segment_id
            == EXPECTED_SEGMENT_ID,
        )
    )

    checks.append(
        (
            "Restricted side is EVEN",
            restricted_side
            == EXPECTED_RESTRICTED_SIDE,
        )
    )

    checks.append(
        (
            "14 measurements loaded",
            len(measurements)
            == EXPECTED_MEASUREMENT_COUNT,
        )
    )

    checks.append(
        (
            "14 intervals built",
            len(intervals)
            == EXPECTED_MEASUREMENT_COUNT,
        )
    )

    checks.append(
        (
            "8 ODD intervals",
            len(odd_intervals)
            == EXPECTED_ODD_COUNT,
        )
    )

    checks.append(
        (
            "6 EVEN intervals",
            len(even_intervals)
            == EXPECTED_EVEN_COUNT,
        )
    )

    checks.append(
        (
            "ODD exclusion does not exceed curb",
            (
                odd_review.get(
                    "merged_driveway_exclusion_meters",
                    float("inf"),
                )
                <= segment_length
            ),
        )
    )

    checks.append(
        (
            "EVEN exclusion does not exceed curb",
            (
                even_review.get(
                    "merged_driveway_exclusion_meters",
                    float("inf"),
                )
                <= segment_length
            ),
        )
    )

    checks.append(
        (
            "ODD usable curb remains nonnegative",
            (
                odd_review.get(
                    "usable_curb_after_driveways_meters",
                    -1,
                )
                >= 0
            ),
        )
    )

    checks.append(
        (
            "EVEN usable curb remains nonnegative",
            (
                even_review.get(
                    "usable_curb_after_driveways_meters",
                    -1,
                )
                >= 0
            ),
        )
    )

    checks.append(
        (
            "Merged exclusions do not exceed raw sum",
            (
                combined_merged_exclusion
                <= combined_raw_width
                + 0.05
            ),
        )
    )

    print("CONSISTENCY CHECK")
    print("=================")
    print()

    for index, (
        check_name,
        passed,
    ) in enumerate(
        checks,
        start=1,
    ):
        print(
            f"Test {index:02d} - "
            f"{check_name}: "
            f"{'PASS' if passed else 'FAIL'}"
        )

    passed_checks = sum(
        1
        for _, passed in checks
        if passed
    )

    failed_checks = (
        len(checks)
        - passed_checks
    )

    print()

    print("ERRORS")
    print("======")
    print()

    if errors:
        for index, error in enumerate(
            errors,
            start=1,
        ):
            print(
                f"{index}. {error}"
            )
    else:
        print(
            "None"
        )

    print()

    print("WARNINGS")
    print("========")
    print()

    if warnings:
        for index, warning in enumerate(
            warnings,
            start=1,
        ):
            print(
                f"{index}. {warning}"
            )
    else:
        print(
            "None"
        )

    print()

    print(
        "======================================="
    )

    print(
        "BANREADY DRIVEWAY REVIEW SUMMARY"
    )

    print(
        "======================================="
    )

    print()

    print(
        f"Total checks: "
        f"{len(checks)}"
    )

    print(
        f"Passed:       "
        f"{passed_checks}"
    )

    print(
        f"Failed:       "
        f"{failed_checks}"
    )

    print()

    if (
        failed_checks == 0
        and not errors
    ):
        print(
            "DRIVEWAY INTERVAL REVIEW PASSED"
        )
    else:
        print(
            "DRIVEWAY INTERVAL REVIEW FAILED"
        )

    print()

    print(
        "Saved:"
    )

    print(
        OUTPUT_FILE
    )

    print()

    print(
        "IMPORTANT:"
    )

    print(
        "The reported usable curb values account "
        "for estimated driveway exclusions only."
    )

    print()

    print(
        "Do not copy them into the completed Conway "
        "curb inventory until intersection, hydrant, "
        "bus-stop, crosswalk and other restriction "
        "evidence is reviewed."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
