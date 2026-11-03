import json
import math
from pathlib import Path


# ============================================================
# Input and output files
# ============================================================

SHORTFALL_FILE = Path(
    "data/research/worcester/"
    "conway_821528_shortfall_result.json"
)

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_matching_result.json"
)


# ============================================================
# Expected Conway values
# ============================================================

EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_SEGMENT_ID = 821528

EXPECTED_ANALYSIS_TYPE = (
    "SYNTHETIC_DEMAND_PROOF_OF_CONCEPT"
)

EXPECTED_RESULT_STATUS = (
    "PROVISIONAL_ESTIMATED"
)

EXPECTED_CENTRAL_SHORTFALL = 6


# ============================================================
# Destination evidence statuses
# ============================================================

VERIFIED_IDENTITY = "VERIFIED_IDENTITY"

SYNTHETIC_CAPACITY = "SYNTHETIC_SCENARIO"

UNKNOWN_LIVE_AVAILABILITY = (
    "UNKNOWN_LIVE_AVAILABILITY"
)


# ============================================================
# Synthetic relocation scenario
#
# IMPORTANT:
#
# The capacities below are synthetic demonstration values.
# They are not measured, verified or live capacities.
#
# The purpose is to demonstrate the capacity-constrained
# allocation algorithm before real destination availability
# is collected.
# ============================================================

DESTINATIONS = [
    {
        "destination_id": (
            "scenario-nearby-street-001"
        ),

        "name": (
            "Nearby Legal Street Segment"
        ),

        "destination_type": (
            "STREET"
        ),

        "distance_km": 0.30,

        "modeled_available_capacity": 2,

        "identity_status": (
            "SYNTHETIC_SCENARIO"
        ),

        "capacity_status": (
            SYNTHETIC_CAPACITY
        ),

        "availability_status": (
            "SYNTHETIC_SCENARIO"
        ),

        "priority": 1,

        "notes": (
            "Synthetic nearby-street destination "
            "used only to demonstrate the matching "
            "algorithm."
        ),
    },

    {
        "destination_id": (
            "scenario-partner-lot-001"
        ),

        "name": (
            "Partner Lot Scenario"
        ),

        "destination_type": (
            "PARTNER_LOT"
        ),

        "distance_km": 0.60,

        "modeled_available_capacity": 3,

        "identity_status": (
            "SYNTHETIC_SCENARIO"
        ),

        "capacity_status": (
            SYNTHETIC_CAPACITY
        ),

        "availability_status": (
            "SYNTHETIC_SCENARIO"
        ),

        "priority": 2,

        "notes": (
            "Synthetic partner-lot capacity used "
            "only to demonstrate constrained vehicle "
            "allocation. No real partnership or live "
            "availability is implied."
        ),
    },

    {
        "destination_id": (
            "scenario-municipal-garage-001"
        ),

        "name": (
            "Municipal Garage Scenario"
        ),

        "destination_type": (
            "MUNICIPAL_GARAGE"
        ),

        "distance_km": 1.20,

        "modeled_available_capacity": 4,

        "identity_status": (
            VERIFIED_IDENTITY
        ),

        "capacity_status": (
            SYNTHETIC_CAPACITY
        ),

        "availability_status": (
            UNKNOWN_LIVE_AVAILABILITY
        ),

        "priority": 3,

        "notes": (
            "The municipal-garage destination type "
            "is grounded in BanReady's verified "
            "Worcester destination research, but the "
            "four-space availability value is entirely "
            "synthetic for this demonstration."
        ),
    },
]


# ============================================================
# Helpers
# ============================================================

def is_number(
    value,
):
    if isinstance(
        value,
        bool,
    ):
        return False

    if not isinstance(
        value,
        (int, float),
    ):
        return False

    return math.isfinite(
        float(value)
    )


def is_non_empty_string(
    value,
):
    return (
        isinstance(
            value,
            str,
        )
        and value.strip()
        != ""
    )


def load_json(
    path,
):
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
            return json.load(
                file
            )

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
# Validate shortfall input
# ============================================================

