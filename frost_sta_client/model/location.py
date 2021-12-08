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

import frost_sta_client.model
from frost_sta_client.dao.location import LocationDao

from . import entity
from . import thing
from . import historical_location

import inspect
import json
import geojson

from frost_sta_client import utils
from .ext import entity_type
from .ext import entity_list


class Location(entity.Entity):

    def __init__(self,
                 name='',
                 description='',
                 encoding_type='',
                 properties=None,
                 location=None,
                 thing=None,
                 historical_locations=None):
        super().__init__()
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.encoding_type = encoding_type
        self.properties = properties
        self.location = location
        self.thing = thing
        self.historical_locations = historical_locations

    def __new__(cls, *args, **kwargs):
        new_loc = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_encodingType': '',
                      '_location': None, '_thing': None, '_historical_locations': None, '_self_link': '',
                      '_service': None}
        for key, value in attributes.items():
            new_loc.__dict__[key] = value
        return new_loc

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value is None:
            self._name = None
            return
        if type(value) != str:
            raise ValueError('name should be of type str!')
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value is None:
            self._description = None
            return
        if type(value) != str:
            raise ValueError('description should be of type str!')
        self._description = value

    @property
    def encoding_type(self):
        return self._encoding_type

    @encoding_type.setter
    def encoding_type(self, value):
        if value is None:
            self._encoding_type = None
            return
        if type(value) != str:
            raise ValueError('encodingType should be of type str!')
        self._encoding_type = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, values):
        if values is None:
            self._properties = None
            return
        if type(values) != dict:
            raise ValueError('properties should be of type dict!')
        self._properties = values

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if value is None:
            self._location = None
            return
        geo_classes = [obj for _, obj in inspect.getmembers(geojson) if inspect.isclass(obj) and
                       obj.__module__ == 'geojson.geometry']
        if type(value) in geo_classes:
            self._location = value
            return
        else:
            try:
                json.dumps(value)
            except TypeError:
                raise ValueError('location should be of json_serializable!')
            self._location = value

    @property
    def thing(self):
        return self._thing

    @thing.setter
    def thing(self, value):
        if value is None:
            self._thing = None
            return
        if type(value) != thing.Thing:
            raise ValueError('thing should be of type Thing!')
        self._thing = value

    @property
    def historical_locations(self):
        return self._historical_locations

    @historical_locations.setter
    def historical_locations(self, values):
        if values is None:
            self._historical_locations = None
            return
        if type(values) == list and all(isinstance(hl, historical_location.HistoricalLocation) for hl in values):
            entity_class = entity_type.EntityTypes['HistoricalLocation']['class']
            self._historical_locations = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if type(values) == entity_list.EntityList and \
                all(isinstance(hl, historical_location.HistoricalLocation) for hl in values.entities):
            self._historical_locations = values
        raise ValueError('historical_location should be of type HistoricalLocation!')

    def ensure_service_on_children(self, service):
        if self.thing is not None:
            self.thing.set_service(service)
        if self.historical_locations is not None:
            self.historical_locations.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.name != other.name:
            return False
        if self.description != other.description:
            return False
        if self.encoding_type != other.encoding_type:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        if self.name is not None and self.name != '':
            data['name'] = self.name
        if self.description is not None and self.description != '':
            data['description'] = self.description
        if self.encoding_type is not None and self.encoding_type != '':
            data['encodingType'] = self.encoding_type
        if self.properties is not None and self.properties != {}:
            data['properties'] = self.properties
        if self.location is not None:
            data['location'] = self.location
        if self.thing is not None:
            data['Thing'] = self.thing
        if self.historical_locations is not None and len(self.historical_locations.entities) > 0:
            data['HistoricalLocation'] = self.historical_locations.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get("name", None)
        self.description = state.get("description", None)
        self.encoding_type = state.get("encodingType", None)
        self.properties = state.get("properties", None)
        if state.get("Thing", None) is not None:
            self.thing = frost_sta_client.model.thing.Thing()
            self.thing.__setstate__(state["Thing"])
        if state.get("location", None) is not None:
            self.location = state["location"]
        if state.get("HistoricalLocations", None) is not None:
            entity_class = entity_type.EntityTypes['HistoricalLocation']['class']
            self.historical_locations = utils.transform_json_to_entity_list(state['HistoricalLocations'], entity_class)
            self.historical_locations.next_link = state.get('HistoricalLocations@iot.nextLink', None)

    def get_dao(self, service):
        return LocationDao(service)
