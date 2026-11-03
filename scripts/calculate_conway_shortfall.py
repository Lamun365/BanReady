import csv
import json
import math
from pathlib import Path


# ============================================================
# Input and output files
# ============================================================

DEMAND_FILE = Path(
    "data/research/worcester/"
    "nighttime_parking_counts.csv"
)

SUPPLY_FILE = Path(
    "data/research/worcester/"
    "conway_821528_hydrant_interval_review.json"
)

OUTPUT_FILE = Path(
    "data/research/worcester/"
    "conway_821528_shortfall_result.json"
)


# ============================================================
# Expected Conway values
# ============================================================

EXPECTED_OBSERVATION_ID = (
    "conway-821528-scenario-001"
)

EXPECTED_STREET_NAME = "CONWAY ST"

EXPECTED_SEGMENT_ID = 821528

EXPECTED_RESTRICTED_SIDE = "EVEN"

EXPECTED_EVIDENCE_STATUS = "ESTIMATED"

EXPECTED_COLLECTION_METHOD = (
    "SYNTHETIC_SCENARIO"
)

SYNTHETIC_SCENARIO = "SYNTHETIC_SCENARIO"


# ============================================================
# Space-allocation assumptions
#
# These are modeling assumptions.
# They are not official Worcester marked-space dimensions.
# ============================================================

SPACE_LENGTH_ASSUMPTIONS_METERS = [
    5.5,
    6.0,
    6.5,
]

CENTRAL_SPACE_LENGTH_METERS = 6.0


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


def parse_integer(
    value,
    field_name,
):
    if value is None:
        raise ValueError(
            f"{field_name} is missing."
        )

    text = str(
        value
    ).strip()

    if text == "":
        raise ValueError(
            f"{field_name} is empty."
        )

    try:
        parsed_value = int(
            text
        )

    except ValueError as error:
        raise ValueError(
            f"{field_name} must be an integer."
        ) from error

    return parsed_value


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