def validate_shortfall_result(
    data,
    errors,
):
    street_name = str(
        data.get(
            "street_name"
        )
        or ""
    ).strip().upper()

    segment_id = data.get(
        "segment_id"
    )

    analysis_type = str(
        data.get(
            "analysis_type"
        )
        or ""
    ).strip().upper()

    result_status = str(
        data.get(
            "result_status"
        )
        or ""
    ).strip().upper()

    demand = data.get(
        "demand",
        {},
    )

    central_result = data.get(
        "central_result",
        {},
    )

    if (
        street_name
        != EXPECTED_STREET_NAME
    ):
        add_error(
            errors,
            (
                "Shortfall result must "
                "reference CONWAY ST."
            ),
        )

    if (
        segment_id
        != EXPECTED_SEGMENT_ID
    ):
        add_error(
            errors,
            (
                "Shortfall result must "
                "reference segment 821528."
            ),
        )

    if (
        analysis_type
        != EXPECTED_ANALYSIS_TYPE
    ):
        add_error(
            errors,
            (
                "Expected synthetic-demand "
                "proof-of-concept analysis."
            ),
        )

    if (
        result_status
        != EXPECTED_RESULT_STATUS
    ):
        add_error(
            errors,
            (
                "Shortfall result must remain "
                "PROVISIONAL_ESTIMATED."
            ),
        )

    collection_method = str(
        demand.get(
            "collection_method"
        )
        or ""
    ).strip().upper()

    evidence_status = str(
        demand.get(
            "evidence_status"
        )
        or ""
    ).strip().upper()

    if (
        collection_method
        != "SYNTHETIC_SCENARIO"
    ):
        add_error(
            errors,
            (
                "Demand must be labeled "
                "SYNTHETIC_SCENARIO."
            ),
        )

    if evidence_status == "OBSERVED":
        add_error(
            errors,
            (
                "Synthetic demand must not "
                "be labeled OBSERVED."
            ),
        )

    shortfall = central_result.get(
        "direct_shortfall"
    )

    if (
        not isinstance(
            shortfall,
            int,
        )
        or isinstance(
            shortfall,
            bool,
        )
    ):
        add_error(
            errors,
            (
                "Central shortfall must be "
                "an integer."
            ),
        )

    elif shortfall < 0:
        add_error(
            errors,
            (
                "Central shortfall cannot "
                "be negative."
            ),
        )

    elif (
        shortfall
        != EXPECTED_CENTRAL_SHORTFALL
    ):
        add_error(
            errors,
            (
                "Expected central Conway "
                "shortfall of 6 vehicles."
            ),
        )

    return {
        "street_name": (
            street_name
        ),

        "segment_id": (
            segment_id
        ),

        "analysis_type": (
            analysis_type
        ),

        "result_status": (
            result_status
        ),

        "demand_collection_method": (
            collection_method
        ),

        "demand_evidence_status": (
            evidence_status
        ),

        "total_demand": (
            central_result.get(
                "total_demand"
            )
        ),

        "vehicles_initially_moving": (
            central_result.get(
                "vehicles_on_restricted_side"
            )
        ),

        "absorbed_on_remaining_side": (
            central_result.get(
                "absorbed_on_remaining_odd_side"
            )
        ),

        "shortfall_vehicles": (
            shortfall
        ),

        "space_length_assumption_meters": (
            central_result.get(
                "space_length_assumption_meters"
            )
        ),

        "estimated_ban_supply": (
            central_result.get(
                "total_ban_capacity"
            )
        ),
    }


# ============================================================
# Validate destination scenarios
# ============================================================

