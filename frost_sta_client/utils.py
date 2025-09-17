# Copyright (C) 2021 Fraunhofer Institut IOSB, Fraunhoferstr. 1, D 76131
# Karlsruhe, Germany.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import jsonpickle
import datetime
from dateutil.parser import isoparse
import geojson
import logging
import sys
import re
from typing import Any, Dict, List
import frost_sta_client.model.ext.entity_list


def extract_value(location):
    try:
        value = int(location[location.find('(')+1: location.find(')')])
    except ValueError:
        value = str(location[location.find('(')+2: location.find(')')-1])
    return value

def transform_entity_to_json_dict(entity):
    try:
        data = entity.__getstate__()
    except AttributeError:
        data = entity.__dict__
    return data

def class_from_string(string):
    module_name, class_name = string.rsplit(".", 1)
    return getattr(sys.modules[module_name], class_name)

def _flatten_time_value(val):
    if isinstance(val, dict):
        start = val.get('start') or val.get('Start')
        end = val.get('end') or val.get('End')
        if start and end:
            return f"{start}/{end}"
        if start:
            return start
    return val

def normalize_sta_odata_json(obj: Any) -> Any:
    """Normalize SensorThings v1.1 and OData (4.0/4.01) JSON to STA-style keys.

    - Ensure '@iot.id' and '@iot.selfLink' are present (mapping id/@id/@odata.id).
    - Map nextLink and count to '@iot.nextLink' and '@iot.count'.
    - Map '*@odata.navigationLink' and '*@navigationLink' to '*@iot.navigationLink'.
    - Map '*@odata.count' and '*@count' to '*@iot.count'.
    - Convert phenomenonTime/resultTime/validTime objects {start,end} to 'start/end' strings.
    - Recurse into nested dicts and lists.
    """
    if isinstance(obj, list):
        return [normalize_sta_odata_json(x) for x in obj]
    if not isinstance(obj, dict):
        return obj

    src: Dict[str, Any] = obj
    dst: Dict[str, Any] = {}

    # Pre-read metadata that we may fold into STA fields later
    meta_id = src.get('@iot.id')
    if meta_id is None:
        if 'id' in src and not isinstance(src.get('id'), dict):
            meta_id = src.get('id')
    meta_self_link = src.get('@iot.selfLink') or src.get('@odata.id') or src.get('@id')

    for k, v in src.items():
        # Skip fields we normalize separately
        if k in ('@odata.id', '@id', 'id'):
            continue
        if k in ('@odata.context', '@context'):
            continue

        # Top-level links and counts
        if k in ('@iot.nextLink', '@odata.nextLink', '@nextLink'):
            dst['@iot.nextLink'] = v
            continue
        if k in ('@iot.count', '@odata.count', '@count'):
            dst['@iot.count'] = v
            continue

        # Navigation link/count on collections
        if k.endswith('@odata.navigationLink'):
            base = k[:-len('@odata.navigationLink')]
            dst[f'{base}@iot.navigationLink'] = v
            continue
        if k.endswith('@navigationLink') and not k.endswith('@iot.navigationLink'):
            base = k[:-len('@navigationLink')]
            dst[f'{base}@iot.navigationLink'] = v
            continue
        if k.endswith('@odata.count'):
            base = k[:-len('@odata.count')]
            dst[f'{base}@iot.count'] = v
            continue
        if k.endswith('@count') and not k.endswith('@iot.count'):
            base = k[:-len('@count')]
            dst[f'{base}@iot.count'] = v
            continue

        # Recurse on nested structures
        if k == 'value' and isinstance(v, list):
            dst['value'] = [normalize_sta_odata_json(x) for x in v]
            continue
        nv = normalize_sta_odata_json(v) if isinstance(v, (dict, list)) else v
        dst[k] = nv

    # Add normalized id/selfLink if available
    if meta_id is not None:
        dst['@iot.id'] = meta_id
    if meta_self_link is not None:
        dst['@iot.selfLink'] = meta_self_link

    # Normalize time objects for known time fields
    for tk in ('phenomenonTime', 'resultTime', 'validTime'):
        if tk in dst:
            dst[tk] = _flatten_time_value(dst[tk])

    return dst

