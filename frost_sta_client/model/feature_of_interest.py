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

from . import entity

import frost_sta_client.dao.features_of_interest

from .ext import entity_list, entity_type

import json

from .. import utils


class FeatureOfInterest(entity.Entity):
    def __init__(self,
                 name='',
                 description='',
                 encoding_type='',
                 feature=None,
                 properties=None,
                 observations=None,
                 **kwargs):
        super().__init__(**kwargs)
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.encoding_type = encoding_type
        self.feature = feature
        self.properties = properties
        self.observations = observations

    def __new__(cls, *args, **kwargs):
        new_foi = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_encoding_type': '',
                      '_feature': '', '_observations': None, '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_foi.__dict__[key] = value
        return new_foi

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value is None:
            self._name = None
            return
        if not isinstance(value, str):
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
        if not isinstance(value, str):
            raise ValueError('description should be of type str!')
        self._description = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if value is None:
            self._properties = None
            return
        if not isinstance(value, dict):
            raise ValueError('properties should be of type dict!')
        self._properties = value

    @property
    def encoding_type(self):
        return self._encoding_type

    @encoding_type.setter
    def encoding_type(self, value):
        if value is None:
            self._encoding_type = None
            return
        if not isinstance(value, str):
            raise ValueError('encodingType should be of type str!')
        self._encoding_type = value

    @property
    def observations(self):
        return self._observations

    @observations.setter
    def observations(self, values):
        if values is None:
            self._observations = None
            return
        if isinstance(values, list) and \
                all(isinstance(ob, frost_sta_client.model.observation.Observation) for ob in values):
            entity_class = entity_type.EntityTypes['Observation']['class']
            self._observations = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if isinstance(values, entity_list.EntityList) and \
                all((isinstance(ob, frost_sta_client.model.observation.Observation)) for ob in values.entities):
            self._observations = values
            return
        raise ValueError('Observations should be a list of Observations')

    @property
    def feature(self):
        return self._feature

    @feature.setter
    def feature(self, value):
        if value is None:
            self._feature = None
            return
        try:
            json.dumps(value)
        except TypeError:
            raise TypeError('feature should be json serializable')
        self._feature = value

    def ensure_service_on_children(self, service):
        if self.observations is not None:
            self.observations.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.name != other.name:
            return False
        if self.properties != other.properties:
            return False
        if self.description != other.description:
            return False
        if self.encoding_type != other.encoding_type:
            return False
        if self.feature != other.feature:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        if data.get('@iot.id', None) is not None:
            return data
        if self.name is not None and self.name != '':
            data['name'] = self.name
        if self.description is not None and self.description != '':
            data['description'] = self.description
        if self.properties is not None and self.properties != {}:
            data['properties'] = self.properties
        if self.encoding_type is not None and self.encoding_type != '':
            data['encodingType'] = self.encoding_type
        if self.feature is not None:
            data['feature'] = self.feature
        if self.observations is not None and len(self.observations.entities) > 0:
            data['Observations'] = self.observations.__gestate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get("name", None)
        self.description = state.get("description", None)
        self.properties = state.get("properties", None)
        self.encoding_type = state.get("encodingType", None)
        if state.get("Observations", None) is not None and isinstance(state["Observations"], list):
            entity_class = entity_type.EntityTypes['Observation']['class']
            self.observations = utils.transform_json_to_entity_list(state['Observations'], entity_class)
            self.observations.next_link = state.get("Observations@iot.nextLink", None)

    def get_dao(self, service):
        return frost_sta_client.dao.features_of_interest.FeaturesOfInterestDao(service)
