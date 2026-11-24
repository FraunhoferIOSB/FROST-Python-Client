"""Parse and write OData time values.

A point in time is a timezone-aware datetime. A date is datetime.date.
A time of day is datetime.time. A duration is datetime.timedelta.
Equality uses those values, so two ISO spellings of one instant match.
Writing emits one ISO form for each of them.
"""

import re
from datetime import date, datetime, time, timedelta, timezone

# SensorThings names that some documents still declare as Edm.String.
TEMPORAL_NAMES = frozenset((
    "phenomenonTime",
    "resultTime",
    "validTime",
    "time",
    "creationTime",
))

_KIND = {
    "Edm.DateTimeOffset": "datetime",
    "Edm.Date": "date",
    "Edm.TimeOfDay": "time",
    "Edm.Duration": "duration",
}

_DURATION = re.compile(
    r"^(-)?P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$"
)


def is_temporal(spec):
    if spec.edm in _KIND:
        return True
    return spec.edm == "Edm.String" and spec.wire in TEMPORAL_NAMES


def is_temporal_edm(edm):
    return edm in _KIND


def read_time(spec, raw):
    """Return the Python value stored for one temporal property."""
    kind = _KIND.get(spec.edm)
    if kind is not None:
        return _read_kind(kind, raw, spec.python_name)
    return _read_named(raw, spec.python_name)


def write_time(spec, value):
    """Return the fixed ISO form of a stored temporal value."""
    kind = _KIND.get(spec.edm)
    if kind is not None:
        return _write_kind(kind, value, spec.python_name)
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError(
                "{} must be an instant or a pair of instants".format(spec.python_name)
            )
        return format_interval(value[0], value[1], spec.python_name)
    return _write_datetime(value, spec.python_name)


def read_edm(edm, raw, property_name):
    kind = _KIND.get(edm)
    if kind is None:
        raise ValueError("{} must be a time value".format(property_name))
    return _read_kind(kind, raw, property_name)


def write_edm(edm, value, property_name):
    kind = _KIND.get(edm)
    if kind is None:
        raise ValueError("{} must be a time value".format(property_name))
    return _write_kind(kind, value, property_name)


def read_interval(raw, property_name):
    """Return ``(start, end)`` for an instant or a SensorThings interval.

    ``end`` is None for a single instant. A duration boundary is applied so
    the result is a pair of instants. An unrecognised shape returns None.
    """
    if isinstance(raw, datetime):
        return _read_datetime(raw, property_name), None
    if isinstance(raw, (list, tuple)):
        return _read_pair(raw, property_name)
    if isinstance(raw, str):
        return _read_interval_text(raw, property_name)
    return None


def format_interval(start, end, property_name):
    """Write an instant, or ``start/end``, in the fixed UTC form."""
    left = _write_datetime(start, property_name)
    if end is None:
        return left
    return "{}/{}".format(left, _write_datetime(end, property_name))


def _read_named(raw, property_name):
    parsed = read_interval(raw, property_name)
    if parsed is None:
        raise ValueError("{} must be an instant or an interval".format(property_name))
    start, end = parsed
    if end is None:
        return start
    return (start, end)


def _read_kind(kind, raw, property_name):
    if kind == "datetime":
        return _read_datetime(raw, property_name)
    if kind == "date":
        return _read_date(raw, property_name)
    if kind == "time":
        return _read_timeofday(raw, property_name)
    return _read_duration(raw, property_name)


def _write_kind(kind, value, property_name):
    if kind == "datetime":
        return _write_datetime(value, property_name)
    if kind == "date":
        return _write_date(value, property_name)
    if kind == "time":
        return _write_timeofday(value, property_name)
    return _write_duration(value, property_name)


def _read_pair(raw, property_name):
    if len(raw) != 2:
        raise ValueError(
            "{} must be an instant or a pair of instants".format(property_name)
        )
    return (
        _read_datetime(raw[0], property_name),
        _read_datetime(raw[1], property_name),
    )


def _read_interval_text(text, property_name):
    parts = text.split("/")
    if len(parts) == 1:
        return _read_datetime(text.strip(), property_name), None
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise ValueError("{} must be an instant or an interval".format(property_name))
    left = _boundary(parts[0].strip(), property_name)
    right = _boundary(parts[1].strip(), property_name)
    return _combine(left, right, property_name)


def _boundary(text, property_name):
    if text.startswith("P") or text.startswith("-P"):
        return "duration", _read_duration(text, property_name)
    return "datetime", _read_datetime(text, property_name)


def _combine(left, right, property_name):
    left_kind, left_value = left
    right_kind, right_value = right
    if left_kind == "datetime" and right_kind == "datetime":
        return left_value, right_value
    if left_kind == "datetime" and right_kind == "duration":
        return left_value, left_value + right_value
    if left_kind == "duration" and right_kind == "datetime":
        return right_value - left_value, right_value
    raise ValueError("{} must be an instant or an interval".format(property_name))


