# Working time (minutes)
DEFAULT_MONTHLY_TARGET_MINUTES = round(40 * 4.35 * 60)  # 40h/week * 4.35 weeks/month
MAX_DURATION_MINUTES = 31 * 24 * 60  # upper bound for a planning period of 31 days

# Target working time tolerances (minutes)
TOLERANCE_LESS = 460
TOLERANCE_MORE = TOLERANCE_LESS

# Scheduling
MAX_CONSECUTIVE_DAYS = 5
SPECIAL_NIGHT_SHIFT_INDEX = 7  # N5: special form of night shift

# Weekdays (isoweekday: Monday=1 ... Sunday=7)
WEEKDAYS = [1, 2, 3, 4, 5]
WEEKEND_DAYS = [6, 7]
NEAR_WEEKEND_DAYS = [5, 6, 7]