def transform_json_to_entity(json_response, entity_class):
    cl = class_from_string(entity_class)
    obj = cl()
    normalized = normalize_sta_odata_json(json_response)
    obj.__setstate__(normalized)
    return obj

def transform_json_to_entity_list(json_response, entity_class):
    entity_list = frost_sta_client.model.ext.entity_list.EntityList(entity_class)
    if isinstance(json_response, dict):
        normalized = normalize_sta_odata_json(json_response)
        response_list = normalized.get('value', [])
        entity_list.next_link = normalized.get("@iot.nextLink", None)
        entity_list.count = normalized.get("@iot.count", None)
    elif isinstance(json_response, list):
        response_list = [normalize_sta_odata_json(item) for item in json_response]
    else:
        raise ValueError("expected json as a dict or list to transform into entity list")
    entity_list.entities = [transform_json_to_entity(item, entity_list.entity_class) for item in response_list]
    return entity_list


def check_datetime(value, time_entity):
    try:
        parse_datetime(value)
    except ValueError as e:
        logging.error(f"error during {time_entity} check")
        raise e
    return value


def parse_datetime(value) -> str:
    if value is None:
        return value
    if isinstance(value, str):
        if '/' in value:
            try:
                times = value.split('/')
                if len(times) != 2:
                    raise ValueError("If the time interval is provided as a string,"
                                     " it should be in isoformat")
                result = [isoparse(times[0]),
                          isoparse(times[1])]
            except ValueError:
                raise ValueError("If the time entity interval is provided as a string,"
                                 " it should be in isoformat")
            result = result[0].isoformat() + '/' + result[1].isoformat()
            return result
        else:
            try:
                result = isoparse(value)
            except ValueError:
                raise ValueError("If the phenomenon time is provided as string, it should be in isoformat")
            result = result.isoformat()
            return result
    if isinstance(value, datetime.datetime):
        return value.isoformat()
    if isinstance(value, list) and all(isinstance(v, datetime.datetime) for v in value):
        return value[0].isoformat() + value[1].isoformat()
    else:
        raise ValueError('time entities should consist of one or two datetimes')



def parse_date(value) -> str:
    """Return ISO-8601 date string from datetime.date or string input.

    Accepts:
    - datetime.date -> returns .isoformat()
    - ISO date string (YYYY-MM-DD) -> validated and normalized
    - None -> None
    """
    if value is None:
        return value
    if isinstance(value, str):
        try:
            d = datetime.date.fromisoformat(value)
        except ValueError:
            raise ValueError("If the date is provided as string, it should be in isoformat (YYYY-MM-DD)")
        return d.isoformat()
    if isinstance(value, datetime.date):
        return value.isoformat()
    raise ValueError("date entities should be datetime.date or ISO-8601 date string")


def parse_time(value) -> str:
    """Return ISO-8601 time string from datetime.time or string input.

    Accepts:
    - datetime.time -> returns .isoformat()
    - ISO time string (HH:MM[:SS[.ffffff]]) -> validated and normalized
    - None -> None
    """
    if value is None:
        return value
    if isinstance(value, str):
        try:
            t = datetime.time.fromisoformat(value)
        except ValueError:
            raise ValueError("If the time is provided as string, it should be in ISO-8601 time format (HH:MM[:SS[.ffffff]])")
        return t.isoformat()
    if isinstance(value, datetime.time):
        return value.isoformat()
    raise ValueError("time entities should be datetime.time or ISO-8601 time string")


