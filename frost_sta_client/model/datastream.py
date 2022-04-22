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
import inspect
import json

import frost_sta_client.model.ext.unitofmeasurement
from frost_sta_client.dao.datastream import DatastreamDao

from . import thing
from . import sensor
from . import observedproperty
from . import observation
from . import entity
from .ext import unitofmeasurement
from .ext import entity_list
from .ext import entity_type

from frost_sta_client import utils

import geojson.geometry


class Datastream(entity.Entity):

    def __init__(self,
                 name='',
                 description='',
                 observation_type='',
                 unit_of_measurement=None,
                 observed_area=None,
                 properties=None,
                 phenomenon_time=None,
                 result_time=None,
                 thing=None,
                 sensor=None,
                 observed_property=None,
                 observations=None,
                 **kwargs):
        """
        This class handles Datastreams assigned to a Thing. Before you create a Datastreams, you firstly have to
        create a Thing, a Sensor and an observedProperty to which you have to refer by specifying its ids.

        Parameters
        ----------
        name: str
        description: str
        observation_type: str
        unit_of_measurement: dict
            Should be a dict of keys 'name', 'symbol', 'definition' with values of str.

        """
        super().__init__(**kwargs)
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.observation_type = observation_type
        self.unit_of_measurement = unit_of_measurement
        self.observed_area = observed_area
        self.properties = properties
        self.phenomenon_time = phenomenon_time
        self.result_time = result_time
        self.thing = thing
        self.sensor = sensor
        self.observed_property = observed_property
        self.observations = observations

    def __new__(cls, *args, **kwargs):
        new_datastream = super().__new__(cls)
        attributes = dict(_id=None, _name='', _description='', _properties={}, _observation_type='',
                          _unit_of_measurement=None, _observed_area=None, _phenomenon_time=None, _result_time=None,
                          _thing=None, _sensor=None, _observed_property=None, _observations=None, _self_link='',
                          _service=None)
        for key, value in attributes.items():
            new_datastream.__dict__[key] = value
        return new_datastream

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
    def observation_type(self):
        return self._observation_type

    @observation_type.setter
    def observation_type(self, value):
        if value is None:
            self._observation_type = None
            return
        if not isinstance(value, str):
            raise ValueError('observation_type should be of type str!')
        self._observation_type = value

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement

    @unit_of_measurement.setter
    def unit_of_measurement(self, value):
        if value is None or isinstance(value, unitofmeasurement.UnitOfMeasurement):
            self._unit_of_measurement = value
            return
        raise ValueError('unitOfMeasurement should be of type UnitOfMeasurement!')

    @property
    def observed_area(self):
        return self._observed_area

    @observed_area.setter
    def observed_area(self, value):
        if value is None:
            self._location = None
            return
        geo_classes = [obj for _, obj in inspect.getmembers(geojson) if inspect.isclass(obj) and
                       obj.__module__ == 'geojson.geometry']
        if type(value) in geo_classes:
            self._observed_area = value
            return
        else:
            try:
                json.dumps(value)
            except TypeError:
                raise ValueError('observedArea should be of json_serializable!')
            self._observed_area = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if value is None:
            self._properties = None
            return
        if not isinstance(value, dict):
            raise ValueError('properties should be of type dict')
        self._properties = value

    @property
    def phenomenon_time(self):
        return self._phenomenon_time

    @phenomenon_time.setter
    def phenomenon_time(self, value):
        self._phenomenon_time = utils.check_datetime(value, 'phenomenon_time')

    @property
    def result_time(self):
        return self._result_time

    @result_time.setter
    def result_time(self, value):
        self._result_time = utils.check_datetime(value, 'result_time')

    @property
    def thing(self):
        return self._thing

    @thing.setter
    def thing(self, value):
        if value is None or isinstance(value, thing.Thing):
            self._thing = value
            return
        raise ValueError('thing should be of type Thing!')

    @property
    def sensor(self):
        return self._sensor

    @sensor.setter
    def sensor(self, value):
        if value is None or isinstance(value, sensor.Sensor):
            self._sensor = value
            return
        raise ValueError('sensor should be of type Sensor!')

    @property
    def observed_property(self):
        return self._observed_property

    @observed_property.setter
    def observed_property(self, value):
        if isinstance(value, observedproperty.ObservedProperty) or value is None:
            self._observed_property = value
            return
        raise ValueError('observed property should by of type ObservedProperty!')

    @property
    def observations(self):
        return self._observations

    @observations.setter
    def observations(self, values):
        if values is None:
            self._observations = None
            return
        if isinstance(values, list) and all(isinstance(ob, observation.Observation) for ob in values):
            entity_class = entity_type.EntityTypes['Observation']['class']
            self._observations = entity_list.EntityList(entity_class=entity_class, entities=values)
            return
        if isinstance(values, entity_list.EntityList) and \
                all(isinstance(ob, observation.Observation) for ob in values.entities):
            self._observations = values
            return
        raise ValueError('Observations should be a list of Observations')

    def ensure_service_on_children(self, service):
        if self.thing is not None:
            self.thing.set_service(service)
        if self.sensor is not None:
            self.sensor.set_service(service)
        if self.observed_property is not None:
            self.observed_property.set_service(service)
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
        if self.description != other.description:
            return False
        if self.observation_type != other.observation_type:
            return False
        if self.unit_of_measurement != other.unit_of_measurement:
            return False
        if self.properties != other.properties:
            return False
        if self.result_time != other.result_time:
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
        if self.observation_type is not None and self.observation_type != '':
            data['observationType'] = self.observation_type
        if self.properties is not None and self.properties != {}:
            data['properties'] = self.properties
        if self.unit_of_measurement is not None:
            data['unitOfMeasurement'] = self.unit_of_measurement
        if self.observed_area is not None:
            data['observedArea'] = self.observed_area
        if self.phenomenon_time is not None:
            data['phenomenonTime'] = utils.parse_datetime(self.phenomenon_time)
        if self.result_time is not None:
            data['resultTime'] = utils.parse_datetime(self.result_time)
        if self.thing is not None:
            data['Thing'] = self.thing
        if self.sensor is not None:
            data['Sensor'] = self.sensor
        if self.observed_property is not None:
            data['ObservedProperty'] = self.observed_property
        if self.observations is not None and len(self.observations.entities) > 0:
            data['Observations'] = self.observations.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get("name", None)
        self.description = state.get("description", None)
        self.observation_type = state.get("observationType", None)
        self.properties = state.get("properties", None)
        if state.get("unitOfMeasurement", None) is not None:
            self.unit_of_measurement = frost_sta_client.model.ext.unitofmeasurement.UnitOfMeasurement()
            self.unit_of_measurement.__setstate__(state["unitOfMeasurement"])
        if state.get("observedArea", None) is not None:
            self.observed_area = frost_sta_client.utils.process_area(state["observedArea"])
        if state.get("phenomenonTime", None) is not None:
            self.phenomenon_time = state["phenomenonTime"]
        if state.get("resultTime", None) is not None:
            self.result_time = state["resultTime"]
        if state.get("Thing", None) is not None:
            self.thing = frost_sta_client.model.thing.Thing()
            self.thing.__setstate__(state["Thing"])
        if state.get("ObservedProperty", None) is not None:
            self.observed_property = frost_sta_client.model.observedproperty.ObservedProperty()
            self.observed_property.__setstate__(state["ObservedProperty"])
        if state.get("Sensor", None) is not None:
            self.sensor = frost_sta_client.model.sensor.Sensor()
            self.sensor.__setstate__(state["Sensor"])
        if state.get("Observations", None) is not None and isinstance(state["Observations"], list):
            entity_class = entity_type.EntityTypes['Observation']['class']
            self.observations = utils.transform_json_to_entity_list(state['Observations'], entity_class)
            self.observations.next_link = state.get("Observations@iot.nextLink", None)

    def get_dao(self, service):
        return DatastreamDao(service)
