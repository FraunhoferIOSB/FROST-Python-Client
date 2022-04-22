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
import frost_sta_client.model.ext.entity_list


def extract_value(location):
    return location[location.find('(')+1: location.find(')')]


def transform_entity_to_json_dict(entity):
    json_str = jsonpickle.encode(entity, unpicklable=False)
    return jsonpickle.decode(json_str)


def transform_json_to_entity(json_response, entity_class):
    decodable_str = '{\'py/object\': \'' + entity_class + '\', \'py/state\': ' \
                    + jsonpickle.encode(json_response, unpicklable=False) + '}'
    return jsonpickle.decode(decodable_str)


def transform_json_to_entity_list(json_response, entity_class):
    entity_list = frost_sta_client.model.ext.entity_list.EntityList(entity_class)
    result_list = []
    if isinstance(json_response, dict):
        try:
            response_list = json_response['value']
            entity_list.next_link = json_response.get("@iot.nextLink", None)
        except AttributeError as e:
            raise e
    elif isinstance(json_response, list):
        response_list = json_response
    else:
        raise ValueError("expected json as a dict or list to transform into entity list")
    for item in response_list:
        result_list.append(transform_json_to_entity(item, entity_list.entity_class))
    entity_list.entities = result_list
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
    raise ValueError("can only handle geojson of type Point, Polygon or Geometry")
