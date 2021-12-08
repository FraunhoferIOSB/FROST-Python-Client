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
import demjson3
import datetime
import geojson
import frost_sta_client.model.ext.entity_list


def extract_value(location):
    return location[location.find('(')+1: location.find(')')]


def transform_entity_to_json_dict(entity):
    json_str = jsonpickle.encode(entity, unpicklable=False)
    return jsonpickle.decode(json_str)


def transform_json_to_entity(json_response, entity_class):
    decodable_str = '{\'py/object\': \'' + entity_class + '\', \'py/state\': ' \
                    + jsonpickle.encode(json_response, unpicklable=False) + '}'
    return jsonpickle.decode(decodable_str, backend=demjson3)


def transform_json_to_entity_list(json_response, entity_class):
    entity_list = frost_sta_client.model.ext.entity_list.EntityList(entity_class)
    result_list = []
    if type(json_response) == dict:
        try:
            response_list = json_response['value']
            entity_list.next_link = json_response.get("@iot.nextLink", None)
        except AttributeError as e:
            raise e
    else:
        response_list = json_response
    for item in response_list:
        result_list.append(transform_json_to_entity(item, entity_list.entity_class))
    entity_list.entities = result_list
    return entity_list


def process_datetime(value):
    if value is None:
        return value
    if type(value) == str:
        value = value.replace('Z', '')
        if '/' in value:
            try:
                times = value.split('/')
                if len(times) != 2:
                    raise ValueError("If the phenomenon time interval is provided as a string,"
                                     " it should be in isoformat")
                result = [datetime.datetime.fromisoformat(times[0]),
                          datetime.datetime.fromisoformat(times[1])]
            except ValueError:
                raise ValueError("If the phenomenon time interval is provided as a string,"
                                 " it should be in isoformat")
            result = result[0].isoformat() + 'Z/' + result[1].isoformat() + 'Z'
            return result
        else:
            try:
                result = datetime.datetime.fromisoformat(value)
            except ValueError:
                raise ValueError("If the phenomenon time is provided as string, it should be in isoformat")
            result = result.isoformat() + 'Z'
            return result
    if value is None:
        return None
    if type(value) == datetime.datetime:
        return value.isoformat() + 'Z'
    if type(value) == list and all(isinstance(v, datetime.datetime) for v in value):
        return value[0].isoformat() + 'Z/' + value[1].isoformat() + 'Z'
    else:
        raise ValueError('phenomenon_time should consist of one or two datetimes')


def process_area(value):
    if type(value) != dict:
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
