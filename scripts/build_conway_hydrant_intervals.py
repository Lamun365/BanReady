import json
import math
from pathlib import Path


# ============================================================
# Input and output files
# ============================================================

HYDRANT_INSPECTION_FILE = Path(
    "data/research/worcester/"
    "conway_821528_hydrant_inspection.json"
)

DRIVEWAY_REVIEW_FILE = Path(
    "data/research/worcester/"
    "conway_821528_driveway_interval_review.json"
)

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_hydrant_interval_review.json"
)


# ============================================================
# Expected Conway attributes
# ============================================================

EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_SEGMENT_ID = 821528

EXPECTED_RESTRICTED_SIDE = "EVEN"

EXPECTED_SEGMENT_LENGTH_METERS = 253.31


# ============================================================
# Worcester hydrant clearance
#
# Relevant ordinance wording:
#
# "Upon any roadway within ten feet of a fire hydrant."
#
# BanReady models this as ten feet in each direction along
# the applicable curb from the hydrant position.
# ============================================================

FEET_TO_METERS = 0.3048

HYDRANT_CLEARANCE_FEET = 10.0

HYDRANT_CLEARANCE_METERS = (
    HYDRANT_CLEARANCE_FEET
    * FEET_TO_METERS
)


# ============================================================
# Hydrant adjudication
# ============================================================

ACCEPTED_INTERIOR_HYDRANT = "HY4767"

ACCEPTED_BOUNDARY_HYDRANT = "HY4768"

REJECTED_HYDRANT = "HY1449"


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


def save_json(
    path,
    data,
):
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


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
# Hydrant lookup
# ============================================================

def find_hydrant_candidate(
    candidates,
    asset_id,
):
    for candidate in candidates:
        if (
            candidate.get(
                "asset_id"
            )
            == asset_id
        ):
            return candidate

    return None


# ============================================================
# Build hydrant interval
# ============================================================

def build_hydrant_interval(
    candidate,
    segment_length_meters,
    relevance_status,
):
    asset_id = candidate.get(
        "asset_id"
    )

    parity_side = candidate.get(
        "parity_side"
    )

    geometric_side = candidate.get(
        "geometric_side"
    )

    position = candidate.get(
        "position_along_segment_meters"
    )

    if not is_number(
        position
    ):
        raise ValueError(
            f"{asset_id}: invalid segment position."
        )

    raw_start = (
        position
        - HYDRANT_CLEARANCE_METERS
    )

    raw_end = (
        position
        + HYDRANT_CLEARANCE_METERS
    )

    interval_start = max(
        0.0,
        raw_start,
    )

    interval_end = min(
        segment_length_meters,
        raw_end,
    )

    interval_length = max(
        0.0,
        interval_end
        - interval_start,
    )

    was_clipped = (
        abs(
            raw_start
            - interval_start
        )
        > 0.001
        or abs(
            raw_end
            - interval_end
        )
        > 0.001
    )

    if was_clipped:
        interval_status = (
            "BOUNDARY_CLIPPED"
        )
    else:
        interval_status = (
            "INTERIOR"
        )

    return {
        "exclusion_id": (
            f"{parity_side.lower()}-"
            f"hydrant-{asset_id}"
        ),

        "exclusion_type": (
            "FIRE_HYDRANT"
        ),

        "asset_id": (
            asset_id
        ),

        "object_id": candidate.get(
            "object_id"
        ),

        "global_id": candidate.get(
            "global_id"
        ),

        "parity_side": (
            parity_side
        ),

        "geometric_side": (
            geometric_side
        ),

        "gis_street_name": candidate.get(
            "street_name"
        ),

        "hydrant_location": candidate.get(
            "hydrant_location"
        ),

        "nearest_house": candidate.get(
            "nearest_house"
        ),

        "position_along_segment_meters": (
            round(
                position,
                2,
            )
        ),

        "distance_to_centerline_meters": (
            candidate.get(
                "distance_to_centerline_meters"
            )
        ),

        "clearance_each_direction_feet": (
            HYDRANT_CLEARANCE_FEET
        ),

        "clearance_each_direction_meters": (
            round(
                HYDRANT_CLEARANCE_METERS,
                3,
            )
        ),

        "raw_interval_start_meters": (
            round(
                raw_start,
                3,
            )
        ),

        "raw_interval_end_meters": (
            round(
                raw_end,
                3,
            )
        ),

        "interval_start_meters": (
            round(
                interval_start,
                3,
            )
        ),

        "interval_end_meters": (
            round(
                interval_end,
                3,
            )
        ),

        "length_meters": (
            round(
                interval_length,
                3,
            )
        ),

        "was_clipped": (
            was_clipped
        ),

        "interval_status": (
            interval_status
        ),

        "relevance_status": (
            relevance_status
        ),

        "location_evidence_status": (
            "VERIFIED_GIS"
        ),

        "legal_clearance_status": (
            "VERIFIED_ORDINANCE"
        ),

        "interval_evidence_status": (
            "GIS_DERIVED"
        ),

        "source_name": (
            "City of Worcester Hydrant GIS "
            "and Worcester Revised Ordinances"
        ),

        "methodology": (
            "The official hydrant point is projected "
            "onto Conway segment 821528. BanReady "
            "applies the Worcester parking prohibition "
            "within ten feet of a fire hydrant as "
            "3.048 meters in each direction along the "
            "applicable curb. Intervals extending past "
            "the segment boundary are clipped."
        ),
    }


