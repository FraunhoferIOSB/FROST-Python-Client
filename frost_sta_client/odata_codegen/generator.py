from __future__ import annotations

import os
from typing import Any, Dict, List, Tuple

from .parser import parse_metadata


_EDM_TO_PY: Dict[str, str] = {
    "Edm.String": "str",
    "Edm.Int16": "int",
    "Edm.Int32": "int",
    "Edm.Int64": "int",
    "Edm.SByte": "int",
    "Edm.Byte": "int",
    "Edm.Decimal": "Decimal",
    "Edm.Double": "float",
    "Edm.Single": "float",
    "Edm.Boolean": "bool",
    "Edm.Guid": "UUID",
    "Edm.DateTimeOffset": "datetime",
    "Edm.Date": "date",
    "Edm.TimeOfDay": "time",
    "Edm.Duration": "timedelta",
    "Edm.Binary": "bytes",
    "Edm.Stream": "bytes",
    "Edm.Untyped": "Any",
    # Geospatial
    "Edm.Geometry": "dict",
    "Edm.Geography": "dict",
    "Edm.GeographyPoint": "dict",
    "Edm.GeometryPoint": "dict",
    "Edm.GeographyLineString": "dict",
    "Edm.GeometryLineString": "dict",
    "Edm.GeographyPolygon": "dict",
    "Edm.GeometryPolygon": "dict",
    "Edm.GeographyMultiPoint": "dict",
    "Edm.GeometryMultiPoint": "dict",
    "Edm.GeographyMultiLineString": "dict",
    "Edm.GeometryMultiLineString": "dict",
    "Edm.GeographyMultiPolygon": "dict",
    "Edm.GeometryMultiPolygon": "dict",
    "Edm.GeographyCollection": "dict",
    "Edm.GeometryCollection": "dict",
}


def _last_segment(fqn: str) -> str:
    return fqn.split(".")[-1]


def _split_collection(type_str: str) -> Tuple[bool, str]:
    s = (type_str or "").strip()
    if s.startswith("Collection(") and s.endswith(")"):
        return True, s[len("Collection("):-1]
    return False, s


def _resolve_underlying(type_str: str, model: Dict[str, Any]) -> str:
    # If this is a TypeDefinition, resolve to its underlying EDM type; otherwise return as-is
    if type_str in model.get("type_defs", {}):
        return model["type_defs"][type_str].get("underlying", type_str)
    return type_str


def _is_real_complex(type_str: str, model: Dict[str, Any]) -> bool:
    """Return True if type_str is a ComplexType (excluding open types like Object/ANY)."""
    return type_str in model.get("complex_types", {}) and _last_segment(type_str) not in {"Object", "ANY"}


def _is_edm_datetimeoffset(type_str: str, model: Dict[str, Any]) -> bool:
    is_coll, inner = _split_collection(type_str)
    underlying = _resolve_underlying(inner, model)
    return underlying == "Edm.DateTimeOffset"

def _is_edm_date(type_str: str, model: Dict[str, Any]) -> bool:
    is_coll, inner = _split_collection(type_str)
    underlying = _resolve_underlying(inner, model)
    return underlying == "Edm.Date"

def _is_edm_time(type_str: str, model: Dict[str, Any]) -> bool:
    is_coll, inner = _split_collection(type_str)
    underlying = _resolve_underlying(inner, model)
    return underlying == "Edm.TimeOfDay"

def _is_edm_duration(type_str: str, model: Dict[str, Any]) -> bool:
    is_coll, inner = _split_collection(type_str)
    underlying = _resolve_underlying(inner, model)
    return underlying == "Edm.Duration"

def _is_edm_geospatial(type_str: str, model: Dict[str, Any]) -> bool:
    is_coll, inner = _split_collection(type_str)
    underlying = _resolve_underlying(inner, model)
    if underlying in ("Edm.Geometry", "Edm.Geography"):
        return True
    return underlying.startswith("Edm.Geometry") or underlying.startswith("Edm.Geography")