def _read_datetime(raw, property_name):
    if isinstance(raw, datetime):
        _require_aware(raw, property_name)
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if text.endswith(("z", "Z")):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            raise ValueError(
                "{} must be a timezone-aware datetime".format(property_name)
            )
        _require_aware(parsed, property_name)
        return parsed
    raise ValueError("{} must be a timezone-aware datetime".format(property_name))


def _require_aware(value, property_name):
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("{} must be a timezone-aware datetime".format(property_name))


def _write_datetime(value, property_name):
    if not isinstance(value, datetime):
        raise ValueError("{} must be a timezone-aware datetime".format(property_name))
    _require_aware(value, property_name)
    utc = value.astimezone(timezone.utc)
    text = utc.strftime("%Y-%m-%dT%H:%M:%S")
    if utc.microsecond:
        text = "{}.{}".format(text, _fraction(utc.microsecond))
    return text + "Z"


def _read_date(raw, property_name):
    if isinstance(raw, date) and not isinstance(raw, datetime):
        return raw
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw.strip())
        except ValueError:
            raise ValueError("{} must be a date".format(property_name))
    raise ValueError("{} must be a date".format(property_name))


def _write_date(value, property_name):
    if isinstance(value, datetime) or not isinstance(value, date):
        raise ValueError("{} must be a date".format(property_name))
    return value.isoformat()


def _read_timeofday(raw, property_name):
    if isinstance(raw, time):
        _require_clock(raw, property_name)
        return raw
    if isinstance(raw, str):
        try:
            parsed = time.fromisoformat(raw.strip())
        except ValueError:
            raise ValueError("{} must be a time of day".format(property_name))
        _require_clock(parsed, property_name)
        return parsed
    raise ValueError("{} must be a time of day".format(property_name))


def _require_clock(value, property_name):
    if value.tzinfo is not None:
        raise ValueError("{} must be a time of day".format(property_name))


def _write_timeofday(value, property_name):
    if not isinstance(value, time) or value.tzinfo is not None:
        raise ValueError("{} must be a time of day".format(property_name))
    text = value.strftime("%H:%M:%S")
    if value.microsecond:
        text = "{}.{}".format(text, _fraction(value.microsecond))
    return text


def _read_duration(raw, property_name):
    if isinstance(raw, timedelta):
        return raw
    if not isinstance(raw, str):
        raise ValueError("{} must be an ISO-8601 duration".format(property_name))
    return _parse_duration(raw.strip(), property_name)


def _parse_duration(text, property_name):
    match = _DURATION.match(text)
    if match is None:
        raise ValueError("{} must be an ISO-8601 duration".format(property_name))
    sign, days, hours, minutes, seconds = match.groups()
    if _duration_empty(text, days, hours, minutes, seconds):
        raise ValueError("{} must be an ISO-8601 duration".format(property_name))
    whole, micros = _split_seconds(seconds)
    try:
        value = timedelta(
            days=int(days or 0),
            hours=int(hours or 0),
            minutes=int(minutes or 0),
            seconds=whole,
            microseconds=micros,
        )
    except OverflowError:
        raise ValueError("{} must be an ISO-8601 duration".format(property_name))
    if sign:
        return -value
    return value


def _duration_empty(text, days, hours, minutes, seconds):
    if days is None and hours is None and minutes is None and seconds is None:
        return True
    return "T" in text and hours is None and minutes is None and seconds is None


def _split_seconds(text):
    if not text:
        return 0, 0
    if "." not in text:
        return int(text), 0
    whole, frac = text.split(".", 1)
    return int(whole or "0"), int((frac + "000000")[:6])


def _write_duration(value, property_name):
    if not isinstance(value, timedelta):
        raise ValueError("{} must be an ISO-8601 duration".format(property_name))
    sign = ""
    if value < timedelta(0):
        sign = "-"
        value = -value
    hours, remainder = divmod(value.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    body = _duration_body(value.days, hours, minutes, seconds, value.microseconds)
    return sign + body


def _duration_body(days, hours, minutes, seconds, micros):
    body = "P"
    if days:
        body += "{}D".format(days)
    clock = ""
    if hours:
        clock += "{}H".format(hours)
    if minutes:
        clock += "{}M".format(minutes)
    if seconds or micros or (not clock and not days):
        clock += _format_seconds(seconds, micros)
    if clock:
        body += "T" + clock
    return body


def _format_seconds(seconds, micros):
    if not micros:
        return "{}S".format(seconds)
    return "{}.{}S".format(seconds, _fraction(micros))


def _fraction(micros):
    return "{:06d}".format(micros).rstrip("0")