# ============================================================
# Normalize driveway intervals
# ============================================================

def get_driveway_intervals(
    driveway_review,
    side_key,
):
    side_data = driveway_review.get(
        side_key,
        {},
    )

    intervals = side_data.get(
        "intervals",
        [],
    )

    normalized = []

    for interval in intervals:
        start = interval.get(
            "interval_start_meters"
        )

        end = interval.get(
            "interval_end_meters"
        )

        if not (
            is_number(start)
            and is_number(end)
            and end >= start
        ):
            continue

        normalized.append(
            {
                "exclusion_id": interval.get(
                    "exclusion_id"
                ),

                "exclusion_type": (
                    "DRIVEWAY"
                ),

                "parity_side": interval.get(
                    "parity_side"
                ),

                "interval_start_meters": (
                    float(start)
                ),

                "interval_end_meters": (
                    float(end)
                ),

                "length_meters": (
                    round(
                        end - start,
                        3,
                    )
                ),

                "evidence_status": (
                    "ESTIMATED"
                ),
            }
        )

    return normalized


# ============================================================
# Merge intervals
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
        start = float(
            interval[
                "interval_start_meters"
            ]
        )

        end = float(
            interval[
                "interval_end_meters"
            ]
        )

        source = {
            "exclusion_id": interval.get(
                "exclusion_id"
            ),

            "exclusion_type": interval.get(
                "exclusion_type"
            ),
        }

        if not merged:
            merged.append(
                {
                    "interval_start_meters": (
                        start
                    ),

                    "interval_end_meters": (
                        end
                    ),

                    "sources": [
                        source
                    ],
                }
            )

            continue

        current = merged[-1]

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
                "sources"
            ].append(
                source
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

                    "sources": [
                        source
                    ],
                }
            )

    for index, interval in enumerate(
        merged,
        start=1,
    ):
        start = interval[
            "interval_start_meters"
        ]

        end = interval[
            "interval_end_meters"
        ]

        interval[
            "merged_interval_id"
        ] = (
            f"merged-{index:02d}"
        )

        interval[
            "interval_start_meters"
        ] = round(
            start,
            3,
        )

        interval[
            "interval_end_meters"
        ] = round(
            end,
            3,
        )

        interval[
            "length_meters"
        ] = round(
            end - start,
            3,
        )

        interval[
            "source_count"
        ] = len(
            interval[
                "sources"
            ]
        )

    return merged


# ============================================================
# Overlap detection
# ============================================================

def calculate_overlap(
    first_interval,
    second_interval,
):
    overlap_start = max(
        first_interval[
            "interval_start_meters"
        ],
        second_interval[
            "interval_start_meters"
        ],
    )

    overlap_end = min(
        first_interval[
            "interval_end_meters"
        ],
        second_interval[
            "interval_end_meters"
        ],
    )

    overlap_length = max(
        0.0,
        overlap_end
        - overlap_start,
    )

    return {
        "overlap_start_meters": (
            round(
                overlap_start,
                3,
            )
        ),

        "overlap_end_meters": (
            round(
                overlap_end,
                3,
            )
        ),

        "overlap_length_meters": (
            round(
                overlap_length,
                3,
            )
        ),
    }


