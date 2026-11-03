import sys
from pathlib import Path


# ============================================================
# Allow this script to import from the BanReady project root
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# Import BanReady rule engine
# ============================================================

from backend.app.services.ban_engine import (
    CAN_STAY_DURING_BAN,
    MUST_MOVE,
    NOT_AFFECTED,
    VERIFY_RULE,
    evaluate_parking_status,
)


# ============================================================
# Test helper
# ============================================================

def run_test(
    test_name,
    expected_status,
    **engine_inputs
):
    result = evaluate_parking_status(**engine_inputs)

    passed = result.status == expected_status

    print()
    print(test_name)
    print("-" * len(test_name))

    print(f"Expected: {expected_status}")
    print(f"Actual:   {result.status}")

    if passed:
        print("Result:   PASS")
    else:
        print("Result:   FAIL")

    print(f"Reason:   {result.reason}")

    return passed


# ============================================================
# Main test suite
# ============================================================

def main():
    print()
    print("BanReady Ban Engine Test Suite")
    print("==============================")

    results = []


    # --------------------------------------------------------
    # TEST 1
    #
    # Declared ban is active.
    # EVEN side is prohibited.
    # Vehicle is parked on EVEN side.
    #
    # Expected: MUST_MOVE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 1 - Declared ban, restricted side",
            expected_status=MUST_MOVE,
            ban_type="DECLARED",
            no_parking_side="EVEN",
            parked_side="EVEN",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 2
    #
    # Declared ban is active.
    # EVEN side is prohibited.
    # Vehicle is parked on ODD side.
    #
    # Expected: CAN_STAY_DURING_BAN
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 2 - Declared ban, opposite side",
            expected_status=CAN_STAY_DURING_BAN,
            ban_type="DECLARED",
            no_parking_side="EVEN",
            parked_side="ODD",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 3
    #
    # Declared ban is active.
    # Both sides are prohibited.
    #
    # Expected: MUST_MOVE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 3 - Declared ban, both sides",
            expected_status=MUST_MOVE,
            ban_type="DECLARED",
            no_parking_side="BOTH",
            parked_side="ODD",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 4
    #
    # Street has a declared-ban rule,
    # but no declared ban is currently active.
    #
    # Expected: NOT_AFFECTED
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 4 - Declared ban inactive",
            expected_status=NOT_AFFECTED,
            ban_type="DECLARED",
            no_parking_side="EVEN",
            parked_side="EVEN",
            declared_ban_active=False,
        )
    )


    # --------------------------------------------------------
    # TEST 5
    #
    # Worcester dataset marks segment NON-APPLICABLE.
    #
    # Expected: NOT_AFFECTED
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 5 - Non-applicable segment",
            expected_status=NOT_AFFECTED,
            ban_type="NON-APPLICABLE",
            no_parking_side="NONE",
            parked_side="ODD",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 6
    #
    # Special restriction.
    # We deliberately refuse to guess what SPEC means.
    #
    # Expected: VERIFY_RULE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 6 - Special restriction",
            expected_status=VERIFY_RULE,
            ban_type="DECLARED",
            no_parking_side="SPEC",
            parked_side="ODD",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 7
    #
    # Restriction is active but Side is missing.
    #
    # Expected: VERIFY_RULE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 7 - Missing restriction side",
            expected_status=VERIFY_RULE,
            ban_type="DECLARED",
            no_parking_side="",
            parked_side="EVEN",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 8
    #
    # Resident does not know which side the vehicle
    # is parked on.
    #
    # Expected: VERIFY_RULE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 8 - Resident unsure of side",
            expected_status=VERIFY_RULE,
            ban_type="DECLARED",
            no_parking_side="EVEN",
            parked_side="UNSURE",
            declared_ban_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 9
    #
    # Permanent restriction.
    # Snow emergency is active.
    # Both sides prohibited.
    #
    # Expected: MUST_MOVE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 9 - Permanent ban during snow emergency",
            expected_status=MUST_MOVE,
            ban_type="PERMANENT",
            no_parking_side="BOTH",
            parked_side="ODD",
            snow_emergency_active=True,
        )
    )


    # --------------------------------------------------------
    # TEST 10
    #
    # Permanent restriction.
    # No snow emergency.
    # Permanent time restriction is active.
    # EVEN side prohibited and vehicle is on EVEN.
    #
    # Expected: MUST_MOVE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 10 - Permanent time restriction",
            expected_status=MUST_MOVE,
            ban_type="PERMANENT",
            no_parking_side="EVEN",
            parked_side="EVEN",
            permanent_time_restriction_active=True,
        )
    )


    # --------------------------------------------------
    # --------------------------------------------------------
    # TEST 11
    #
    # Permanent restriction exists, but neither the
    # permanent time restriction nor a snow emergency
    # is currently active.
    #
    # Expected: NOT_AFFECTED
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 11 - Permanent restriction inactive",
            expected_status=NOT_AFFECTED,
            ban_type="PERMANENT",
            no_parking_side="EVEN",
            parked_side="EVEN",
            snow_emergency_active=False,
            permanent_time_restriction_active=False,
        )
    )

    # --------------------------------------------------------
    # TEST 12
    #
    # State-owned road with no Worcester winter parking ban.
    #
    # Expected: NOT_AFFECTED
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 12 - State-owned road",
            expected_status=NOT_AFFECTED,
            ban_type=(
                "STATE OWNED - NO WORCESTER "
                "WINTER PARKING BAN"
            ),
            no_parking_side="NONE",
            parked_side="ODD",
            declared_ban_active=True,
        )
    )

    # --------------------------------------------------------
    # TEST 13
    #
    # Unknown ban type.
    #
    # Expected: VERIFY_RULE
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 13 - Unknown ban type",
            expected_status=VERIFY_RULE,
            ban_type="UNKNOWN TYPE",
            no_parking_side="EVEN",
            parked_side="EVEN",
            declared_ban_active=True,
        )
    )

    # --------------------------------------------------------
    # TEST 14
    #
    # Active declared restriction, but the GIS indicates
    # that no side is prohibited.
    #
    # Expected: NOT_AFFECTED
    # --------------------------------------------------------

    results.append(
        run_test(
            test_name="Test 14 - No prohibited side",
            expected_status=NOT_AFFECTED,
            ban_type="DECLARED",
            no_parking_side="NONE",
            parked_side="EVEN",
            declared_ban_active=True,
        )
    )

    # ========================================================
    # TEST SUMMARY
    # ========================================================

    total_tests = len(results)
    passed_tests = sum(results)
    failed_tests = total_tests - passed_tests

    print()
    print("================================")
    print("BANREADY TEST SUMMARY")
    print("================================")
    print()

    print(f"Total tests: {total_tests}")
    print(f"Passed:      {passed_tests}")
    print(f"Failed:      {failed_tests}")
    print()

    if failed_tests == 0:
        print("ALL TESTS PASSED")
        print()
        print(
            "BanReady's basic winter parking-ban "
            "rule engine is working as expected."
        )
    else:
        print("SOME TESTS FAILED")
        print()
        print(
            "Do not connect the rule engine to the "
            "mobile app until the failures are fixed."
        )


# ============================================================
# RUN TEST SUITE
# ============================================================

if __name__ == "__main__":
    main()