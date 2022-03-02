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

from frost_sta_client.dao.observedproperty import ObservedPropertyDao

from . import entity
from . import datastream
from . import multi_datastream

from frost_sta_client import utils
from .ext import entity_type
from .ext import entity_list


class ObservedProperty(entity.Entity):

    def __init__(self,
                 name='',
                 definition='',
                 description='',
                 datastreams=None,
                 properties=None,
                 multi_datastreams=None,
                 **kwargs):
        super().__init__(**kwargs)
        if properties is None:
            properties = {}
        self.properties = properties
        self.name = name
        self.definition = definition
        self.description = description
        self.datastreams = datastreams
        self.multi_datastreams = multi_datastreams

    def __new__(cls, *args, **kwargs):
        new_observed_property = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_definition': '', '_description': '',
                      '_datastreams': None, '_multi_datastreams': None, '_self_link': None, '_service': None}
        for key, value in attributes.items():
            new_observed_property.__dict__[key] = value
        return new_observed_property

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
    def definition(self):
        return self._definition

    @definition.setter
    def definition(self, value):
        if value is None:
            self._definition = None
            return
        if not isinstance(value, str):
            raise ValueError('description should be of type str!')
        self._definition = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if value is None:
            self._properties = {}
            return
        if not isinstance(value, dict):
            raise ValueError('properties should be of type dict!')
        self._properties = value

    @property
    def datastreams(self):
        return self._datastreams

    @datastreams.setter
    def datastreams(self, value):
        if value is None:
            self._datastreams = None
            return
        if isinstance(value, list) and all(isinstance(ds, datastream.Datastream) for ds in value):
            entity_class = entity_type.EntityTypes['Datastream']['class']
            self._datastreams = entity_list.EntityList(entity_class=entity_class, entities=value)
            return
        if not isinstance(value, entity_list.EntityList) \
                or any((not isinstance(ds, datastream.Datastream)) for ds in value.entities):
            raise ValueError('datastreams should be of list of type Datastream!')
        self._datastreams = value

    @property
    def multi_datastreams(self):
        return self._multi_datastreams

    @multi_datastreams.setter
    def multi_datastreams(self, values):
        if values is None:
            self._multi_datastreams = None
            return
        if isinstance(values, list) and all(isinstance(mds, multi_datastream.MultiDatastream) for mds in values):
            entity_class = entity_type.EntityTypes['MultiDatastream']['class']
            self._multi_datastreams = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if not isinstance(values, entity_list.EntityList) or\
                any((not isinstance(mds, multi_datastream.MultiDatastream)) for mds in values.entities):
            raise ValueError('multi_datastreams should be a list of multi_datastreams!')
        self._multi_datastreams = values

    def ensure_service_on_children(self, service):
        if self.datastreams is not None:
            self.datastreams.set_service(service)
        if self.multi_datastreams is not None:
            self.multi_datastreams.set_service(service)

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
        if self.definition != other.definition:
            return False
        if self.properties != other.properties:
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
        if self.definition is not None and self.definition != '':
            data['definition'] = self.definition
        if self.properties is not None and self.properties != {}:
            data['properties'] = self.properties
        if self.datastreams is not None and len(self.datastreams.entities) > 0:
            data['Datastream'] = self.datastreams.__getstate__()
        if self.multi_datastreams is not None and len(self.multi_datastreams.entities) > 0:
            data['MultiDatastreams'] = self.multi_datastreams.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get("name", None)
        self.description = state.get("description", None)
        self.definition = state.get("definition", None)
        self.properties = state.get("properties", None)
        if state.get("Datastreams", None) is not None and isinstance(state["Datastreams"], list):
            entity_class = entity_type.EntityTypes['Datastream']['class']
            self.datastreams = utils.transform_json_to_entity_list(state['Datastreams'], entity_class)
            self.datastreams.next_link = state.get('Datastreams@iot.nextLink', None)
        if state.get("MultiDatastreams", None) is not None and isinstance(state["MultiDatastreams"], list):
            entity_class = entity_type.EntityTypes['MultiDatastream']['class']
            self.multi_datastreams = utils.transform_json_to_entity_list(state['MultiDatatstreams'], entity_class)
            self.multi_datastreams.next_link = state.get('MultiDatastreams@iot.nextLink', None)

    def get_dao(self, service):
        return ObservedPropertyDao(service)