# ============================================================
# Side summary
# ============================================================

def build_side_summary(
    side,
    segment_length_meters,
    driveway_intervals,
    hydrant_intervals,
):
    combined_intervals = (
        driveway_intervals
        + hydrant_intervals
    )

    driveway_length = round(
        sum(
            interval[
                "length_meters"
            ]
            for interval
            in driveway_intervals
        ),
        3,
    )

    hydrant_length = round(
        sum(
            interval[
                "length_meters"
            ]
            for interval
            in hydrant_intervals
        ),
        3,
    )

    raw_combined_length = round(
        driveway_length
        + hydrant_length,
        3,
    )

    merged_intervals = (
        merge_intervals(
            combined_intervals
        )
    )

    merged_exclusion_length = round(
        sum(
            interval[
                "length_meters"
            ]
            for interval
            in merged_intervals
        ),
        3,
    )

    overlap_removed = max(
        0.0,
        round(
            raw_combined_length
            - merged_exclusion_length,
            3,
        ),
    )

    provisional_remaining = round(
        segment_length_meters
        - merged_exclusion_length,
        3,
    )

    return {
        "side": side,

        "base_curb_length_meters": (
            segment_length_meters
        ),

        "driveway_interval_count": (
            len(
                driveway_intervals
            )
        ),

        "hydrant_interval_count": (
            len(
                hydrant_intervals
            )
        ),

        "driveway_exclusion_meters": (
            driveway_length
        ),

        "raw_hydrant_exclusion_meters": (
            hydrant_length
        ),

        "raw_combined_exclusion_meters": (
            raw_combined_length
        ),

        "overlap_removed_meters": (
            overlap_removed
        ),

        "merged_exclusion_meters": (
            merged_exclusion_length
        ),

        "provisional_remaining_curb_meters": (
            provisional_remaining
        ),

        "inventory_status": (
            "INCOMPLETE"
        ),

        "evidence_status": (
            "ESTIMATED"
        ),

        "merged_intervals": (
            merged_intervals
        ),
    }


# ============================================================
# Terminal display
# ============================================================

def print_hydrant_interval(
    interval,
):
    print(
        f"{interval['asset_id']}"
    )

    print(
        "-" * 45
    )

    print(
        f"Side:               "
        f"{interval['parity_side']} / "
        f"{interval['geometric_side']}"
    )

    print(
        f"Position:           "
        f"{interval['position_along_segment_meters']:.2f} m"
    )

    print(
        f"Raw interval:       "
        f"{interval['raw_interval_start_meters']:.3f}"
        f" to "
        f"{interval['raw_interval_end_meters']:.3f} m"
    )

    print(
        f"Applied interval:   "
        f"{interval['interval_start_meters']:.3f}"
        f" to "
        f"{interval['interval_end_meters']:.3f} m"
    )

    print(
        f"Applied length:     "
        f"{interval['length_meters']:.3f} m"
    )

    print(
        f"Boundary clipped:   "
        f"{interval['was_clipped']}"
    )

    print(
        f"Interval status:    "
        f"{interval['interval_status']}"
    )

    print(
        f"Relevance status:   "
        f"{interval['relevance_status']}"
    )

    print()


