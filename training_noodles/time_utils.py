import datetime


def convert_unix_time_to_iso(t, tz=None):
    # Convert to datetime
    d = datetime.datetime.fromtimestamp(t, tz=tz)

    # Return ISO format
    return d.isoformat()
