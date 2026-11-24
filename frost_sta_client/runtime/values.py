"""Read and write structural values. Navigation is handled by Entity."""

from datetime import datetime
from enum import Enum

import geojson

from frost_sta_client.runtime.geo import (
    coerce_geometry,
    geometry_to_json,
    is_geo_media,
    is_geography,
)
from frost_sta_client.runtime.registry import is_collection, resolve_declared, unwrap_type
from frost_sta_client.runtime.timeutil import (
    format_interval,
    is_temporal,
    is_temporal_edm,
    read_edm,
    read_interval,
    read_time,
    write_edm,
    write_time,
)


def _read_complex(target, raw, property_name):
    if isinstance(raw, target):
        return raw
    if isinstance(raw, dict):
        return target.from_json(raw)
    if _accepts_time(target):
        built = _time_as_complex(target, raw, property_name)
        if built is not None:
            return built
    raise ValueError("{} should be a {}".format(property_name, target.__name__))


class _OmitType:
    """Marker for a value that must not appear in JSON."""


OMIT = _OmitType()


def read_structural(spec, raw, entity):
    """Convert a JSON value into the Python value stored on an entity."""
    if raw is None:
        if not spec.nullable:
            raise ValueError("{} must not be None".format(spec.python_name))
        return None
    if is_collection(spec.edm):
        return _read_collection(spec, raw, entity)
    if is_geography(spec.edm):
        return coerce_geometry(raw, spec.edm, spec.python_name)
    if is_temporal(spec):
        return read_time(spec, raw)
    target = resolve_declared(spec.edm, entity)
    if target is not None and isinstance(target, type) and issubclass(target, Enum):
        return _read_enum(target, raw, spec.python_name)
    if _is_complex(target):
        return _read_complex(target, raw, spec.python_name)
    if spec.edm == "Edm.String":
        if not isinstance(raw, str):
            raise ValueError("{} should be of type str".format(spec.python_name))
        return raw
    if spec.edm.startswith("Edm.Int"):
        if isinstance(raw, bool) or not isinstance(raw, int):
            raise ValueError("{} should be an integer".format(spec.python_name))
        return raw
    if spec.edm == "Edm.Boolean":
        if not isinstance(raw, bool):
            raise ValueError("{} should be a boolean".format(spec.python_name))
        return raw
    if spec.edm in ("Edm.Double", "Edm.Decimal", "Edm.Single"):
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise ValueError("{} should be a number".format(spec.python_name))
        return raw
    return _read_untyped(spec, raw, entity)


def write_structural(spec, value, service, owner=None):
    """Convert a stored value to JSON, or OMIT when it must be left out."""
    if value is None:
        return OMIT
    if is_collection(spec.edm):
        if len(value) == 0:
            return OMIT
        return [_write_item(unwrap_type(spec.edm), item, service, owner) for item in value]
    if is_geography(spec.edm) or isinstance(value, geojson.GeoJSON):
        return geometry_to_json(value)
    if is_temporal(spec):
        return write_time(spec, value)
    target = resolve_declared(spec.edm, owner)
    if target is not None and isinstance(target, type) and issubclass(target, Enum):
        if isinstance(value, Enum):
            return value.value
        return value
    if hasattr(value, "to_json") and _is_complex(target):
        return value.to_json(service)
    return value


def structural_equal(spec, left, right):
    if is_collection(spec.edm):
        left = [] if not left else left
        right = [] if not right else right
    if is_geography(spec.edm):
        if left is not None:
            left = geometry_to_json(left)
        if right is not None:
            right = geometry_to_json(right)
    return left == right


def _read_collection(spec, raw, owner=None):
    if isinstance(raw, dict) and isinstance(raw.get("value"), list):
        raw = raw["value"]
    if not isinstance(raw, list):
        raise ValueError("{} should be a list".format(spec.python_name))
    inner = unwrap_type(spec.edm)
    target = resolve_declared(inner, owner)
    if target is not None and isinstance(target, type) and issubclass(target, Enum):
        return [_read_enum(target, item, spec.python_name) for item in raw]
    if _is_complex(target):
        return [_read_complex(target, item, spec.python_name) for item in raw]
    if inner == "Edm.String":
        for item in raw:
            if not isinstance(item, str):
                raise ValueError("{} must be a list of str".format(spec.python_name))
        return list(raw)
    if is_geography(inner):
        return [coerce_geometry(item, inner, spec.python_name) for item in raw]
    if is_temporal_edm(inner):
        return [read_edm(inner, item, spec.python_name) for item in raw]
    return list(raw)


def _write_item(inner, item, service, owner=None):
    target = resolve_declared(inner, owner)
    if is_geography(inner) or isinstance(item, geojson.GeoJSON):
        return geometry_to_json(item)
    if hasattr(item, "to_json") and (_is_complex(target) or _is_entity(target)):
        return item.to_json(service)
    if isinstance(item, Enum):
        return item.value
    if is_temporal_edm(inner):
        return write_edm(inner, item, inner)
    return item


def _accepts_time(target):
    properties = getattr(target, "__properties__", ())
    names = {spec.wire for spec in properties}
    return "start" in names and any(is_temporal(spec) for spec in properties)


def _time_as_complex(target, raw, property_name):
    """Build a start/end complex value from an instant, an interval, or a pair."""
    parsed = read_interval(raw, property_name)
    if parsed is None:
        return None
    start, end = parsed
    payload = {"start": start}
    if end is not None:
        payload["end"] = end
    return target.from_json(payload)


def wire_time(value):
    """One data-array cell: an ISO instant, or start/end in that form."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return write_edm("Edm.DateTimeOffset", value, "time")
    if isinstance(value, tuple):
        if len(value) != 2:
            raise ValueError("time must be an instant or a pair of instants")
        return format_interval(value[0], value[1], "time")
    start = getattr(value, "start", None)
    end = getattr(value, "end", None)
    if start is None and end is None:
        if isinstance(value, str):
            parsed = read_interval(value, "time")
            if parsed is None:
                return value
            return format_interval(parsed[0], parsed[1], "time")
        return value
    return format_interval(start, end, "time")


def _read_enum(enum_cls, raw, property_name):
    if isinstance(raw, enum_cls):
        return raw
    for member in enum_cls:
        if raw == member.value or raw == member.name:
            return member
    raise ValueError("{} should be a {}".format(property_name, enum_cls.__name__))


def _read_untyped(spec, raw, entity):
    if isinstance(raw, geojson.GeoJSON):
        return raw
    encoding = None
    if entity is not None:
        encoding = entity._values.get("encoding_type")
    if is_geo_media(encoding) and isinstance(raw, dict) and "type" in raw:
        return coerce_geometry(raw, "Edm.Geography", spec.python_name)
    return raw


def _is_complex(target):
    return isinstance(target, type) and getattr(target, "__is_entity__", None) is False


def _is_entity(target):
    return isinstance(target, type) and getattr(target, "__is_entity__", None) is True