def print_side_summary(
    summary,
):
    print(
        f"{summary['side']} SIDE"
    )

    print(
        "-" * 45
    )

    print(
        f"Base curb length:         "
        f"{summary['base_curb_length_meters']:.2f} m"
    )

    print(
        f"Driveway intervals:       "
        f"{summary['driveway_interval_count']}"
    )

    print(
        f"Hydrant intervals:        "
        f"{summary['hydrant_interval_count']}"
    )

    print(
        f"Driveway exclusion:       "
        f"{summary['driveway_exclusion_meters']:.3f} m"
    )

    print(
        f"Raw hydrant exclusion:    "
        f"{summary['raw_hydrant_exclusion_meters']:.3f} m"
    )

    print(
        f"Raw combined exclusion:   "
        f"{summary['raw_combined_exclusion_meters']:.3f} m"
    )

    print(
        f"Overlap removed:          "
        f"{summary['overlap_removed_meters']:.3f} m"
    )

    print(
        f"Merged exclusion:         "
        f"{summary['merged_exclusion_meters']:.3f} m"
    )

    print(
        f"Provisional curb remaining:"
        f" "
        f"{summary['provisional_remaining_curb_meters']:.3f} m"
    )

    print()


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Hydrant Interval Builder"
    )

    print(
        "======================================="
    )

    print()

    try:
        hydrant_data = load_json(
            HYDRANT_INSPECTION_FILE
        )

        driveway_data = load_json(
            DRIVEWAY_REVIEW_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    errors = []

    warnings = []

    # --------------------------------------------------------
    # Dataset identity
    # --------------------------------------------------------

    street_name = hydrant_data.get(
        "street_name"
    )

    segment_id = hydrant_data.get(
        "segment_id"
    )

    restricted_side = hydrant_data.get(
        "restricted_side"
    )

    segment_length = hydrant_data.get(
        "segment_length_meters"
    )

    if (
        street_name
        != EXPECTED_STREET_NAME
    ):
        add_error(
            errors,
            "Expected street_name CONWAY ST.",
        )

    if (
        segment_id
        != EXPECTED_SEGMENT_ID
    ):
        add_error(
            errors,
            "Expected segment_id 821528.",
        )

    if (
        restricted_side
        != EXPECTED_RESTRICTED_SIDE
    ):
        add_error(
            errors,
            "Expected restricted_side EVEN.",
        )

    if not is_number(
        segment_length
    ):
        add_error(
            errors,
            "Invalid Conway segment length.",
        )

    elif abs(
        segment_length
        - EXPECTED_SEGMENT_LENGTH_METERS
    ) > 0.50:
        add_error(
            errors,
            (
                "Conway segment length does not "
                "match 253.31 meters."
            ),
        )

    if errors:
        print(
            "INPUT VALIDATION FAILED"
        )

        for error in errors:
            print(
                f"- {error}"
            )

        return

    # --------------------------------------------------------
    # Locate hydrants
    # --------------------------------------------------------

    candidates = hydrant_data.get(
        "candidates",
        [],
    )

    hy1449 = find_hydrant_candidate(
        candidates,
        REJECTED_HYDRANT,
    )

    hy4767 = find_hydrant_candidate(
        candidates,
        ACCEPTED_INTERIOR_HYDRANT,
    )

    hy4768 = find_hydrant_candidate(
        candidates,
        ACCEPTED_BOUNDARY_HYDRANT,
    )

    if hy4767 is None:
        add_error(
            errors,
            "Interior hydrant HY4767 is missing.",
        )

    if hy4768 is None:
        add_error(
            errors,
            "Boundary hydrant HY4768 is missing.",
        )

    if hy1449 is None:
        add_warning(
            warnings,
            "Rejected hydrant HY1449 was not found.",
        )

    if errors:
        print(
            "HYDRANT LOOKUP FAILED"
        )

        for error in errors:
            print(
                f"- {error}"
            )

        return

    # --------------------------------------------------------
    # Build accepted hydrant intervals
    # --------------------------------------------------------

    hy4767_interval = (
        build_hydrant_interval(
            candidate=hy4767,
            segment_length_meters=(
                segment_length
            ),
            relevance_status=(
                "ACCEPTED_INTERIOR"
            ),
        )
    )

    hy4768_interval = (
        build_hydrant_interval(
            candidate=hy4768,
            segment_length_meters=(
                segment_length
            ),
            relevance_status=(
                "ACCEPTED_BOUNDARY_CLIPPED"
            ),
        )
    )

    accepted_hydrant_intervals = [
        hy4767_interval,
        hy4768_interval,
    ]

    rejected_hydrants = []

    if hy1449 is not None:
        rejected_hydrants.append(
            {
                "asset_id": (
                    REJECTED_HYDRANT
                ),

                "gis_street_name": (
                    hy1449.get(
                        "street_name"
                    )
                ),

                "position_along_segment_meters": (
                    hy1449.get(
                        "position_along_segment_meters"
                    )
                ),

                "distance_to_centerline_meters": (
                    hy1449.get(
                        "distance_to_centerline_meters"
                    )
                ),

                "decision": (
                    "REJECTED_FROM_CONWAY_INTERIOR"
                ),

                "reason": (
                    "Official GIS street name is "
                    "GREENWOOD ST and the point projects "
                    "to the Conway start boundary. Current "
                    "evidence does not establish a Conway "
                    "curb exclusion."
                ),
            }
        )

    # --------------------------------------------------------
    # Load driveway intervals
    # --------------------------------------------------------

    odd_driveway_intervals = (
        get_driveway_intervals(
            driveway_review=driveway_data,
            side_key="odd_side",
        )
    )

    even_driveway_intervals = (
        get_driveway_intervals(
            driveway_review=driveway_data,
            side_key="even_side",
        )
    )

    odd_hydrant_intervals = [
        interval
        for interval
        in accepted_hydrant_intervals
        if interval[
            "parity_side"
        ] == "ODD"
    ]

    even_hydrant_intervals = [
        interval
        for interval
        in accepted_hydrant_intervals
        if interval[
            "parity_side"
        ] == "EVEN"
    ]

    # --------------------------------------------------------
    # Explicit HY4768 / driveway overlap
    # --------------------------------------------------------

    boundary_driveway = next(
        (
            interval
            for interval
            in even_driveway_intervals
            if interval.get(
                "exclusion_id"
            )
            == "even-driveway-30570"
        ),
        None,
    )

    boundary_overlap = None

    if boundary_driveway is not None:
        boundary_overlap = (
            calculate_overlap(
                boundary_driveway,
                hy4768_interval,
            )
        )

    else:
        add_warning(
            warnings,
            (
                "Boundary driveway 30570 was not "
                "found for overlap review."
            ),
        )

    # --------------------------------------------------------
    # Build side summaries
    # --------------------------------------------------------

    odd_summary = build_side_summary(
        side="ODD",
        segment_length_meters=(
            segment_length
        ),
        driveway_intervals=(
            odd_driveway_intervals
        ),
        hydrant_intervals=(
            odd_hydrant_intervals
        ),
    )

    even_summary = build_side_summary(
        side="EVEN",
        segment_length_meters=(
            segment_length
        ),
        driveway_intervals=(
            even_driveway_intervals
        ),
        hydrant_intervals=(
            even_hydrant_intervals
        ),
    )

    # --------------------------------------------------------
    # Save output
    # --------------------------------------------------------

    output = {
        "dataset_name": (
            "BanReady Conway Hydrant Interval Review"
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

        "inventory_status": (
            "INCOMPLETE"
        ),

        "review_stage": (
            "DRIVEWAY_AND_HYDRANT_STAGE"
        ),

        "clearance_rule": {
            "distance_each_direction_feet": (
                HYDRANT_CLEARANCE_FEET
            ),

            "distance_each_direction_meters": (
                round(
                    HYDRANT_CLEARANCE_METERS,
                    3,
                )
            ),

            "unclipped_total_interval_meters": (
                round(
                    HYDRANT_CLEARANCE_METERS
                    * 2.0,
                    3,
                )
            ),

            "ordinance_text": (
                "Upon any roadway within ten feet "
                "of a fire hydrant."
            ),

            "evidence_status": (
                "VERIFIED_ORDINANCE"
            ),
        },

        "accepted_hydrant_intervals": (
            accepted_hydrant_intervals
        ),

        "rejected_hydrants": (
            rejected_hydrants
        ),

        "boundary_overlap_review": {
            "hydrant_asset_id": (
                ACCEPTED_BOUNDARY_HYDRANT
            ),

            "driveway_exclusion_id": (
                "even-driveway-30570"
            ),

            "overlap": (
                boundary_overlap
            ),
        },

        "odd_side": (
            odd_summary
        ),

        "even_side": (
            even_summary
        ),

        "limitations": [
            (
                "The review includes driveways and "
                "accepted hydrant intervals only."
            ),
            (
                "Bus stops, crosswalks, signed "
                "restrictions and other curb exclusions "
                "have not yet been incorporated."
            ),
            (
                "The Conway curb inventory therefore "
                "remains INCOMPLETE."
            ),
        ],

        "warnings": (
            warnings
        ),

        "errors": (
            errors
        ),
    }

    save_json(
        OUTPUT_FILE,
        output,
    )

    # ========================================================
    # Display result
    # ========================================================

    print("CLEARANCE RULE")
    print("==============")
    print()

    print(
        f"Each direction: "
        f"{HYDRANT_CLEARANCE_FEET:.1f} ft"
    )

    print(
        f"Each direction: "
        f"{HYDRANT_CLEARANCE_METERS:.3f} m"
    )

    print(
        f"Full interval:  "
        f"{HYDRANT_CLEARANCE_METERS * 2.0:.3f} m"
    )

    print()

    print("ACCEPTED HYDRANT INTERVALS")
    print("==========================")
    print()

    print_hydrant_interval(
        hy4767_interval
    )

    print_hydrant_interval(
        hy4768_interval
    )

    print("REJECTED HYDRANTS")
    print("=================")
    print()

    if rejected_hydrants:
        for rejected in (
            rejected_hydrants
        ):
            print(
                f"{rejected['asset_id']}: "
                f"{rejected['decision']}"
            )

            print(
                f"Reason: "
                f"{rejected['reason']}"
            )

            print()
    else:
        print(
            "None"
        )

        print()

    print("BOUNDARY OVERLAP")
    print("================")
    print()

    if boundary_overlap is not None:
        print(
            f"HY4768 and driveway 30570:"
        )

        print(
            f"Overlap start:  "
            f"{boundary_overlap['overlap_start_meters']:.3f} m"
        )

        print(
            f"Overlap end:    "
            f"{boundary_overlap['overlap_end_meters']:.3f} m"
        )

        print(
            f"Overlap length: "
            f"{boundary_overlap['overlap_length_meters']:.3f} m"
        )

    else:
        print(
            "Not calculated"
        )

    print()

    print_side_summary(
        odd_summary
    )

    print_side_summary(
        even_summary
    )

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
            "Hydrant clearance is 3.048 m",
            abs(
                HYDRANT_CLEARANCE_METERS
                - 3.048
            )
            < 0.0001,
        )
    )

    checks.append(
        (
            "HY4767 accepted as interior",
            (
                hy4767_interval[
                    "interval_status"
                ]
                == "INTERIOR"
                and not hy4767_interval[
                    "was_clipped"
                ]
            ),
        )
    )

    checks.append(
        (
            "HY4768 boundary clipped",
            (
                hy4768_interval[
                    "interval_status"
                ]
                == "BOUNDARY_CLIPPED"
                and hy4768_interval[
                    "was_clipped"
                ]
            ),
        )
    )

    checks.append(
        (
            "HY1449 rejected",
            (
                len(
                    rejected_hydrants
                )
                == 1
            ),
        )
    )

    checks.append(
        (
            "No ODD hydrant intervals",
            (
                len(
                    odd_hydrant_intervals
                )
                == 0
            ),
        )
    )

    checks.append(
        (
            "Two EVEN hydrant intervals",
            (
                len(
                    even_hydrant_intervals
                )
                == 2
            ),
        )
    )

    checks.append(
        (
            "Boundary overlap detected",
            (
                boundary_overlap
                is not None
                and boundary_overlap[
                    "overlap_length_meters"
                ]
                > 0
            ),
        )
    )

    checks.append(
        (
            "ODD curb remains nonnegative",
            (
                odd_summary[
                    "provisional_remaining_curb_meters"
                ]
                >= 0
            ),
        )
    )

    checks.append(
        (
            "EVEN curb remains nonnegative",
            (
                even_summary[
                    "provisional_remaining_curb_meters"
                ]
                >= 0
            ),
        )
    )

    checks.append(
        (
            "Inventory remains INCOMPLETE",
            (
                output[
                    "inventory_status"
                ]
                == "INCOMPLETE"
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
        for _, passed
        in checks
        if passed
    )

    failed_checks = (
        len(checks)
        - passed_checks
    )

    print()
    print(
        "======================================="
    )

    print(
        "BANREADY HYDRANT INTERVAL SUMMARY"
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
            "HYDRANT INTERVAL BUILD PASSED"
        )
    else:
        print(
            "HYDRANT INTERVAL BUILD FAILED"
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
        "The provisional curb remainder includes "
        "driveway and hydrant exclusions only."
    )

    print()

    print(
        "The Conway curb inventory remains "
        "INCOMPLETE until the remaining curb "
        "restriction categories are reviewed."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