def duration_to_isoformat(td: datetime.timedelta) -> str:
    """Convert a timedelta to an ISO-8601 duration string (PnDTnHnMnS)."""
    if td == datetime.timedelta(0):
        return "PT0S"
    sign = "-" if td.total_seconds() < 0 else ""
    total = abs(td.total_seconds())
    days = int(total // 86400)
    rem = total - days * 86400
    hours = int(rem // 3600)
    rem -= hours * 3600
    minutes = int(rem // 60)
    seconds_float = rem - minutes * 60
    seconds = int(seconds_float)
    microseconds = int(round((seconds_float - seconds) * 1_000_000))
    # Normalize possible rounding overflow
    if microseconds >= 1_000_000:
        seconds += 1
        microseconds -= 1_000_000
    if seconds >= 60:
        minutes += 1
        seconds -= 60
    if minutes >= 60:
        hours += 1
        minutes -= 60
    if hours >= 24:
        days += 1
        hours -= 24
    parts = []
    if days:
        parts.append(f"{days}D")
    time_parts = []
    if hours:
        time_parts.append(f"{hours}H")
    if minutes:
        time_parts.append(f"{minutes}M")
    if seconds or microseconds:
        if microseconds:
            sec_str = f"{seconds}.{microseconds:06d}".rstrip('0')
        else:
            sec_str = f"{seconds}"
        time_parts.append(f"{sec_str}S")
    if not parts and not time_parts:
        return "PT0S"
    if time_parts:
        return f"{sign}P{''.join(parts)}T{''.join(time_parts)}"
    return f"{sign}P{''.join(parts)}"


def parse_duration_to_timedelta(value: str) -> datetime.timedelta:
    """Parse an ISO-8601 duration (PnDTnHnMnS or PnW, optional sign) into a timedelta."""
    if value is None:
        return value
    if not isinstance(value, str):
        raise ValueError("duration must be provided as ISO-8601 string")
    s = value.strip()
    m = re.fullmatch(r'(?P<sign>[-+]?)P(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+(?:\.\d+)?)S)?)?', s)
    if not m:
        raise ValueError("Invalid ISO-8601 duration string")
    sign = -1 if m.group('sign') == '-' else 1
    weeks = int(m.group('weeks') or 0)
    days = int(m.group('days') or 0)
    hours = int(m.group('hours') or 0)
    minutes = int(m.group('minutes') or 0)
    sec_str = m.group('seconds')
    if sec_str:
        sec_float = float(sec_str)
    else:
        sec_float = 0.0
    total_days = weeks * 7 + days
    seconds = int(sec_float)
    microseconds = int(round((sec_float - seconds) * 1_000_000))
    td = datetime.timedelta(days=total_days, hours=hours, minutes=minutes, seconds=seconds, microseconds=microseconds)
    if sign < 0:
        return -td
    return td


def parse_duration(value) -> str:
    """Return ISO-8601 duration string from timedelta or string input.

    Accepts:
    - datetime.timedelta -> converted to ISO-8601 duration
    - ISO-8601 duration string -> validated and normalized
    - None -> None
    """
    if value is None:
        return value
    if isinstance(value, datetime.timedelta):
        return duration_to_isoformat(value)
    if isinstance(value, str):
        td = parse_duration_to_timedelta(value)
        return duration_to_isoformat(td)
    raise ValueError("duration entities should be timedelta or ISO-8601 duration string")

def process_area(value):
    if not isinstance(value, dict):
        raise ValueError("geojsons can only be handled as dictionaries!")
    if value.get("type", None) is None or value.get("coordinates", None) is None:
        raise ValueError("Both type and coordinates need to be specified in the dictionary")
    if value["type"] == "Point":
        return geojson.geometry.Point(value["coordinates"])
    if value["type"] == "Polygon":
        return geojson.geometry.Polygon(value["coordinates"])
    if value["type"] == "Geometry":
        return geojson.geometry.Geometry(value["coordinates"])
    if value["type"] == "LineString":
        return geojson.geometry.LineString(value["coordinates"])
    raise ValueError("can only handle geojson of type Point, Polygon, Geometry or LineString")

def handle_server_error(error, failed_action):
    # Try to extract a meaningful error message even if the response is not JSON
    try:
        err = error.response.json()
        if isinstance(err, dict):
            error_message = err.get('message', err.get('error', str(err)))
        else:
            error_message = str(err)
    except Exception:
        try:
            error_message = getattr(error.response, 'text', str(error))
        except Exception:
            error_message = str(error)
    logging.error("{} failed with status-code {}, {}".format(failed_action, getattr(error.response, 'status_code', 'unknown'), error_message))
    raise error