def validate_destinations(
    destinations,
    errors,
):
    destination_ids = set()

    for index, destination in enumerate(
        destinations,
        start=1,
    ):
        destination_id = destination.get(
            "destination_id"
        )

        name = destination.get(
            "name"
        )

        distance_km = destination.get(
            "distance_km"
        )

        capacity = destination.get(
            "modeled_available_capacity"
        )

        capacity_status = destination.get(
            "capacity_status"
        )

        priority = destination.get(
            "priority"
        )

        if not is_non_empty_string(
            destination_id
        ):
            add_error(
                errors,
                (
                    f"Destination {index} has "
                    "no destination_id."
                ),
            )

        elif (
            destination_id
            in destination_ids
        ):
            add_error(
                errors,
                (
                    "Duplicate destination_id: "
                    f"{destination_id}."
                ),
            )

        else:
            destination_ids.add(
                destination_id
            )

        if not is_non_empty_string(
            name
        ):
            add_error(
                errors,
                (
                    f"Destination {index} has "
                    "no name."
                ),
            )

        if not is_number(
            distance_km
        ):
            add_error(
                errors,
                (
                    f"{destination_id}: "
                    "distance_km must be numeric."
                ),
            )

        elif distance_km < 0:
            add_error(
                errors,
                (
                    f"{destination_id}: "
                    "distance_km cannot be negative."
                ),
            )

        if (
            not isinstance(
                capacity,
                int,
            )
            or isinstance(
                capacity,
                bool,
            )
        ):
            add_error(
                errors,
                (
                    f"{destination_id}: modeled "
                    "capacity must be an integer."
                ),
            )

        elif capacity < 0:
            add_error(
                errors,
                (
                    f"{destination_id}: modeled "
                    "capacity cannot be negative."
                ),
            )

        if (
            capacity_status
            != SYNTHETIC_CAPACITY
        ):
            add_error(
                errors,
                (
                    f"{destination_id}: scenario "
                    "capacity must be explicitly "
                    "labeled SYNTHETIC_SCENARIO."
                ),
            )

        if (
            not isinstance(
                priority,
                int,
            )
            or isinstance(
                priority,
                bool,
            )
            or priority <= 0
        ):
            add_error(
                errors,
                (
                    f"{destination_id}: priority "
                    "must be a positive integer."
                ),
            )


# ============================================================
# Capacity-aware greedy allocation
# ============================================================

def allocate_vehicles(
    shortfall_vehicles,
    destinations,
):
    """
    Allocate displaced vehicles across modeled destinations.

    Destinations are sorted by:
    1. Priority
    2. Distance
    3. Name

    The algorithm never assigns more vehicles than the
    destination's modeled available capacity.
    """

    remaining_vehicles = (
        shortfall_vehicles
    )

    ordered_destinations = sorted(
        destinations,
        key=lambda item: (
            item[
                "priority"
            ],
            item[
                "distance_km"
            ],
            item[
                "name"
            ],
        ),
    )

    allocations = []

    total_walking_distance_km = 0.0

    for destination in (
        ordered_destinations
    ):
        capacity = destination[
            "modeled_available_capacity"
        ]

        allocated = min(
            remaining_vehicles,
            capacity,
        )

        remaining_capacity = (
            capacity
            - allocated
        )

        allocation_distance = (
            allocated
            * destination[
                "distance_km"
            ]
        )

        total_walking_distance_km += (
            allocation_distance
        )

        allocations.append(
            {
                "destination_id": (
                    destination[
                        "destination_id"
                    ]
                ),

                "name": (
                    destination[
                        "name"
                    ]
                ),

                "destination_type": (
                    destination[
                        "destination_type"
                    ]
                ),

                "priority": (
                    destination[
                        "priority"
                    ]
                ),

                "distance_km": (
                    destination[
                        "distance_km"
                    ]
                ),

                "modeled_available_capacity": (
                    capacity
                ),

                "allocated_vehicles": (
                    allocated
                ),

                "remaining_capacity": (
                    remaining_capacity
                ),

                "capacity_utilization": (
                    round(
                        (
                            allocated
                            / capacity
                        )
                        if capacity > 0
                        else 0.0,
                        3,
                    )
                ),

                "allocation_distance_km": (
                    round(
                        allocation_distance,
                        3,
                    )
                ),

                "identity_status": (
                    destination[
                        "identity_status"
                    ]
                ),

                "capacity_status": (
                    destination[
                        "capacity_status"
                    ]
                ),

                "availability_status": (
                    destination[
                        "availability_status"
                    ]
                ),

                "notes": (
                    destination[
                        "notes"
                    ]
                ),
            }
        )

        remaining_vehicles -= (
            allocated
        )

        if remaining_vehicles <= 0:
            remaining_vehicles = 0
            break

    # --------------------------------------------------------
    # Include unused destinations in the output so the
    # allocation result remains fully auditable.
    # --------------------------------------------------------

    allocated_ids = {
        allocation[
            "destination_id"
        ]
        for allocation in allocations
    }

    for destination in (
        ordered_destinations
    ):
        if (
            destination[
                "destination_id"
            ]
            in allocated_ids
        ):
            continue

        capacity = destination[
            "modeled_available_capacity"
        ]

        allocations.append(
            {
                "destination_id": (
                    destination[
                        "destination_id"
                    ]
                ),

                "name": (
                    destination[
                        "name"
                    ]
                ),

                "destination_type": (
                    destination[
                        "destination_type"
                    ]
                ),

                "priority": (
                    destination[
                        "priority"
                    ]
                ),

                "distance_km": (
                    destination[
                        "distance_km"
                    ]
                ),

                "modeled_available_capacity": (
                    capacity
                ),

                "allocated_vehicles": 0,

                "remaining_capacity": (
                    capacity
                ),

                "capacity_utilization": 0.0,

                "allocation_distance_km": 0.0,

                "identity_status": (
                    destination[
                        "identity_status"
                    ]
                ),

                "capacity_status": (
                    destination[
                        "capacity_status"
                    ]
                ),

                "availability_status": (
                    destination[
                        "availability_status"
                    ]
                ),

                "notes": (
                    destination[
                        "notes"
                    ]
                ),
            }
        )

    total_allocated = sum(
        allocation[
            "allocated_vehicles"
        ]
        for allocation in allocations
    )

    total_scenario_capacity = sum(
        allocation[
            "modeled_available_capacity"
        ]
        for allocation in allocations
    )

    total_remaining_capacity = sum(
        allocation[
            "remaining_capacity"
        ]
        for allocation in allocations
    )

    average_distance_km = (
        total_walking_distance_km
        / total_allocated
        if total_allocated > 0
        else 0.0
    )

    return {
        "requested_vehicles": (
            shortfall_vehicles
        ),

        "total_allocated": (
            total_allocated
        ),

        "unallocated_vehicles": (
            remaining_vehicles
        ),

        "total_scenario_capacity": (
            total_scenario_capacity
        ),

        "total_remaining_capacity": (
            total_remaining_capacity
        ),

        "total_allocation_distance_km": (
            round(
                total_walking_distance_km,
                3,
            )
        ),

        "average_assigned_distance_km": (
            round(
                average_distance_km,
                3,
            )
        ),

        "all_vehicles_allocated": (
            remaining_vehicles == 0
        ),

        "allocations": (
            allocations
        ),
    }