def _geo_expected_kind(underlying: str) -> str | None:
    mapping = {
        "Edm.GeometryPoint": "Point",
        "Edm.GeographyPoint": "Point",
        "Edm.GeometryLineString": "LineString",
        "Edm.GeographyLineString": "LineString",
        "Edm.GeometryPolygon": "Polygon",
        "Edm.GeographyPolygon": "Polygon",
        "Edm.GeometryMultiPoint": "MultiPoint",
        "Edm.GeographyMultiPoint": "MultiPoint",
        "Edm.GeometryMultiLineString": "MultiLineString",
        "Edm.GeographyMultiLineString": "MultiLineString",
        "Edm.GeometryMultiPolygon": "MultiPolygon",
        "Edm.GeographyMultiPolygon": "MultiPolygon",
        "Edm.GeometryCollection": "GeometryCollection",
        "Edm.GeographyCollection": "GeometryCollection",
    }
    return mapping.get(underlying)


def _to_py_hint(prop_name: str, type_str: str, model: Dict[str, Any], nullable: bool = True) -> Tuple[str, str, bool]:
    """Return (annotation, base_for_check, is_collection).

    - annotation: string used in function signature, e.g. Optional[str] or List[int]
    - base_for_check: runtime isinstance check target (e.g. str, int, ClassName) or 'Any' to skip
    - is_collection: whether the type is a collection
    """
    is_coll, inner = _split_collection(type_str)
    underlying = _resolve_underlying(inner, model)
    if underlying.startswith("Edm."):
        base_py = _EDM_TO_PY.get(underlying, "Any")
    else:
        last = _last_segment(underlying)
        # Open types or unknown complex types should remain flexible
        if last in {"Object", "ANY"}:
            base_py = "Any"
        else:
            base_py = last
    if underlying == "Edm.DateTimeOffset":
        hint_base = "Union[datetime, str]"
    elif underlying == "Edm.Date":
        hint_base = "Union[date, str]"
    elif underlying == "Edm.TimeOfDay":
        hint_base = "Union[time, str]"
    elif underlying == "Edm.Duration":
        hint_base = "Union[timedelta, str]"
    elif underlying.startswith("Edm.Geometry") or underlying.startswith("Edm.Geography"):
        # Accept dict (GeoJSON-like) or JSON string; canonical storage is dict
        hint_base = "Union[dict, str]"
    else:
        hint_base = base_py
    inner_ann = f"List[{hint_base}]" if is_coll else f"{hint_base}"
    ann = f"Optional[{inner_ann}]" if nullable else inner_ann
    return ann, base_py, is_coll


