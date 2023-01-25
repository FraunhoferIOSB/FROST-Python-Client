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

EntityTypes = {
    'Datastream': {
        'singular': 'Datastream',
        'plural': 'Datastreams',
        'class': 'frost_sta_client.model.datastream.Datastream',
        'relations_list': ['Sensor', 'Thing', 'ObservedProperty', 'Observations']
    },
    'MultiDatastream': {
        'singular': 'MultiDatastream',
        'plural': 'MultiDatastreams',
        'class': 'frost_sta_client.model.multi_datastream.MultiDatastream',
        'relations_list': ['Sensor', 'Thing', 'ObservedProperties', 'Observations']
    },
    'FeatureOfInterest': {
        'singular': 'FeatureOfInterest',
        'plural': 'FeaturesOfInterest',
        'class': 'frost_sta_client.model.feature_of_interest.FeatureOfInterest',
        'relations_list': ['Observations']
    },
    'HistoricalLocation': {
        'singular': 'HistoricalLocation',
        'plural': 'HistoricalLocations',
        'class': 'frost_sta_client.model.historical_location.HistoricalLocation',
        'relations_list': ['Thing', 'Locations']
    },
    'Actuator': {
        'singular': 'Actuator',
        'plural': 'Actuators',
        'class': 'frost_sta_client.model.actuator.Actuator',
        'relations_list': ['TaskingCapabilities']
    },
    'Location': {
        'singular': 'Location',
        'plural': 'Locations',
        'class': 'frost_sta_client.model.location.Location',
        'relations_list': ['Things', 'HistoricalLocations']
    },
    'Observation': {
        'singular': 'Observation',
        'plural': 'Observations',
        'class': 'frost_sta_client.model.observation.Observation',
        'relations_list': ['FeatureOfInterest', 'Datastream', 'MultiDatastream']
    },
    'Thing': {
        'singular': 'Thing',
        'plural': 'Things',
        'class': 'frost_sta_client.model.thing.Thing',
        'relations_list': ['Datastreams', 'MultiDatastreams', 'Locations', 'HistoricalLocations', 'TaskingCapabilities']
    },
    'ObservedProperty': {
        'singular': 'ObservedProperty',
        'plural': 'ObservedProperties',
        'class': 'frost_sta_client.model.observedproperty.ObservedProperty',
        'relations_list': ['Datastreams', 'MultiDatastreams']
    },
    'Sensor': {
        'singular': 'Sensor',
        'plural': 'Sensors',
        'class': 'frost_sta_client.model.sensor.Sensor',
        'relations_list': ['Datastreams', 'MultiDatastreams']
    },
    'Task': {
        'singular': 'Task',
        'plural': 'Tasks',
        'class': 'frost_sta_client.model.task.Task',
        'relations_list': ['TaskingCapability']
    },
    'TaskingCapability': {
        'singular': 'TaskingCapability',
        'plural': 'TaskingCapabilities',
        'class': 'frost_sta_client.model.tasking_capability.TaskingCapability',
        'relations_list': ['Tasks', 'Actuator', 'Thing']
    },
    'UnitOfMeasurement': {
        'singular': 'UnitOfMeasurement',
        'plural': 'UnitOfMeasurements',
        'class': 'frost_sta_client.model.ext.unitofmeasurement.UnitOfMeasurement'
    },
    'EntityList': {
        'singular': 'EntityList',
        'plural': 'EntityLists',
        'class': 'frost_sta_client.model.ext.entity_list.EntityList'
    }
}

list_for_class = {}
for key, entity_type in EntityTypes.items():
    list_for_class[entity_type["class"]] = entity_type["plural"]

def get_list_for_class(clazz):
    clazz_name = clazz.__module__ + "." + clazz.__name__
    return list_for_class[clazz_name]
