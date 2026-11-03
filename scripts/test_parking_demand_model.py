import sys
from pathlib import Path


# ============================================================
# Project setup
# ============================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parent.parent


if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


# ============================================================
# BanReady imports
# ============================================================

from backend.app.models.parking_demand import (
    CLEAR,
    ESTIMATED,
    MANUAL_FIELD_COUNT,
    OBSERVED,
    SYNTHETIC_SCENARIO,
    ParkingDemandObservation,
)


# ============================================================
# Test-result helper
# ============================================================

def print_test(
    test_number,
    test_name,
    passed,
):
    result = (
        "PASS"
        if passed
        else "FAIL"
    )

    print(
        f"Test {test_number:02d} - "
        f"{test_name}: "
        f"{result}"
    )


# ============================================================
# Main test suite
# ============================================================

def main():
    print()
    print(
        "BanReady Parking Demand Model Test Suite"
    )

    print(
        "========================================"
    )

    print()

    results = []


    # ========================================================
    # Create a valid synthetic observation
    #
    # IMPORTANT:
    # These values are for software testing only.
    # They are not real Conway field observations.
    # ========================================================

    observation = ParkingDemandObservation(
        observation_id=(
            "synthetic-demand-test-001"
        ),

        street_name=(
            "SYNTHETIC TEST STREET"
        ),

        segment_id=999999,

        observation_date=(
            "2026-10-01"
        ),

        observation_time=(
            "22:15"
        ),

        parked_odd=12,

        parked_even=9,

        driveway_vehicles=7,

        private_lot_vehicles=4,

        observer_id=(
            "test-observer"
        ),

        weather=CLEAR,

        snow_on_ground=False,

        winter_ban_active=False,

        unusual_event=False,

        evidence_status=OBSERVED,

        collection_method=(
            MANUAL_FIELD_COUNT
        ),

        notes=(
            "Synthetic observation used only "
            "to test the BanReady demand model."
        ),
    )


    # ========================================================
    # Test 1
    #
    # ODD + EVEN should equal total on-street demand.
    #
    # 12 + 9 = 21
    # ========================================================

    test_1 = (
        observation.total_on_street_demand
        == 21
    )

    results.append(
        (
            "On-street demand calculation",
            test_1,
        )
    )


    # ========================================================
    # Test 2
    #
    # Contextual off-street vehicles should be calculated
    # independently.
    #
    # 7 driveway + 4 private-lot = 11
    # ========================================================

    test_2 = (
        observation
        .total_contextual_off_street_vehicles
        == 11
    )

    results.append(
        (
            "Contextual vehicle calculation",
            test_2,
        )
    )


    # ========================================================
    # Test 3
    #
    # Off-street vehicles must not enter on-street demand.
    # ========================================================

    test_3 = (
        observation.total_on_street_demand
        == 21
        and observation
        .total_contextual_off_street_vehicles
        == 11
        and observation.total_on_street_demand
        != 32
    )

    results.append(
        (
            "Off-street vehicles excluded",
            test_3,
        )
    )


    # ========================================================
    # Test 4
    #
    # Valid observation should have no validation errors.
    # ========================================================

    validation_errors = (
        observation.validate()
    )

    test_4 = (
        validation_errors == []
    )

    results.append(
        (
            "Valid observation accepted",
            test_4,
        )
    )


    # ========================================================
    # Test 5
    #
    # Evidence status should be retained.
    # ========================================================

    test_5 = (
        observation.evidence_status
        == OBSERVED
    )

    results.append(
        (
            "Evidence status retained",
            test_5,
        )
    )


    # ========================================================
    # Test 6
    #
    # Collection method should be retained.
    # ========================================================

    test_6 = (
        observation.collection_method
        == MANUAL_FIELD_COUNT
    )

    results.append(
        (
            "Collection method retained",
            test_6,
        )
    )


    # ========================================================
    # Test 7
    #
    # Observation date and time should be retained.
    # ========================================================

    test_7 = (
        observation.observation_date
        == "2026-10-01"
        and observation.observation_time
        == "22:15"
    )

    results.append(
        (
            "Date and time retained",
            test_7,
        )
    )


    # ========================================================
    # Test 8
    #
    # Dictionary conversion should include calculated totals.
    # ========================================================

    observation_data = (
        observation.to_dict()
    )

    test_8 = (
        observation_data[
            "parked_odd"
        ]
        == 12
        and observation_data[
            "parked_even"
        ]
        == 9
        and observation_data[
            "total_on_street_demand"
        ]
        == 21
        and observation_data[
            "total_contextual_off_street_vehicles"
        ]
        == 11
    )

    results.append(
        (
            "Dictionary totals included",
            test_8,
        )
    )


    # ========================================================
    # Test 9
    #
    # Zero parked vehicles should be valid.
    # ========================================================

    zero_observation = ParkingDemandObservation(
        observation_id=(
            "synthetic-zero-test"
        ),

        street_name=(
            "SYNTHETIC EMPTY STREET"
        ),

        segment_id=888888,

        observation_date=(
            "2026-10-01"
        ),

        observation_time=(
            "23:00"
        ),

        parked_odd=0,

        parked_even=0,

        evidence_status=OBSERVED,

        collection_method=(
            MANUAL_FIELD_COUNT
        ),
    )

    test_9 = (
        zero_observation
        .total_on_street_demand
        == 0
        and zero_observation.validate()
        == []
    )

    results.append(
        (
            "Zero-count observation accepted",
            test_9,
        )
    )


    # ========================================================
    # Test 10
    #
    # Null contextual counts should be treated as zero.
    # ========================================================

    test_10 = (
        zero_observation
        .total_contextual_off_street_vehicles
        == 0
    )

    results.append(
        (
            "Null contextual counts handled",
            test_10,
        )
    )


    # ========================================================
    # Test 11
    #
    # Negative ODD count should be rejected.
    # ========================================================

    negative_odd_observation = (
        ParkingDemandObservation(
            observation_id=(
                "invalid-negative-odd"
            ),

            street_name=(
                "INVALID TEST STREET"
            ),

            segment_id=777777,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "21:30"
            ),

            parked_odd=-1,

            parked_even=5,
        )
    )

    negative_odd_errors = (
        negative_odd_observation
        .validate()
    )

    test_11 = (
        "parked_odd cannot be negative."
        in negative_odd_errors
    )

    results.append(
        (
            "Negative ODD count rejected",
            test_11,
        )
    )


    # ========================================================
    # Test 12
    #
    # Negative EVEN count should be rejected.
    # ========================================================

    negative_even_observation = (
        ParkingDemandObservation(
            observation_id=(
                "invalid-negative-even"
            ),

            street_name=(
                "INVALID TEST STREET"
            ),

            segment_id=777778,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "21:45"
            ),

            parked_odd=5,

            parked_even=-1,
        )
    )

    negative_even_errors = (
        negative_even_observation
        .validate()
    )

    test_12 = (
        "parked_even cannot be negative."
        in negative_even_errors
    )

    results.append(
        (
            "Negative EVEN count rejected",
            test_12,
        )
    )


    # ========================================================
    # Test 13
    #
    # Negative driveway count should be rejected.
    # ========================================================

    negative_driveway_observation = (
        ParkingDemandObservation(
            observation_id=(
                "invalid-negative-driveway"
            ),

            street_name=(
                "INVALID TEST STREET"
            ),

            segment_id=777779,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "22:00"
            ),

            parked_odd=5,

            parked_even=5,

            driveway_vehicles=-1,
        )
    )

    negative_driveway_errors = (
        negative_driveway_observation
        .validate()
    )

    test_13 = (
        (
            "driveway_vehicles cannot be "
            "negative."
        )
        in negative_driveway_errors
    )

    results.append(
        (
            "Negative driveway count rejected",
            test_13,
        )
    )


    # ========================================================
    # Test 14
    #
    # Non-integer street counts should be rejected.
    # ========================================================

    non_integer_observation = (
        ParkingDemandObservation(
            observation_id=(
                "invalid-non-integer"
            ),

            street_name=(
                "INVALID TEST STREET"
            ),

            segment_id=777780,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "22:10"
            ),

            parked_odd=5.5,

            parked_even=4,
        )
    )

    non_integer_errors = (
        non_integer_observation
        .validate()
    )

    test_14 = (
        "parked_odd must be an integer."
        in non_integer_errors
    )

    results.append(
        (
            "Non-integer count rejected",
            test_14,
        )
    )


    # ========================================================
    # Test 15
    #
    # Synthetic scenario cannot be labeled OBSERVED.
    # ========================================================

    mislabeled_synthetic_observation = (
        ParkingDemandObservation(
            observation_id=(
                "synthetic-mislabeled-test"
            ),

            street_name=(
                "SYNTHETIC TEST STREET"
            ),

            segment_id=666666,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "22:30"
            ),

            parked_odd=10,

            parked_even=10,

            evidence_status=OBSERVED,

            collection_method=(
                SYNTHETIC_SCENARIO
            ),
        )
    )

    synthetic_label_errors = (
        mislabeled_synthetic_observation
        .validate()
    )

    test_15 = (
        (
            "Synthetic scenario data cannot be "
            "labeled OBSERVED."
        )
        in synthetic_label_errors
    )

    results.append(
        (
            "Synthetic OBSERVED label rejected",
            test_15,
        )
    )


    # ========================================================
    # Test 16
    #
    # Properly labeled synthetic scenario should be valid.
    # ========================================================

    valid_synthetic_observation = (
        ParkingDemandObservation(
            observation_id=(
                "synthetic-valid-test"
            ),

            street_name=(
                "SYNTHETIC TEST STREET"
            ),

            segment_id=666667,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "22:45"
            ),

            parked_odd=10,

            parked_even=10,

            evidence_status=ESTIMATED,

            collection_method=(
                SYNTHETIC_SCENARIO
            ),

            notes=(
                "Synthetic scenario used only "
                "for model demonstration."
            ),
        )
    )

    test_16 = (
        valid_synthetic_observation
        .validate()
        == []
    )

    results.append(
        (
            "Labeled synthetic scenario accepted",
            test_16,
        )
    )


    # ========================================================
    # Test 17
    #
    # Empty observation ID should be rejected.
    # ========================================================

    empty_id_observation = (
        ParkingDemandObservation(
            observation_id="",

            street_name=(
                "TEST STREET"
            ),

            segment_id=555555,

            observation_date=(
                "2026-10-01"
            ),

            observation_time=(
                "23:15"
            ),

            parked_odd=1,

            parked_even=1,
        )
    )

    empty_id_errors = (
        empty_id_observation
        .validate()
    )

    test_17 = (
        (
            "observation_id cannot be empty."
        )
        in empty_id_errors
    )

    results.append(
        (
            "Empty observation ID rejected",
            test_17,
        )
    )


    # ========================================================
    # Display sample observation
    # ========================================================

    print(
        "SYNTHETIC MODEL RECORD"
    )

    print(
        "======================"
    )

    print()

    print(
        f"Observation ID:       "
        f"{observation.observation_id}"
    )

    print(
        f"Street:               "
        f"{observation.street_name}"
    )

    print(
        f"Segment ID:           "
        f"{observation.segment_id}"
    )

    print(
        f"Date:                 "
        f"{observation.observation_date}"
    )

    print(
        f"Time:                 "
        f"{observation.observation_time}"
    )

    print()

    print(
        f"Parked ODD:           "
        f"{observation.parked_odd}"
    )

    print(
        f"Parked EVEN:          "
        f"{observation.parked_even}"
    )

    print(
        f"On-street demand:     "
        f"{observation.total_on_street_demand}"
    )

    print()

    print(
        f"Driveway vehicles:    "
        f"{observation.driveway_vehicles}"
    )

    print(
        f"Private-lot vehicles: "
        f"{observation.private_lot_vehicles}"
    )

    print(
        f"Contextual off-street:"
        f" "
        f"{observation.total_contextual_off_street_vehicles}"
    )

    print()

    print(
        f"Evidence status:      "
        f"{observation.evidence_status}"
    )

    print(
        f"Collection method:    "
        f"{observation.collection_method}"
    )

    print()


    # ========================================================
    # Print tests
    # ========================================================

    print(
        "MODEL CHECKS"
    )

    print(
        "============"
    )

    print()

    for index, (
        test_name,
        passed,
    ) in enumerate(
        results,
        start=1,
    ):
        print_test(
            test_number=index,
            test_name=test_name,
            passed=passed,
        )


    # ========================================================
    # Summary
    # ========================================================

    total_tests = len(
        results
    )

    passed_tests = sum(
        1
        for _, passed
        in results
        if passed
    )

    failed_tests = (
        total_tests
        - passed_tests
    )

    print()

    print(
        "====================================="
    )

    print(
        "BANREADY DEMAND MODEL TEST SUMMARY"
    )

    print(
        "====================================="
    )

    print()

    print(
        f"Total tests: "
        f"{total_tests}"
    )

    print(
        f"Passed:      "
        f"{passed_tests}"
    )

    print(
        f"Failed:      "
        f"{failed_tests}"
    )

    print()

    if failed_tests == 0:
        print(
            "ALL PARKING DEMAND MODEL TESTS PASSED"
        )

        print()

        print(
            "BanReady's demand model is ready "
            "for the field-count sheet."
        )

    else:
        print(
            "PARKING DEMAND MODEL TESTS FAILED"
        )

        print()

        print(
            "Resolve the model errors before "
            "recording field observations."
        )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    main()