def generate_from_metadata(xml_text: str, out_dir: str, module_name: str = "datamodel", source_url: str = "", odata_version: str = "") -> str:
    """Generate Python source for the OData model; classes align with frost_sta_client.model patterns.

    - Entities inherit from frost_sta_client.model.entity.Entity
    - Navigation collections use frost_sta_client.model.ext.entity_list.EntityList
    - __getstate__/__setstate__ follow SensorThings/OData JSON field names
    - Equality mirrors base behaviour plus scalar/complex property checks
    - Service propagation to child objects/lists is provided
    - ComplexTypes are type with corresponding Python class in entity properties and type is enforced in setter methods.
      Furthermore, ComplexTypes and collections are correctly (de)serialized in __getstate__/__setstate__.
      Nullability (Nullable) is respected in annotations, constructor signatures and setter validations.

    Returns: absolute path of the generated module file.
    """
    model = parse_metadata(xml_text)


    def snake(name: str) -> str:
        # Convert PascalCase/camelCase to snake_case for attribute names
        out: List[str] = []
        prev_is_lower = False
        for ch in name:
            if ch.isupper():
                if prev_is_lower:
                    out.append('_')
                out.append(ch.lower())
                prev_is_lower = False
            else:
                out.append(ch)
                prev_is_lower = ch.isalpha()
        return ''.join(out)


    lines: List[str] = []
    lines.append("from __future__ import annotations")
    lines.append("# Auto-generated by FROST-STA OData codegen. Do not edit manually.")
    if source_url:
        lines.append(f"# Source: {source_url}")
    if odata_version:
        lines.append(f"# OData Version: {odata_version}")
    lines.append("from typing import Any, List, Optional, Union")
    lines.append("from datetime import datetime, date, time, timedelta")
    lines.append("from dateutil.parser import isoparse")
    lines.append("from decimal import Decimal")
    lines.append("from uuid import UUID")
    lines.append("from frost_sta_client import utils")
    lines.append("from frost_sta_client.model.entity import Entity")
    lines.append("from frost_sta_client.model.ext.entity_list import EntityList")
    lines.append("")

    exported: List[str] = []

    # Complex Types
    for fqn, cplx in model.get("complex_types", {}).items():
        c_name = cplx["name"]
        exported.append(c_name)
        props = cplx.get("properties", [])
        # Build typed __init__ signature for complex types (EDM primitives get concrete types)
        arg_parts = []
        for p in props:
            nullable = p.get('nullable', True)
            ann, _base_check, _is_coll = _to_py_hint(p['name'], p['type'], model, nullable)
            if nullable:
                arg_parts.append(f"{snake(p['name'])}: {ann} = None")
            else:
                arg_parts.append(f"{snake(p['name'])}: {ann}")
        args = ", ".join(arg_parts)
        lines.append(f"class {c_name}:")
        lines.append(f"    def __init__(self, {args}):" if args else "    def __init__(self):")
        if not props:
            lines.append("        pass")
        else:
            for p in props:
                on = p['name']
                sn = snake(on)
                lines.append(f"        self.{sn} = {sn}")
        lines.append("")

        # Properties with getters/setters and type checks for complex types
        for p in props:
            on = p['name']
            sn = snake(on)
            nullable = p.get('nullable', True)
            _ann, base_check, is_coll = _to_py_hint(on, p['type'], model, nullable)
            lines.append("    @property")
            lines.append(f"    def {sn}(self):")
            lines.append(f"        return getattr(self, '_{sn}', None)")
            lines.append("")
            lines.append(f"    @{sn}.setter")
            lines.append(f"    def {sn}(self, value):")
            is_coll_raw, inner_raw = _split_collection(p['type'])
            if _is_edm_datetimeoffset(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of datetime or ISO-8601 string')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, datetime):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(isoparse(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of datetime or ISO-8601 string')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, datetime):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = isoparse(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 string or datetime')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type datetime or ISO-8601 string!')")
            elif _is_edm_date(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of date or ISO-8601 date string (YYYY-MM-DD)')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, date):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(date.fromisoformat(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 date string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of date or ISO-8601 date string (YYYY-MM-DD)')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, date):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = date.fromisoformat(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 date string (YYYY-MM-DD) or date')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type date or ISO-8601 date string (YYYY-MM-DD)!')")
            elif _is_edm_time(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of time or ISO-8601 time string')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, time):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(time.fromisoformat(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 time string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of time or ISO-8601 time string')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, time):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = time.fromisoformat(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 time string or time')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type time or ISO-8601 time string!')")
            elif _is_edm_duration(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of timedelta or ISO-8601 duration string')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, timedelta):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(utils.parse_duration_to_timedelta(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 duration string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of timedelta or ISO-8601 duration string')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, timedelta):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = utils.parse_duration_to_timedelta(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 duration string or timedelta')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type timedelta or ISO-8601 duration string!')")
            elif _is_edm_geospatial(inner_raw, model):
                expected = _geo_expected_kind(_resolve_underlying(inner_raw, model))
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of GeoJSON geometry dicts or JSON strings')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"            try:")
                    lines.append(f"                tmp_{sn}.append(utils.parse_geometry(_x{if_expected}))")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} contains an invalid geometry')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"        try:")
                    lines.append(f"            self._{sn} = utils.parse_geometry(value{if_expected})")
                    lines.append(f"        except ValueError:")
                    lines.append(f"            raise ValueError('{sn} should be a valid GeoJSON geometry')")
            elif base_check != "Any":
                if is_coll:
                    if nullable:
                        lines.append(f"        if value is not None and (not isinstance(value, list) or not all(isinstance(x, {base_check}) for x in value)):")
                        lines.append(f"            raise ValueError('{sn} should be a list of {base_check}')")
                        lines.append(f"        self._{sn} = value")
                    else:
                        lines.append(f"        if value is None:")
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                        lines.append(f"        if not isinstance(value, list) or not all(isinstance(x, {base_check}) for x in value):")
                        lines.append(f"            raise ValueError('{sn} should be a list of {base_check}')")
                        lines.append(f"        self._{sn} = value")
                else:
                    if nullable:
                        lines.append(f"        if value is not None and not isinstance(value, {base_check}):")
                        lines.append(f"            raise ValueError('{sn} should be of type {base_check}!')")
                        lines.append(f"        self._{sn} = value")
                    else:
                        lines.append(f"        if value is None:")
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                        lines.append(f"        if not isinstance(value, {base_check}):")
                        lines.append(f"            raise ValueError('{sn} should be of type {base_check}!')")
                        lines.append(f"        self._{sn} = value")
            else:
                if nullable:
                    lines.append(f"        self._{sn} = value")
                else:
                    lines.append(f"        if value is None:")
                    lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        self._{sn} = value")
            lines.append("")

        lines.append("    def __getstate__(self):")
        lines.append("        d = {}")
        for p in props:
            on = p['name']
            sn = snake(on)
            is_coll, inner = _split_collection(p['type'])
            if _is_edm_datetimeoffset(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            d['{on}'] = [utils.parse_datetime(x) for x in self.{sn}]")
                else:
                    lines.append(f"            d['{on}'] = utils.parse_datetime(self.{sn})")
            elif _is_edm_date(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            d['{on}'] = [utils.parse_date(x) for x in self.{sn}]")
                else:
                    lines.append(f"            d['{on}'] = utils.parse_date(self.{sn})")
            elif _is_edm_time(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            d['{on}'] = [utils.parse_time(x) for x in self.{sn}]")
                else:
                    lines.append(f"            d['{on}'] = utils.parse_time(self.{sn})")
            elif _is_edm_duration(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            d['{on}'] = [utils.parse_duration(x) for x in self.{sn}]")
                else:
                    lines.append(f"            d['{on}'] = utils.parse_duration(self.{sn})")
            elif _is_edm_geospatial(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            d['{on}'] = [utils.geometry_to_json(x) for x in self.{sn}]")
                else:
                    lines.append(f"            d['{on}'] = utils.geometry_to_json(self.{sn})")
            else:
                lines.append(f"        if self.{sn} is not None:")
                lines.append(f"            d['{on}'] = self.{sn}")
        lines.append("        return d")
        lines.append("")
        lines.append("    def __setstate__(self, state):")
        for p in props:
            on = p['name']
            sn = snake(on)
            is_coll, inner = _split_collection(p['type'])
            if _is_edm_datetimeoffset(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, datetime):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(isoparse(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, datetime):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = isoparse(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_date(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, date):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(date.fromisoformat(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 date string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, date):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = date.fromisoformat(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 date string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_time(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, time):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(time.fromisoformat(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 time string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, time):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = time.fromisoformat(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 time string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_duration(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, timedelta):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(utils.parse_duration_to_timedelta(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 duration string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, timedelta):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = utils.parse_duration_to_timedelta(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 duration string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_geospatial(inner, model):
                expected = _geo_expected_kind(_resolve_underlying(inner, model))
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(utils.parse_geometry(_v{if_expected}))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('invalid geometry for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if _tmp is not None:")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = utils.parse_geometry(_tmp{if_expected})")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid geometry for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            else:
                lines.append(f"        self.{sn} = state.get('{on}', None)")
        lines.append("")
        lines.append("    def __eq__(self, other):")
        lines.append("        if other is None or not isinstance(other, type(self)):")
        lines.append("            return False")
        if props:
            cmp_expr = " and ".join([f"self.{snake(p['name'])} == other.{snake(p['name'])}" for p in props])
            lines.append(f"        return {cmp_expr}")
        else:
            lines.append("        return True")
        lines.append("")

    # Entity Types
    for fqn, et in model.get("entity_types", {}).items():
        e_name = et["name"]
        exported.append(e_name)
        props = et.get("properties", [])
        navs = et.get("navigation_properties", [])

        arg_parts: List[str] = ["self"]
        for p in props:
            on = p['name']
            sn = snake(on)
            # skip 'id' which is handled by base Entity
            if sn == 'id':
                continue
            nullable = p.get('nullable', True)
            ann, _base_check, _is_coll = _to_py_hint(on, p['type'], model, nullable)
            if nullable:
                arg_parts.append(f"{snake(p['name'])}: {ann} = None")
            else:
                arg_parts.append(f"{snake(p['name'])}: {ann}")
        for np in navs:
            related = _last_segment(np['type'])
            sn = snake(np['name'])
            nullable_nav = np.get('nullable', True)
            if np.get("collection", False):
                ann = f"Optional[Union[EntityList[{related}], List[{related}]]]" if nullable_nav else f"Union[EntityList[{related}], List[{related}]]"
            else:
                ann = f"Optional[{related}]" if nullable_nav else f"{related}"
            arg_parts.append(f"{sn}: {ann} = None")
        arg_parts.append("**kwargs")
        arg_sig = ",\n\t\t\t\t ".join(arg_parts)

        lines.append(f"class {e_name}(Entity):")
        lines.append(f"    def __init__({arg_sig}):")
        lines.append("        super().__init__(**kwargs)")
        for p in props:
            sn = snake(p['name'])
            # skip 'id' which is handled by base Entity
            if sn == 'id':
                continue
            lines.append(f"        self.{sn} = {sn}")
        for np in navs:
            sn = snake(np['name'])
            lines.append(f"        self.{sn} = {sn}")
        lines.append("")

        # Properties with getters/setters and type checks
        for p in props:
            on = p['name']
            sn = snake(on)
            # skip 'id' which is handled by base Entity
            if sn == 'id':
                continue
            nullable = p.get('nullable', True)
            _ann, base_check, is_coll = _to_py_hint(on, p['type'], model, nullable)
            lines.append("    @property")
            lines.append(f"    def {sn}(self):")
            lines.append(f"        return getattr(self, '_{sn}', None)")
            lines.append("")
            lines.append(f"    @{sn}.setter")
            lines.append(f"    def {sn}(self, value):")
            is_coll_raw, inner_raw = _split_collection(p['type'])
            if _is_edm_datetimeoffset(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of datetime or ISO-8601 string')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, datetime):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(isoparse(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of datetime or ISO-8601 string')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, datetime):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = isoparse(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 string or datetime')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type datetime or ISO-8601 string!')")
            elif _is_edm_date(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of date or ISO-8601 date string (YYYY-MM-DD)')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, date):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(date.fromisoformat(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 date string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of date or ISO-8601 date string (YYYY-MM-DD)')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, date):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = date.fromisoformat(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 date string (YYYY-MM-DD) or date')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type date or ISO-8601 date string (YYYY-MM-DD)!')")
            elif _is_edm_time(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of time or ISO-8601 time string')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, time):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(time.fromisoformat(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 time string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of time or ISO-8601 time string')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, time):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = time.fromisoformat(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 time string or time')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type time or ISO-8601 time string!')")
            elif _is_edm_duration(inner_raw, model):
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of timedelta or ISO-8601 duration string')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    lines.append(f"            if isinstance(_x, timedelta):")
                    lines.append(f"                tmp_{sn}.append(_x)")
                    lines.append(f"            elif isinstance(_x, str):")
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(utils.parse_duration_to_timedelta(_x))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('{sn} contains an invalid ISO-8601 duration string')")
                    lines.append(f"            else:")
                    lines.append(f"                raise ValueError('{sn} should be a list of timedelta or ISO-8601 duration string')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if isinstance(value, timedelta):")
                    lines.append(f"            self._{sn} = value")
                    lines.append(f"        elif isinstance(value, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self._{sn} = utils.parse_duration_to_timedelta(value)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} should be an ISO-8601 duration string or timedelta')")
                    lines.append(f"        else:")
                    lines.append(f"            raise ValueError('{sn} should be of type timedelta or ISO-8601 duration string!')")
            elif _is_edm_geospatial(inner_raw, model):
                expected = _geo_expected_kind(_resolve_underlying(inner_raw, model))
                if is_coll:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        if not isinstance(value, list):")
                    lines.append(f"            raise ValueError('{sn} should be a list of GeoJSON geometry dicts or JSON strings')")
                    lines.append(f"        tmp_{sn} = []")
                    lines.append(f"        for _x in value:")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"            try:")
                    lines.append(f"                tmp_{sn}.append(utils.parse_geometry(_x{if_expected}))")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('{sn} contains an invalid geometry')")
                    lines.append(f"        self._{sn} = tmp_{sn}")
                else:
                    lines.append(f"        if value is None:")
                    if nullable:
                        lines.append(f"            self._{sn} = None")
                        lines.append(f"            return")
                    else:
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"        try:")
                    lines.append(f"            self._{sn} = utils.parse_geometry(value{if_expected})")
                    lines.append(f"        except ValueError:")
                    lines.append(f"            raise ValueError('{sn} should be a valid GeoJSON geometry')")
            elif base_check != "Any":
                if is_coll:
                    if nullable:
                        lines.append(f"        if value is not None and (not isinstance(value, list) or not all(isinstance(x, {base_check}) for x in value)):")
                        lines.append(f"            raise ValueError('{sn} should be a list of {base_check}')")
                        lines.append(f"        self._{sn} = value")
                    else:
                        lines.append(f"        if value is None:")
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                        lines.append(f"        if not isinstance(value, list) or not all(isinstance(x, {base_check}) for x in value):")
                        lines.append(f"            raise ValueError('{sn} should be a list of {base_check}')")
                        lines.append(f"        self._{sn} = value")
                else:
                    if nullable:
                        lines.append(f"        if value is not None and not isinstance(value, {base_check}):")
                        lines.append(f"            raise ValueError('{sn} should be of type {base_check}!')")
                        lines.append(f"        self._{sn} = value")
                    else:
                        lines.append(f"        if value is None:")
                        lines.append(f"            raise ValueError('{sn} may not be None')")
                        lines.append(f"        if not isinstance(value, {base_check}):")
                        lines.append(f"            raise ValueError('{sn} should be of type {base_check}!')")
                        lines.append(f"        self._{sn} = value")
            else:
                if nullable:
                    lines.append(f"        self._{sn} = value")
                else:
                    lines.append(f"        if value is None:")
                    lines.append(f"            raise ValueError('{sn} may not be None')")
                    lines.append(f"        self._{sn} = value")
            lines.append("")

        # Navigation properties with getters/setters and type checks
        for np in navs:
            on = np['name']
            sn = snake(on)
            related = _last_segment(np['type'])
            lines.append("    @property")
            lines.append(f"    def {sn}(self):")
            lines.append(f"        return getattr(self, '_{sn}', None)")
            lines.append("")
            lines.append(f"    @{sn}.setter")
            lines.append(f"    def {sn}(self, value):")
            if np.get('nullable', True):
                lines.append("        if value is None:")
                lines.append(f"            self._{sn} = None")
                lines.append("            return")
            else:
                lines.append("        if value is None:")
                lines.append(f"            raise ValueError('{sn} may not be None')")
            if np.get("collection", False):
                lines.append(f"        if isinstance(value, EntityList):")
                lines.append(f"            if not all(isinstance(x, {related}) for x in value.entities):")
                lines.append(f"                raise ValueError('{sn} should be an EntityList of {related}')")
                lines.append(f"            self._{sn} = value")
                lines.append(f"        elif isinstance(value, list):")
                lines.append(f"            if not all(isinstance(x, {related}) for x in value):")
                lines.append(f"                raise ValueError('{sn} should be a List of {related}')")
                lines.append(f"            self._{sn} = EntityList(__name__ + '.{related}', value)")
                lines.append(f"        else:")
                lines.append(f"            raise ValueError('{sn} should be of type EntityList[{related}] or List[{related}]!')")
            else:
                lines.append(f"        if not isinstance(value, {related}):")
                lines.append(f"            raise ValueError('{sn} should be of type {related}!')")
                lines.append(f"        self._{sn} = value")
            lines.append("")

        # Service propagation
        lines.append("    def ensure_service_on_children(self, service):")
        if not navs:
            lines.append("        pass")
        else:
            for np in navs:
                sn = snake(np['name'])
                lines.append(f"        if self.{sn} is not None:")
                lines.append(f"            self.{sn}.set_service(service)")
        lines.append("")

        # Equality
        lines.append("    def __eq__(self, other):")
        lines.append("        if not super().__eq__(other):")
        lines.append("            return False")
        if props:
            for p in props:
                sn = snake(p['name'])
                # skip 'id' which is handled by base Entity
                if sn == 'id':
                    continue
                lines.append(f"        if self.{sn} != other.{sn}:")
                lines.append("            return False")
            lines.append("        return True")
        else:
            lines.append("        return True")
        lines.append("")

        # __getstate__
        lines.append("    def __getstate__(self):")
        lines.append("        data = super().__getstate__()")
        for p in props:
            on = p['name']
            sn = snake(on)
            # skip 'id' which is handled by base Entity
            if sn == 'id':
                continue
            is_coll, inner = _split_collection(p['type'])
            if _is_real_complex(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            data['{on}'] = [x.__getstate__() for x in self.{sn}]")
                else:
                    lines.append(f"            data['{on}'] = self.{sn}.__getstate__()")
            elif _is_edm_datetimeoffset(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            data['{on}'] = [utils.parse_datetime(x) for x in self.{sn}]")
                else:
                    lines.append(f"            data['{on}'] = utils.parse_datetime(self.{sn})")
            elif _is_edm_date(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            data['{on}'] = [utils.parse_date(x) for x in self.{sn}]")
                else:
                    lines.append(f"            data['{on}'] = utils.parse_date(self.{sn})")
            elif _is_edm_time(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            data['{on}'] = [utils.parse_time(x) for x in self.{sn}]")
                else:
                    lines.append(f"            data['{on}'] = utils.parse_time(self.{sn})")
            elif _is_edm_duration(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            data['{on}'] = [utils.parse_duration(x) for x in self.{sn}]")
                else:
                    lines.append(f"            data['{on}'] = utils.parse_duration(self.{sn})")
            elif _is_edm_geospatial(inner, model):
                lines.append(f"        if self.{sn} is not None:")
                if is_coll:
                    lines.append(f"            data['{on}'] = [utils.geometry_to_json(x) for x in self.{sn}]")
                else:
                    lines.append(f"            data['{on}'] = utils.geometry_to_json(self.{sn})")
            else:
                lines.append(f"        if self.{sn} is not None:")
                lines.append(f"            data['{on}'] = self.{sn}")
        for np in navs:
            on = np['name']
            sn = snake(on)
            if np.get("collection", False):
                lines.append(f"        if self.{sn} is not None and len(self.{sn}.entities) > 0:")
                lines.append(f"            data['{on}'] = self.{sn}.__getstate__()")
            else:
                lines.append(f"        if self.{sn} is not None:")
                lines.append(f"            data['{on}'] = self.{sn}.__getstate__()")
        lines.append("        return data")
        lines.append("")

        # __setstate__
        lines.append("    def __setstate__(self, state):")
        lines.append("        super().__setstate__(state)")
        for p in props:
            on = p['name']
            sn = snake(on)
            # skip 'id' which is handled by base Entity
            if sn == 'id':
                continue
            is_coll, inner = _split_collection(p['type'])
            if _is_real_complex(inner, model):
                related = _last_segment(inner)
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, dict):")
                    lines.append(f"                    _obj = {related}()")
                    lines.append(f"                    _obj.__setstate__(_v)")
                    lines.append(f"                    tmp_{sn}.append(_obj)")
                    lines.append(f"                else:")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
                else:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], dict):")
                    lines.append(f"            _obj = {related}()")
                    lines.append(f"            _obj.__setstate__(state['{on}'])")
                    lines.append(f"            self.{sn} = _obj")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = state.get('{on}', None)")
            elif _is_edm_datetimeoffset(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, datetime):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(isoparse(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, datetime):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = isoparse(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_date(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, date):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(date.fromisoformat(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 date string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, date):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = date.fromisoformat(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 date string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_time(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, time):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(time.fromisoformat(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 time string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, time):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = time.fromisoformat(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 time string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_duration(inner, model):
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    lines.append(f"                if isinstance(_v, timedelta):")
                    lines.append(f"                    tmp_{sn}.append(_v)")
                    lines.append(f"                elif isinstance(_v, str):")
                    lines.append(f"                    try:")
                    lines.append(f"                        tmp_{sn}.append(utils.parse_duration_to_timedelta(_v))")
                    lines.append(f"                    except ValueError:")
                    lines.append(f"                        raise ValueError('invalid ISO-8601 duration string for {sn}')")
                    lines.append(f"                else:")
                    lines.append(f"                    raise ValueError('invalid value for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if isinstance(_tmp, timedelta):")
                    lines.append(f"            self.{sn} = _tmp")
                    lines.append(f"        elif isinstance(_tmp, str):")
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = utils.parse_duration_to_timedelta(_tmp)")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid ISO-8601 duration string for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            elif _is_edm_geospatial(inner, model):
                expected = _geo_expected_kind(_resolve_underlying(inner, model))
                if is_coll:
                    lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                    lines.append(f"            tmp_{sn} = []")
                    lines.append(f"            for _v in state['{on}']:")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"                try:")
                    lines.append(f"                    tmp_{sn}.append(utils.parse_geometry(_v{if_expected}))")
                    lines.append(f"                except ValueError:")
                    lines.append(f"                    raise ValueError('invalid geometry for {sn}')")
                    lines.append(f"            self.{sn} = tmp_{sn}")
                else:
                    lines.append(f"        _tmp = state.get('{on}', None)")
                    lines.append(f"        if _tmp is not None:")
                    if_expected = " , expected_kind='" + expected + "'" if expected else ""
                    lines.append(f"            try:")
                    lines.append(f"                self.{sn} = utils.parse_geometry(_tmp{if_expected})")
                    lines.append(f"            except ValueError:")
                    lines.append(f"                raise ValueError('invalid geometry for {sn}')")
                    lines.append(f"        else:")
                    lines.append(f"            self.{sn} = _tmp")
            else:
                lines.append(f"        self.{sn} = state.get('{on}', None)")
        for np in navs:
            on = np['name']
            sn = snake(on)
            related = _last_segment(np['type'])
            if np.get("collection", False):
                lines.append(f"        if state.get('{on}', None) is not None and isinstance(state['{on}'], list):")
                lines.append(f"            self.{sn} = utils.transform_json_to_entity_list(state['{on}'], __name__ + '.{related}')")
                lines.append(f"            self.{sn}.next_link = state.get('{on}@iot.nextLink', None)")
                lines.append(f"            self.{sn}.count = state.get('{on}@iot.count', None)")
            else:
                lines.append(f"        if state.get('{on}', None) is not None:")
                lines.append(f"            self.{sn} = {related}()")
                lines.append(f"            self.{sn}.__setstate__(state['{on}'])")
        lines.append("")

    # EntitySets mapping
    lines.append("# Map EntitySet name -> class")
    lines.append("ENTITY_SETS = {")
    for es, fqn in model.get("entity_sets", {}).items():
        lines.append(f"    '{es}': {_last_segment(fqn)},")
    lines.append("}")
    lines.append("")

    # __all__
    exported.extend(list(model.get("entity_sets", {}).keys()))
    lines.append("__all__ = [")
    for name in sorted(set(exported)):
        lines.append(f"    '{name}',")
    lines.append("]")
    lines.append("")

    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{module_name}.py")
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return out_path


def generate_from_url(base_url: str, out_dir: str, module_name: str = "datamodel", auth: Any = None) -> str:
    """Detect an OData endpoint and generate models accordingly.

    Fallback: If no OData endpoint is available, use project's metadata.xml.
    """
    from .runtime import find_odata_endpoint, fetch_metadata
    info = find_odata_endpoint(base_url, auth=auth)
    if info is None:
        meta_path_candidates = [
            os.path.join(os.getcwd(), "frost_sta_client/metadata.xml"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frost_sta_client/metadata.xml"),
        ]
        xml_text = None
        source = None
        for p in meta_path_candidates:
            try:
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as fh:
                        xml_text = fh.read()
                        source = p
                        break
            except Exception:
                pass
        if not xml_text:
            raise RuntimeError("No OData endpoint detected and metadata.xml not found. No code generated.")
        return generate_from_metadata(xml_text, out_dir, module_name, source_url=source or "", odata_version="4.01")
    xml = fetch_metadata(info["metadata_url"], auth=auth)
    return generate_from_metadata(xml, out_dir, module_name, source_url=info["metadata_url"], odata_version=info["version"])
