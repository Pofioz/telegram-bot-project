# bot/core/helpers.py
import re
from datetime import datetime, timedelta

def parse_time(time_str: str) -> datetime:
    """Parses a time string like '1d5h30m' and returns a future datetime object."""
    regex = re.compile(r"(\d+)([dhm])")
    matches = regex.findall(time_str.lower())

    if not matches:
        return None

    time_delta_args = {}
    for amount, unit in matches:
        amount = int(amount)
        if unit == 'd':
            time_delta_args['days'] = amount
        elif unit == 'h':
            time_delta_args['hours'] = amount
        elif unit == 'm':
            time_delta_args['minutes'] = amount

    return datetime.now() + timedelta(**time_delta_args)