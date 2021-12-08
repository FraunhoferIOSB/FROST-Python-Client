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
from frost_sta_client.dao.multi_datastream import MultiDatastreamDao

from . import entity
from . import thing
from . import sensor
from . import observation
from . import observedproperty
from .ext import unitofmeasurement

from frost_sta_client import utils
from .ext import entity_list
from .ext import entity_type

import geojson.geometry


class MultiDatastream(entity.Entity):
    def __init__(self,
                 name='',
                 description='',
                 properties=None,
                 unit_of_measurements=None,
                 observation_type='',
                 multi_observation_data_types=None,
                 observed_area=None,
                 phenomenon_time=None,
                 result_time=None,
                 thing=None,
                 sensor=None,
                 observed_properties=None,
                 observations=None):
        super().__init__()
        if properties is None:
            properties = {}
        if multi_observation_data_types is None:
            multi_observation_data_types = []
        self.name = name
        self.description = description
        self.properties = properties
        self.unit_of_measurements = unit_of_measurements
        self.observation_type = observation_type
        self.multi_observation_data_types = multi_observation_data_types
        self.observed_area = observed_area
        self.phenomenon_time = phenomenon_time
        self.result_time = result_time
        self.thing = thing
        self.sensor = sensor
        self.observed_properties = observed_properties
        self.observations = observations

    def __new__(cls, *args, **kwargs):
        new_mds = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_unit_of_measurement': [],
                      '_observation_type': '', '_multi_observation_data_types': [], '_observed_area': None,
                      '_phenomenon_time': None, '_result_time': None, '_thing': None, '_sensor': None,
                      '_observed_properties': None, '_observations': None, '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_mds.__dict__[key] = value
        return new_mds

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
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, values):
        if values is None:
            self._properties = {}
            return
        if type(values) != dict:
            raise ValueError('properties should be of type dict!')
        self._properties = values

    @property
    def unit_of_measurements(self):
        return self._unit_of_measurements

    @unit_of_measurements.setter
    def unit_of_measurements(self, values):
        if values is None:
            self._unit_of_measurements = None
            return
        if type(values) == list and all(isinstance(uom, unitofmeasurement.UnitOfMeasurement) for uom in values):
            entity_class = entity_type.EntityTypes['UnitOfMeasurement']['class']
            self._unit_of_measurements = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if type(values) != entity_list.EntityList or \
                any((not isinstance(uom, unitofmeasurement.UnitOfMeasurement)) for uom in values.entities):
            raise ValueError('unit_of_measurements should be an entity_list of type UnitOfMeasurement')
        self._unit_of_measurements = values

    @property
    def observation_type(self):
        return self._observation_type

    @observation_type.setter
    def observation_type(self, value):
        if type(value) != str:
            raise ValueError('observation_type should be of type str!')
        self._observation_type = value

    @property
    def multi_observation_data_types(self):
        return self._multi_observation_data_types

    @multi_observation_data_types.setter
    def multi_observation_data_types(self, values):
        if values is not None and (type(values) != list or any((not isinstance(dtype, str)) for dtype in values)):
            raise ValueError('multi_observations_data_types should be list of type str!')
        self._multi_observation_data_types = values
    
    @property
    def observed_area(self):
        return self._observed_area

    @observed_area.setter
    def observed_area(self, value):
        if value is None:
            self._observed_area = None
            return
        if type(value) != geojson.geometry.Polygon:
            raise ValueError('observedArea should be geojson object')
        self._observed_area = value

    @property
    def phenomenon_time(self):
        return self._phenomenon_time

    @phenomenon_time.setter
    def phenomenon_time(self, value):
        self._phenomenon_time = utils.process_datetime(value)

    @property
    def result_time(self):
        return self._result_time

    @result_time.setter
    def result_time(self, value):
        self._result_time = utils.process_datetime(value)

    @property
    def thing(self):
        return self._thing

    @thing.setter
    def thing(self, value):
        if value is not None and type(value) != thing.Thing:
            raise ValueError('thing should be of type Thing!')
        self._thing = value

    @property
    def sensor(self):
        return self._sensor

    @sensor.setter
    def sensor(self, value):
        if value is not None and type(value) != sensor.Sensor:
            raise ValueError('sensor should be of type Sensor!')
        self._sensor = value

    @property
    def observed_properties(self):
        return self._observed_properties

    @observed_properties.setter
    def observed_properties(self, values):
        if values is None:
            self._observed_properties = None
            return
        if type(values) == list and all(isinstance(op, observedproperty.ObservedProperty) for op in values):
            entity_class = entity_type.EntityTypes['ObservedProperty']['class']
            self._observed_properties = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if type(values) != entity_list.EntityList or \
                any(not isinstance(op, observedproperty.ObservedProperty) for op in values.entities):
            raise ValueError('observed_properties should be an entity list of ObservedProperty!')
        self._observed_properties = values

    @property
    def observations(self):
        return self._observations

    @observations.setter
    def observations(self, values):
        if values is None:
            self._observations = None
            return
        if type(values) == list and all(isinstance(ob, observation.Observation) for ob in values):
            entity_class = entity_type.EntityTypes['Observation']['class']
            self._observations = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if type(values) != entity_list.EntityList or \
                any(not isinstance(ob, observation.Observation) for ob in values.entities):
            raise ValueError('Observations should be an entity list of Observations')
        self._observations = values

    def ensure_service_on_children(self, service):
        if self.thing is not None:
            self.thing.set_service(service)
        if self.sensor is not None:
            self.sensor.set_service(service)
        if self.observations is not None:
            self.observations.set_service(service)
        if self.observed_properties is not None:
            self.observed_properties.set_service(service)

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
        if self.observation_type != other.observation_type:
            return False
        if self.observed_area != other.observation_area:
            return False
        if self.properties != other.properties:
            return False
        if self.result_time != other.result_time:
            return False
        if self.unit_of_measurements != other.unit_of_measurements:
            return False
        if self.multi_observation_data_types != other.multi_observation_data_types:
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
        if self.observation_type is not None and self.observation_type != '':
            data['observationType'] = self.observation_type
        if self.observed_area is not None:
            data['observedArea'] = self.observed_area
        if self.phenomenon_time is not None:
            data['phenomenonTime'] = self.phenomenon_time
        if self.result_time is not None:
            data['resultTime'] = self.result_time
        if self.thing is not None:
            data['Thing'] = self.thing
        if self.sensor is not None:
            data['Sensor'] = self.sensor
        if self.properties is not None and self.properties != {}:
            data['properties'] = self.properties
        if self.unit_of_measurements is not None and len(self.unit_of_measurements.entities) > 0:
            data['unitOfMeasurements'] = self.unit_of_measurements.__getstate__()
        if len(self.multi_observation_data_types) > 0:
            data['multiObservationDataTypes'] = self.multi_observation_data_types
        if self.observed_properties is not None and len(self.observed_properties.entities) > 0:
            data['ObservedProperty'] = self.observed_properties.__getstate__()
        if self.observations is not None and len(self.observations.entities) > 0:
            data['Observation'] = self.observations.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get('name', None)
        self.description = state.get('description', None)
        self.observation_type = state.get('observationType', None)
        self.observation_area = state.get('observedArea', None)
        self.phenomenon_time = state.get('phenomenonTime', None)
        self.result_time = state.get('resultTime', None)
        self.properties = state.get('properties', None)
        if state.get('Thing', None) is not None:
            self.thing = frost_sta_client.model.thing.Thing()
            self.thing.__setstate__(state['Thing'])
        if state.get('Sensor', None) is not None:
            self.sensor = frost_sta_client.model.sensor.Sensor()
            self.sensor.__setstate__(state['Sensor'])
        if state.get('unitOfMeasurements', None) is not None and type(state['unitOfMeasurements']) == list:
            entity_class = entity_type.EntityTypes['UnitOfMeasurement']['class']
            self.unit_of_measurements = utils.transform_json_to_entity_list(state['unitOfMeasurements'], entity_class)
            self.unit_of_measurements.next_link = state.get('unitOfMeasurements', None)
        if state.get('multiObservationDataTypes', None) is not None \
                and type(state['multiObservationDataTypes']) == list:
            self.multi_observation_data_types = []
            for value in state['multiObservationDataTypes']:
                self.multi_observation_data_types.append(value)
        if state.get('ObservedProperties', None) is not None and type(state['ObservedProperties']) == list:
            entity_class = entity_type.EntityTypes['ObservedProperty']['class']
            self.observed_properties = utils.transform_json_to_entity_list(state['ObservedProperty'], entity_class)
            self.observed_properties.next_link = state.get('ObservedProperties@iot.nextLink')
        if state.get('Observations', None) is not None and type(state['Observations']) == list:
            entity_class = entity_type.EntityTypes['Observation']['class']
            self.observations = utils.transform_json_to_entity_list(state['Observations'], entity_class)
            self.observed_properties.next_link = state.get('Observations@iot.nextLink')

    def get_dao(self):
        return MultiDatastreamDao(self)