# ============================================================
# Print destination scenario
# ============================================================

def print_destination(
    destination,
):
    print(
        destination[
            "name"
        ]
    )

    print(
        "-" * 50
    )

    print(
        f"Type:                 "
        f"{destination['destination_type']}"
    )

    print(
        f"Priority:             "
        f"{destination['priority']}"
    )

    print(
        f"Distance:             "
        f"{destination['distance_km']:.2f} km"
    )

    print(
        f"Modeled capacity:     "
        f"{destination['modeled_available_capacity']}"
    )

    print(
        f"Capacity status:      "
        f"{destination['capacity_status']}"
    )

    print(
        f"Availability status:  "
        f"{destination['availability_status']}"
    )

    print()


# ============================================================
# Print allocation
# ============================================================

def print_allocation(
    allocation,
):
    print(
        allocation[
            "name"
        ]
    )

    print(
        "-" * 50
    )

    print(
        f"Distance:             "
        f"{allocation['distance_km']:.2f} km"
    )

    print(
        f"Modeled capacity:     "
        f"{allocation['modeled_available_capacity']}"
    )

    print(
        f"Allocated vehicles:   "
        f"{allocation['allocated_vehicles']}"
    )

    print(
        f"Remaining capacity:   "
        f"{allocation['remaining_capacity']}"
    )

    print(
        f"Capacity utilization: "
        f"{allocation['capacity_utilization'] * 100:.1f}%"
    )

    print(
        f"Allocation distance:  "
        f"{allocation['allocation_distance_km']:.2f} "
        f"vehicle-km"
    )

    print()


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Capacity-Aware "
        "Matching Demonstration"
    )

    print(
        "========================================="
    )

    print()

    errors = []

    warnings = []

    # --------------------------------------------------------
    # Load shortfall result
    # --------------------------------------------------------

    try:
        shortfall_data = load_json(
            SHORTFALL_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    source = validate_shortfall_result(
        data=shortfall_data,
        errors=errors,
    )

    validate_destinations(
        destinations=DESTINATIONS,
        errors=errors,
    )

    if errors:
        print(
            "INPUT VALIDATION FAILED"
        )

        print()

        for index, error in enumerate(
            errors,
            start=1,
        ):
            print(
                f"{index}. {error}"
            )

        return

    shortfall_vehicles = source[
        "shortfall_vehicles"
    ]

    # --------------------------------------------------------
    # Allocate displaced vehicles
    # --------------------------------------------------------

    matching_result = allocate_vehicles(
        shortfall_vehicles=(
            shortfall_vehicles
        ),
        destinations=DESTINATIONS,
    )

    # --------------------------------------------------------
    # Expected MVP allocation
    # --------------------------------------------------------

    allocation_by_id = {
        allocation[
            "destination_id"
        ]: allocation
        for allocation
        in matching_result[
            "allocations"
        ]
    }

    # --------------------------------------------------------
    # Build output
    # --------------------------------------------------------

    output = {
        "dataset_name": (
            "BanReady Conway Matching Demonstration"
        ),

        "street_name": (
            source[
                "street_name"
            ]
        ),

        "segment_id": (
            source[
                "segment_id"
            ]
        ),

        "analysis_type": (
            "SYNTHETIC_CAPACITY_MATCHING_DEMONSTRATION"
        ),

        "result_status": (
            "PROOF_OF_CONCEPT_ONLY"
        ),

        "source_shortfall": (
            source
        ),

        "matching_objective": (
            "Allocate the complete modeled shortfall "
            "while prioritizing shorter-distance "
            "destinations and respecting each "
            "destination's modeled capacity."
        ),

        "algorithm": {
            "name": (
                "CAPACITY_CONSTRAINED_GREEDY_ALLOCATION"
            ),

            "ordering": [
                "priority",
                "distance_km",
                "destination_name",
            ],

            "capacity_constraint": (
                "allocated_vehicles must not exceed "
                "modeled_available_capacity"
            ),

            "demand_constraint": (
                "total allocated vehicles should equal "
                "the source shortfall when sufficient "
                "scenario capacity exists"
            ),
        },

        "destination_scenarios": (
            DESTINATIONS
        ),

        "matching_result": (
            matching_result
        ),

        "interpretation": (
            "The central Conway proof-of-concept "
            "shortfall contains six displaced vehicles. "
            "The capacity-aware allocation sends two "
            "vehicles to the nearby legal-street "
            "scenario, three vehicles to the partner-lot "
            "scenario, and one vehicle to the municipal-"
            "garage scenario. No modeled destination "
            "capacity is exceeded."
        ),

        "limitations": [
            (
                "The source demand is synthetic and "
                "was not observed in the field."
            ),
            (
                "The Conway legal-supply result is "
                "provisional and estimated."
            ),
            (
                "All destination availability values "
                "in this matching demonstration are "
                "synthetic scenario capacities."
            ),
            (
                "The municipal-garage scenario does "
                "not represent live garage occupancy."
            ),
            (
                "The nearby-street and partner-lot "
                "destinations do not represent verified "
                "current relocation agreements."
            ),
            (
                "A production system would use real "
                "walking-network distance, current ban "
                "eligibility and dynamic capacity."
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
    # Terminal report
    # ========================================================

    print("SOURCE SHORTFALL")
    print("================")
    print()

    print(
        f"Street:                    "
        f"{source['street_name']}"
    )

    print(
        f"Segment ID:                "
        f"{source['segment_id']}"
    )

    print(
        f"Synthetic demand:          "
        f"{source['total_demand']}"
    )

    print(
        f"Estimated ban supply:      "
        f"{source['estimated_ban_supply']}"
    )

    print(
        f"Initially moving:          "
        f"{source['vehicles_initially_moving']}"
    )

    print(
        f"Absorbed within block:     "
        f"{source['absorbed_on_remaining_side']}"
    )

    print(
        f"Vehicles requiring match:  "
        f"{source['shortfall_vehicles']}"
    )

    print()

    print("DESTINATION SCENARIOS")
    print("=====================")
    print()

    for destination in sorted(
        DESTINATIONS,
        key=lambda item: (
            item[
                "priority"
            ],
            item[
                "distance_km"
            ],
        ),
    ):
        print_destination(
            destination
        )

    print("CAPACITY-AWARE ALLOCATION")
    print("=========================")
    print()

    for allocation in sorted(
        matching_result[
            "allocations"
        ],
        key=lambda item: (
            item[
                "priority"
            ],
            item[
                "distance_km"
            ],
        ),
    ):
        print_allocation(
            allocation
        )

    print("ALLOCATION SUMMARY")
    print("==================")
    print()

    print(
        f"Requested vehicles:        "
        f"{matching_result['requested_vehicles']}"
    )

    print(
        f"Total allocated:           "
        f"{matching_result['total_allocated']}"
    )

    print(
        f"Unallocated vehicles:      "
        f"{matching_result['unallocated_vehicles']}"
    )

    print(
        f"Total scenario capacity:   "
        f"{matching_result['total_scenario_capacity']}"
    )

    print(
        f"Remaining capacity:        "
        f"{matching_result['total_remaining_capacity']}"
    )

    print(
        f"Total allocation distance: "
        f"{matching_result['total_allocation_distance_km']:.2f} "
        f"vehicle-km"
    )

    print(
        f"Average assigned distance: "
        f"{matching_result['average_assigned_distance_km']:.2f} km"
    )

    print(
        f"All vehicles allocated:    "
        f"{matching_result['all_vehicles_allocated']}"
    )

    print()

    # ========================================================
    # Consistency checks
    # ========================================================

    checks = []

    checks.append(
        (
            "Source shortfall is 6",
            (
                shortfall_vehicles
                == 6
            ),
        )
    )

    checks.append(
        (
            "Three destination scenarios",
            (
                len(
                    DESTINATIONS
                )
                == 3
            ),
        )
    )

    checks.append(
        (
            "All capacities labeled synthetic",
            all(
                destination[
                    "capacity_status"
                ]
                == SYNTHETIC_CAPACITY
                for destination
                in DESTINATIONS
            ),
        )
    )

    checks.append(
        (
            "Total scenario capacity is 9",
            (
                matching_result[
                    "total_scenario_capacity"
                ]
                == 9
            ),
        )
    )

    checks.append(
        (
            "Total allocated is 6",
            (
                matching_result[
                    "total_allocated"
                ]
                == 6
            ),
        )
    )

    checks.append(
        (
            "No vehicles remain unallocated",
            (
                matching_result[
                    "unallocated_vehicles"
                ]
                == 0
            ),
        )
    )

    checks.append(
        (
            "Every destination respects capacity",
            all(
                allocation[
                    "allocated_vehicles"
                ]
                <= allocation[
                    "modeled_available_capacity"
                ]
                for allocation
                in matching_result[
                    "allocations"
                ]
            ),
        )
    )

    checks.append(
        (
            "Nearby street receives 2 vehicles",
            (
                allocation_by_id[
                    "scenario-nearby-street-001"
                ][
                    "allocated_vehicles"
                ]
                == 2
            ),
        )
    )

    checks.append(
        (
            "Partner lot receives 3 vehicles",
            (
                allocation_by_id[
                    "scenario-partner-lot-001"
                ][
                    "allocated_vehicles"
                ]
                == 3
            ),
        )
    )

    checks.append(
        (
            "Municipal garage receives 1 vehicle",
            (
                allocation_by_id[
                    "scenario-municipal-garage-001"
                ][
                    "allocated_vehicles"
                ]
                == 1
            ),
        )
    )

    checks.append(
        (
            "Allocation equals source shortfall",
            (
                matching_result[
                    "total_allocated"
                ]
                == shortfall_vehicles
            ),
        )
    )

    checks.append(
        (
            "All displaced vehicles allocated",
            (
                matching_result[
                    "all_vehicles_allocated"
                ]
                is True
            ),
        )
    )

    checks.append(
        (
            "Result remains proof-of-concept only",
            (
                output[
                    "result_status"
                ]
                == "PROOF_OF_CONCEPT_ONLY"
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
    print(
        "========================================"
    )

    print(
        "BANREADY CONWAY MATCHING SUMMARY"
    )

    print(
        "========================================"
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

    if failed_checks == 0:
        print(
            "CONWAY CAPACITY-AWARE MATCHING PASSED"
        )
    else:
        print(
            "CONWAY CAPACITY-AWARE MATCHING FAILED"
        )

    print()
    print(
        "FINAL MVP ALLOCATION"
    )

    print(
        "--------------------"
    )

    print()

    print(
        "Nearby legal street:  2 vehicles"
    )

    print(
        "Partner lot:          3 vehicles"
    )

    print(
        "Municipal garage:     1 vehicle"
    )

    print(
        "                       ----------"
    )

    print(
        "Total relocated:      6 vehicles"
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
        "All destination capacities and availability "
        "values in this demonstration are synthetic."
    )

    print()

    print(
        "The matching result demonstrates the "
        "capacity-constrained allocation method and "
        "must not be presented as a live relocation plan."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