def load_demand_rows(
    path,
):
    if not path.exists():
        raise RuntimeError(
            f"Required CSV file not found: {path}"
        )

    with open(
        path,
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.DictReader(
            file
        )

        return list(
            reader
        )


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
# Locate Conway scenario
# ============================================================

def find_demand_row(
    rows,
):
    for row in rows:
        observation_id = str(
            row.get(
                "observation_id"
            )
            or ""
        ).strip()

        if (
            observation_id
            == EXPECTED_OBSERVATION_ID
        ):
            return row

    return None


# ============================================================
# Validate and normalize demand
# ============================================================

def validate_demand_row(
    row,
    errors,
):
    if row is None:
        add_error(
            errors,
            (
                "Conway synthetic demand "
                "scenario was not found."
            ),
        )

        return None

    observation_id = str(
        row.get(
            "observation_id"
        )
        or ""
    ).strip()

    street_name = str(
        row.get(
            "street_name"
        )
        or ""
    ).strip().upper()

    evidence_status = str(
        row.get(
            "evidence_status"
        )
        or ""
    ).strip().upper()

    collection_method = str(
        row.get(
            "collection_method"
        )
        or ""
    ).strip().upper()

    notes = str(
        row.get(
            "notes"
        )
        or ""
    ).strip()

    try:
        segment_id = parse_integer(
            row.get(
                "segment_id"
            ),
            "segment_id",
        )

        parked_odd = parse_integer(
            row.get(
                "parked_odd"
            ),
            "parked_odd",
        )

        parked_even = parse_integer(
            row.get(
                "parked_even"
            ),
            "parked_even",
        )

        declared_total = parse_integer(
            row.get(
                "total_on_street_demand"
            ),
            "total_on_street_demand",
        )

    except ValueError as error:
        add_error(
            errors,
            str(error),
        )

        return None

    if (
        observation_id
        != EXPECTED_OBSERVATION_ID
    ):
        add_error(
            errors,
            (
                "Unexpected observation_id: "
                f"{observation_id}."
            ),
        )

    if (
        street_name
        != EXPECTED_STREET_NAME
    ):
        add_error(
            errors,
            (
                "Demand row must reference "
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
                "Demand row must reference "
                "segment 821528."
            ),
        )

    if parked_odd < 0:
        add_error(
            errors,
            (
                "parked_odd cannot be "
                "negative."
            ),
        )

    if parked_even < 0:
        add_error(
            errors,
            (
                "parked_even cannot be "
                "negative."
            ),
        )

    calculated_total = (
        parked_odd
        + parked_even
    )

    if (
        declared_total
        != calculated_total
    ):
        add_error(
            errors,
            (
                "Declared total demand does "
                "not equal parked_odd plus "
                "parked_even."
            ),
        )

    if (
        evidence_status
        != EXPECTED_EVIDENCE_STATUS
    ):
        add_error(
            errors,
            (
                "Synthetic demand scenario "
                "must have evidence_status "
                "ESTIMATED."
            ),
        )

    if (
        collection_method
        != EXPECTED_COLLECTION_METHOD
    ):
        add_error(
            errors,
            (
                "Demand scenario must have "
                "collection_method "
                "SYNTHETIC_SCENARIO."
            ),
        )

    if evidence_status == "OBSERVED":
        add_error(
            errors,
            (
                "Synthetic demand cannot be "
                "labeled OBSERVED."
            ),
        )

    if (
        "synthetic"
        not in notes.lower()
    ):
        add_error(
            errors,
            (
                "Demand notes must clearly "
                "identify the scenario as "
                "synthetic."
            ),
        )

    return {
        "observation_id": (
            observation_id
        ),

        "street_name": (
            street_name
        ),

        "segment_id": (
            segment_id
        ),

        "observation_date": str(
            row.get(
                "observation_date"
            )
            or ""
        ).strip(),

        "observation_time": str(
            row.get(
                "observation_time"
            )
            or ""
        ).strip(),

        "parked_odd": (
            parked_odd
        ),

        "parked_even": (
            parked_even
        ),

        "total_on_street_demand": (
            calculated_total
        ),

        "evidence_status": (
            evidence_status
        ),

        "collection_method": (
            collection_method
        ),

        "notes": (
            notes
        ),
    }


# ============================================================
# Validate and normalize supply
# ============================================================

def validate_supply_data(
    data,
    errors,
    warnings,
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

    restricted_side = str(
        data.get(
            "restricted_side"
        )
        or ""
    ).strip().upper()

    inventory_status = str(
        data.get(
            "inventory_status"
        )
        or ""
    ).strip().upper()

    odd_side = data.get(
        "odd_side",
        {},
    )

    even_side = data.get(
        "even_side",
        {},
    )

    odd_curb = odd_side.get(
        "provisional_remaining_curb_meters"
    )

    even_curb = even_side.get(
        "provisional_remaining_curb_meters"
    )

    if (
        street_name
        != EXPECTED_STREET_NAME
    ):
        add_error(
            errors,
            (
                "Supply file must reference "
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
                "Supply file must reference "
                "segment 821528."
            ),
        )

    if (
        restricted_side
        != EXPECTED_RESTRICTED_SIDE
    ):
        add_error(
            errors,
            (
                "Conway restricted side "
                "must be EVEN."
            ),
        )

    if not is_number(
        odd_curb
    ):
        add_error(
            errors,
            (
                "ODD provisional curb "
                "length is invalid."
            ),
        )

    elif odd_curb < 0:
        add_error(
            errors,
            (
                "ODD provisional curb "
                "length cannot be negative."
            ),
        )

    if not is_number(
        even_curb
    ):
        add_error(
            errors,
            (
                "EVEN provisional curb "
                "length is invalid."
            ),
        )

    elif even_curb < 0:
        add_error(
            errors,
            (
                "EVEN provisional curb "
                "length cannot be negative."
            ),
        )

    if (
        inventory_status
        != "INCOMPLETE"
    ):
        add_warning(
            warnings,
            (
                "Expected the Conway curb "
                "inventory to remain "
                "INCOMPLETE at MVP stage."
            ),
        )

    return {
        "street_name": (
            street_name
        ),

        "segment_id": (
            segment_id
        ),

        "restricted_side": (
            restricted_side
        ),

        "inventory_status": (
            inventory_status
        ),

        "odd_provisional_curb_meters": (
            float(
                odd_curb
            )
            if is_number(
                odd_curb
            )
            else None
        ),

        "even_provisional_curb_meters": (
            float(
                even_curb
            )
            if is_number(
                even_curb
            )
            else None
        ),

        "review_stage": data.get(
            "review_stage"
        ),
    }


# ============================================================
# Calculate one sensitivity scenario
# ============================================================

def calculate_scenario(
    demand,
    supply,
    space_length_meters,
):
    odd_demand = demand[
        "parked_odd"
    ]

    even_demand = demand[
        "parked_even"
    ]

    total_demand = demand[
        "total_on_street_demand"
    ]

    odd_curb = supply[
        "odd_provisional_curb_meters"
    ]

    even_curb = supply[
        "even_provisional_curb_meters"
    ]

    # --------------------------------------------------------
    # Normal modeled capacities
    # --------------------------------------------------------

    odd_normal_capacity = math.floor(
        odd_curb
        / space_length_meters
    )

    even_normal_capacity = math.floor(
        even_curb
        / space_length_meters
    )

    total_normal_capacity = (
        odd_normal_capacity
        + even_normal_capacity
    )

    # --------------------------------------------------------
    # Active-ban capacities
    #
    # Conway segment 821528 restricts the EVEN side.
    # --------------------------------------------------------

    odd_ban_capacity = (
        odd_normal_capacity
    )

    even_ban_capacity = 0

    total_ban_capacity = (
        odd_ban_capacity
        + even_ban_capacity
    )

    # --------------------------------------------------------
    # Demand and displacement
    # --------------------------------------------------------

    affected_vehicles = (
        even_demand
    )

    odd_spare_capacity_before_move = max(
        0,
        odd_ban_capacity
        - odd_demand,
    )

    absorbed_on_remaining_side = min(
        affected_vehicles,
        odd_spare_capacity_before_move,
    )

    shortfall_from_reallocation = max(
        0,
        affected_vehicles
        - absorbed_on_remaining_side,
    )

    direct_shortfall = max(
        0,
        total_demand
        - total_ban_capacity,
    )

    # --------------------------------------------------------
    # Both formulations should agree for this scenario.
    # --------------------------------------------------------

    shortfall_consistent = (
        shortfall_from_reallocation
        == direct_shortfall
    )

    normal_spare_capacity = max(
        0,
        total_normal_capacity
        - total_demand,
    )

    return {
        "space_length_assumption_meters": (
            space_length_meters
        ),

        "assumption_status": (
            "MODELED_ASSUMPTION"
        ),

        "odd_provisional_curb_meters": (
            round(
                odd_curb,
                3,
            )
        ),

        "even_provisional_curb_meters": (
            round(
                even_curb,
                3,
            )
        ),

        "odd_normal_capacity": (
            odd_normal_capacity
        ),

        "even_normal_capacity": (
            even_normal_capacity
        ),

        "total_normal_capacity": (
            total_normal_capacity
        ),

        "odd_ban_capacity": (
            odd_ban_capacity
        ),

        "even_ban_capacity": (
            even_ban_capacity
        ),

        "total_ban_capacity": (
            total_ban_capacity
        ),

        "odd_observed_or_modeled_demand": (
            odd_demand
        ),

        "even_observed_or_modeled_demand": (
            even_demand
        ),

        "total_demand": (
            total_demand
        ),

        "vehicles_on_restricted_side": (
            affected_vehicles
        ),

        "odd_spare_capacity_before_move": (
            odd_spare_capacity_before_move
        ),

        "absorbed_on_remaining_odd_side": (
            absorbed_on_remaining_side
        ),

        "shortfall_from_reallocation": (
            shortfall_from_reallocation
        ),

        "direct_shortfall": (
            direct_shortfall
        ),

        "shortfall_consistent": (
            shortfall_consistent
        ),

        "normal_condition_spare_capacity": (
            normal_spare_capacity
        ),
    }


# ============================================================
# Print scenario
# ============================================================

def print_scenario(
    scenario,
    is_central,
):
    label = (
        "CENTRAL SCENARIO"
        if is_central
        else "SENSITIVITY SCENARIO"
    )

    print(
        f"{label}: "
        f"{scenario['space_length_assumption_meters']:.1f} m"
    )

    print(
        "-" * 55
    )

    print(
        f"ODD normal capacity:        "
        f"{scenario['odd_normal_capacity']}"
    )

    print(
        f"EVEN normal capacity:       "
        f"{scenario['even_normal_capacity']}"
    )

    print(
        f"Total normal capacity:      "
        f"{scenario['total_normal_capacity']}"
    )

    print()

    print(
        f"ODD ban capacity:           "
        f"{scenario['odd_ban_capacity']}"
    )

    print(
        f"EVEN ban capacity:          "
        f"{scenario['even_ban_capacity']}"
    )

    print(
        f"Total ban capacity:         "
        f"{scenario['total_ban_capacity']}"
    )

    print()

    print(
        f"Synthetic total demand:     "
        f"{scenario['total_demand']}"
    )

    print(
        f"Vehicles on restricted side:"
        f" "
        f"{scenario['vehicles_on_restricted_side']}"
    )

    print(
        f"ODD spare capacity:         "
        f"{scenario['odd_spare_capacity_before_move']}"
    )

    print(
        f"Absorbed on ODD side:       "
        f"{scenario['absorbed_on_remaining_odd_side']}"
    )

    print(
        f"Remaining shortfall:        "
        f"{scenario['direct_shortfall']}"
    )

    print(
        f"Calculation consistent:     "
        f"{scenario['shortfall_consistent']}"
    )

    print()


# ============================================================
# Main
# ============================================================

def main():
    print()
    print(
        "BanReady Conway Shortfall Calculator"
    )

    print(
        "===================================="
    )

    print()

    errors = []

    warnings = []

    # --------------------------------------------------------
    # Load files
    # --------------------------------------------------------

    try:
        demand_rows = load_demand_rows(
            DEMAND_FILE
        )

        supply_json = load_json(
            SUPPLY_FILE
        )

    except RuntimeError as error:
        print(
            f"ERROR: {error}"
        )

        return

    # --------------------------------------------------------
    # Validate inputs
    # --------------------------------------------------------

    demand_row = find_demand_row(
        demand_rows
    )

    demand = validate_demand_row(
        row=demand_row,
        errors=errors,
    )

    supply = validate_supply_data(
        data=supply_json,
        errors=errors,
        warnings=warnings,
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

    # --------------------------------------------------------
    # Calculate sensitivity scenarios
    # --------------------------------------------------------

    scenarios = []

    for assumption in (
        SPACE_LENGTH_ASSUMPTIONS_METERS
    ):
        scenario = calculate_scenario(
            demand=demand,
            supply=supply,
            space_length_meters=(
                assumption
            ),
        )

        scenarios.append(
            scenario
        )

    central_scenario = next(
        (
            scenario
            for scenario in scenarios
            if abs(
                scenario[
                    "space_length_assumption_meters"
                ]
                - CENTRAL_SPACE_LENGTH_METERS
            )
            < 0.001
        ),
        None,
    )

    if central_scenario is None:
        print(
            "ERROR: Central 6.0 m scenario "
            "was not calculated."
        )

        return

    shortfall_values = [
        scenario[
            "direct_shortfall"
        ]
        for scenario in scenarios
    ]

    minimum_shortfall = min(
        shortfall_values
    )

    maximum_shortfall = max(
        shortfall_values
    )

    # --------------------------------------------------------
    # Build output
    # --------------------------------------------------------

    output = {
        "dataset_name": (
            "BanReady Conway Shortfall Result"
        ),

        "street_name": (
            EXPECTED_STREET_NAME
        ),

        "segment_id": (
            EXPECTED_SEGMENT_ID
        ),

        "analysis_type": (
            "SYNTHETIC_DEMAND_PROOF_OF_CONCEPT"
        ),

        "result_status": (
            "PROVISIONAL_ESTIMATED"
        ),

        "demand": (
            demand
        ),

        "supply": {
            **supply,

            "supply_status": (
                "PROVISIONAL_ESTIMATED"
            ),

            "supply_limitations": [
                (
                    "The curb inventory is "
                    "INCOMPLETE."
                ),
                (
                    "The provisional curb lengths "
                    "include driveway and hydrant "
                    "exclusions only."
                ),
                (
                    "The result is not an official "
                    "legal-space count."
                ),
            ],
        },

        "space_length_assumptions_meters": (
            SPACE_LENGTH_ASSUMPTIONS_METERS
        ),

        "central_space_length_meters": (
            CENTRAL_SPACE_LENGTH_METERS
        ),

        "scenarios": (
            scenarios
        ),

        "central_result": (
            central_scenario
        ),

        "sensitivity_summary": {
            "minimum_shortfall": (
                minimum_shortfall
            ),

            "maximum_shortfall": (
                maximum_shortfall
            ),

            "shortfall_range": (
                f"{minimum_shortfall}"
                f"-"
                f"{maximum_shortfall}"
            ),
        },

        "interpretation": (
            "Under the central synthetic scenario, "
            "18 vehicles begin on the restricted EVEN "
            "side. Modeled spare capacity on the ODD "
            "side absorbs 12 vehicles, leaving a "
            "six-vehicle shortfall requiring relocation "
            "to another street, garage or partner lot."
        ),

        "limitations": [
            (
                "Demand values are synthetic and "
                "were not collected through a field "
                "observation."
            ),
            (
                "The Conway curb inventory remains "
                "INCOMPLETE."
            ),
            (
                "Vehicle-space lengths are modeling "
                "assumptions rather than official "
                "marked-space dimensions."
            ),
            (
                "The results demonstrate the BanReady "
                "calculation pipeline and must not be "
                "presented as measured current parking "
                "conditions."
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

    print("DEMAND SCENARIO")
    print("===============")
    print()

    print(
        f"Observation ID:      "
        f"{demand['observation_id']}"
    )

    print(
        f"Street:              "
        f"{demand['street_name']}"
    )

    print(
        f"Segment ID:          "
        f"{demand['segment_id']}"
    )

    print(
        f"Parked ODD:          "
        f"{demand['parked_odd']}"
    )

    print(
        f"Parked EVEN:         "
        f"{demand['parked_even']}"
    )

    print(
        f"Total demand:        "
        f"{demand['total_on_street_demand']}"
    )

    print(
        f"Evidence status:     "
        f"{demand['evidence_status']}"
    )

    print(
        f"Collection method:   "
        f"{demand['collection_method']}"
    )

    print()

    print("PROVISIONAL SUPPLY")
    print("==================")
    print()

    print(
        f"ODD curb remaining:  "
        f"{supply['odd_provisional_curb_meters']:.3f} m"
    )

    print(
        f"EVEN curb remaining: "
        f"{supply['even_provisional_curb_meters']:.3f} m"
    )

    print(
        f"Restricted side:     "
        f"{supply['restricted_side']}"
    )

    print(
        f"Inventory status:    "
        f"{supply['inventory_status']}"
    )

    print()

    print("SENSITIVITY ANALYSIS")
    print("====================")
    print()

    for scenario in scenarios:
        is_central = (
            abs(
                scenario[
                    "space_length_assumption_meters"
                ]
                - CENTRAL_SPACE_LENGTH_METERS
            )
            < 0.001
        )

        print_scenario(
            scenario=scenario,
            is_central=is_central,
        )

    # ========================================================
    # Consistency checks
    # ========================================================

    checks = []

    checks.append(
        (
            "Demand row is synthetic",
            (
                demand[
                    "collection_method"
                ]
                == EXPECTED_COLLECTION_METHOD
            ),
        )
    )

    checks.append(
        (
            "Synthetic demand not labeled OBSERVED",
            (
                demand[
                    "evidence_status"
                ]
                != "OBSERVED"
            ),
        )
    )

    checks.append(
        (
            "ODD plus EVEN equals total demand",
            (
                demand[
                    "parked_odd"
                ]
                + demand[
                    "parked_even"
                ]
                == demand[
                    "total_on_street_demand"
                ]
            ),
        )
    )

    checks.append(
        (
            "Restricted side is EVEN",
            (
                supply[
                    "restricted_side"
                ]
                == "EVEN"
            ),
        )
    )

    checks.append(
        (
            "Three sensitivity scenarios calculated",
            (
                len(scenarios)
                == 3
            ),
        )
    )

    checks.append(
        (
            "Every scenario has zero EVEN ban capacity",
            all(
                scenario[
                    "even_ban_capacity"
                ]
                == 0
                for scenario
                in scenarios
            ),
        )
    )

    checks.append(
        (
            "Every shortfall is nonnegative",
            all(
                scenario[
                    "direct_shortfall"
                ]
                >= 0
                for scenario
                in scenarios
            ),
        )
    )

    checks.append(
        (
            "Both shortfall calculations agree",
            all(
                scenario[
                    "shortfall_consistent"
                ]
                for scenario
                in scenarios
            ),
        )
    )

    checks.append(
        (
            "Central estimated ban capacity is 34",
            (
                central_scenario[
                    "total_ban_capacity"
                ]
                == 34
            ),
        )
    )

    checks.append(
        (
            "Central shortfall is 6",
            (
                central_scenario[
                    "direct_shortfall"
                ]
                == 6
            ),
        )
    )

    checks.append(
        (
            "Shortfall sensitivity range is 3 to 9",
            (
                minimum_shortfall
                == 3
                and maximum_shortfall
                == 9
            ),
        )
    )

    checks.append(
        (
            "Result remains provisional",
            (
                output[
                    "result_status"
                ]
                == "PROVISIONAL_ESTIMATED"
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
        "===================================="
    )

    print(
        "BANREADY CONWAY SHORTFALL SUMMARY"
    )

    print(
        "===================================="
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
            "CONWAY SHORTFALL CALCULATION PASSED"
        )
    else:
        print(
            "CONWAY SHORTFALL CALCULATION FAILED"
        )

    print()

    print(
        "CENTRAL SYNTHETIC SCENARIO"
    )

    print(
        "--------------------------"
    )

    print()

    print(
        f"Synthetic demand:          "
        f"{central_scenario['total_demand']}"
    )

    print(
        f"Estimated ban supply:      "
        f"{central_scenario['total_ban_capacity']}"
    )

    print(
        f"Vehicles initially moving:"
        f" "
        f"{central_scenario['vehicles_on_restricted_side']}"
    )

    print(
        f"Absorbed on ODD side:      "
        f"{central_scenario['absorbed_on_remaining_odd_side']}"
    )

    print(
        f"Estimated shortfall:       "
        f"{central_scenario['direct_shortfall']}"
    )

    print(
        f"Sensitivity range:         "
        f"{minimum_shortfall}"
        f" to "
        f"{maximum_shortfall}"
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
        "The demand values are synthetic and "
        "must not be presented as field observations."
    )

    print()

    print(
        "The supply values are provisional estimates "
        "and not official legal-space counts."
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()
