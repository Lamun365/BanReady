from datetime import datetime
from zoneinfo import ZoneInfo


# ============================================================
# Worcester permanent winter parking ban timing
#
# Dec 1 - Apr 30, 2:00 a.m. to 6:00 a.m. (Worcester time)
# ============================================================

# Worcester uses Eastern Time (EST in winter, EDT in summer)
WORCESTER_TZ = ZoneInfo("America/New_York")

PERMANENT_BAN_MONTHS = {12, 1, 2, 3, 4}
PERMANENT_BAN_START_HOUR = 2   # 2:00 a.m.
PERMANENT_BAN_END_HOUR = 6     # 6:00 a.m. (not included)


def to_worcester_time(check_time=None):
    """Return the given time (or right now) in Worcester time."""
    if check_time is None:
        return datetime.now(WORCESTER_TZ)

    if check_time.tzinfo is None:
        # A time with no time zone is treated as Worcester local time
        return check_time.replace(tzinfo=WORCESTER_TZ)

    return check_time.astimezone(WORCESTER_TZ)


def is_permanent_ban_time(check_time=None):
    """True if the permanent winter ban (Dec 1 - Apr 30, 2-6 a.m.) is in effect."""
    local_time = to_worcester_time(check_time)

    in_season = local_time.month in PERMANENT_BAN_MONTHS

    in_hours = (
        PERMANENT_BAN_START_HOUR
        <= local_time.hour
        < PERMANENT_BAN_END_HOUR
    )

    return in_season and in_hours
