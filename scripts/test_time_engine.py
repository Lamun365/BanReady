"""
Tests for the permanent 2-6 a.m. winter ban timing.

Run from the project folder:

    python -m scripts.test_time_engine
"""

from datetime import datetime, timezone

from backend.app.services.time_engine import (
    is_permanent_ban_time,
)


TESTS = [
    # (description, time, expected)
    ("January 3 a.m.",               datetime(2027, 1, 15, 3, 0),  True),
    ("January noon",                 datetime(2027, 1, 15, 12, 0), False),
    ("1:59 a.m. (before window)",    datetime(2027, 1, 15, 1, 59), False),
    ("2:00 a.m. (window starts)",    datetime(2027, 1, 15, 2, 0),  True),
    ("5:59 a.m. (last minute)",      datetime(2027, 1, 15, 5, 59), True),
    ("6:00 a.m. (window over)",      datetime(2027, 1, 15, 6, 0),  False),
    ("Dec 1, 2 a.m. (season starts)", datetime(2026, 12, 1, 2, 0), True),
    ("Nov 30, 3 a.m. (before season)", datetime(2026, 11, 30, 3, 0), False),
    ("Apr 30, 5:59 a.m. (season end)", datetime(2027, 4, 30, 5, 59), True),
    ("May 1, 3 a.m. (after season)", datetime(2027, 5, 1, 3, 0),  False),
    ("July 3 a.m.",                  datetime(2027, 7, 15, 3, 0),  False),
    # 08:00 UTC on Jan 15 = 3:00 a.m. in Worcester (EST, UTC-5)
    ("UTC time converted to Worcester", datetime(2027, 1, 15, 8, 0, tzinfo=timezone.utc), True),
]


def main():
    passed = 0

    for description, when, expected in TESTS:
        result = is_permanent_ban_time(when)
        ok = result == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {description:34} -> {result}")

    print()
    print(f"Total tests: {len(TESTS)}")
    print(f"Passed:      {passed}")
    print(f"Failed:      {len(TESTS) - passed}")

    if passed == len(TESTS):
        print()
        print("ALL TIME ENGINE TESTS PASSED")


if __name__ == "__main__":
    main()
