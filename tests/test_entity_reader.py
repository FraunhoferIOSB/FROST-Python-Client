import unittest

import frost_sta_client.model.observation
import frost_sta_client.utils
import frost_sta_client.model.ext.entity_type
import datetime


class TestEntityReader(unittest.TestCase):

    def test_write_thing_basic_success(self):
        json_dict = {
            'phenomenonTime': '2016-01-07T02:00:00.000+00:00',
            'resultTime': None,
            'result': '0.15',
            'Datastream@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/'
                                             'Observations(7179373)/Datastream',
            'FeatureOfInterest@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/'
                                                    'Observations(7179373)/FeatureOfInterest',
            '@iot.id': '719373',
            '@iot.selfLink': 'https://server.de/SensorThingsService/v1.0/Observations(7179373)'
        }
        result = frost_sta_client.utils.transform_json_to_entity(json_dict, "frost_sta_client.model.observation.Observation")

        exp_observation = frost_sta_client.model.observation.Observation(
            phenomenon_time='2016-01-07T02:00:00.000+00:00',
            result='0.15',
            id='719373',
            self_link='https://server.de/SensorThingsService/v1.0/Observations(7179373)'
        )
        self.assertEqual(result, exp_observation)

    def test_read_entity_list(self):
        json_dict = {
            "@iot.nextLink": "https://server.de/SensorThingsService/v1.0/Things?$top=2&"
                             "$skip=14&$expand=Datastreams%28%24top%3D2%3B%24count%3Dtrue%29",
            "value": [
                {
                    "name": "Recoaro 1000",
                    "description": "Weather station Recoaro 1000",
                    "Datastreams@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/Things(19)/"
                                                      "Datastreams",
                    "Datastreams@iot.count": 6,
                    "Datastreams": [
                        {
                            "name": "Air Temperature Recoaro 1000",
                            "description": "The Air Temperature at Recoaro 1000",
                            "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                            "phenomenonTime": "2010-01-01T00:00:00.000Z/2019-01-13T06:00:00.000Z",
                            "unitOfMeasurement": {
                                "name": "degree celcius",
                                "symbol": "°C",
                                "definition": "ucum:Cel",
                            },
                            "Observations": [
                                {
                                    "result": 0.0
                                }
                            ],
                            "@iot.id": 66,
                            "@iot.selfLink": "https://server.de/SensorThingsService/v1.0/Datastreams(66)",
                        },
                        {
                            "name": "Precipitation Recoaro 1000",
                            "description": "The Precipitation at Recoaro 1000",
                            "observationType": "http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_Measurement",
                            "phenomenonTime": "2010-01-01T00:00:00.000Z/2019-01-13T06:00:00.000Z",
                            "unitOfMeasurement": {
                                "name": "mm/h",
                                "symbol": "mm/h",
                                "definition": "ucum:mm/h"
                            },
                            "@iot.id": 130,
                            "@iot.selfLink": "https://server.de/SensorThingsService/v1.0/Datastreams(130)"
                        }
                    ],
                    "Datastreams@iot.nextLink": "https://server.de/SensorThingsService/v1.0/Things(19)/"
                                                "Datastreams?$top=2&$skip=2&$count=true",
                    "MultiDatastreams@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/"
                                                           "Things(19)/MultiDatastreams",
                    "Locations@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/Things(19)/Locations",
                    "HistoricalLocations@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/"
                                                              "Things(19)/HistoricalLocations",
                    "@iot.id": 19,
                    "@iot.selfLink": "https://server.de/SensorThingsService/v1.0/Things(19)"
                },
                {
                    "name": "Valdagno",
                    "description": "Weather station Valdagno",
                    "Datastreams@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/"
                                                      "Things(20)/Datastreams",
                    "Datastreams": [],
                    "Datastreams@iot.count": 6,
                    "Datastreams@iot.nextLink": "https://server.de/SensorThingsService/v1.0/Things(20)/"
                                                "Datastreams?$top=2&$skip=2&$count=true",
                    "MultiDatastreams@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/"
                                                           "Things(20)/MultiDatastreams",
                    "Locations@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/Things(20)/Locations",
                    "HistoricalLocations@iot.navigationLink": "https://server.de/SensorThingsService/v1.0/"
                                                              "Things(20)/HistoricalLocations",
                    "@iot.id": 20,
                    "@iot.selfLink": "https://server.de/SensorThingsService/v1.0/Things(20)"
                }
            ]
        }

        things = frost_sta_client.utils.transform_json_to_entity_list(json_dict, 'frost_sta_client.model.thing.Thing')

        self.assertEqual('https://server.de/SensorThingsService/v1.0/Things?$top=2&$'
                         'skip=14&$expand=Datastreams%28%24top%3D2%3B%24count%3Dtrue%29', things.next_link)

        thing = things.entities[0]
        self.assertEqual(19, thing.id)
        self.assertEqual('Recoaro 1000', thing.name)
        self.assertEqual('Weather station Recoaro 1000', thing.description)

        ds_list = thing.datastreams
        self.assertEqual('https://server.de/SensorThingsService/v1.0/Things(19)/Datastreams?$top=2&$skip=2&$count=true',
                         ds_list.next_link)
        # self.assertEqual(6, ds_list.count)

        ds = ds_list.entities[0]
        self.assertEqual('Air Temperature Recoaro 1000', ds.name)
        self.assertEqual('The Air Temperature at Recoaro 1000', ds.description)

        result = ds.observations.entities[0].result
        self.assertEqual(0, result)

        ds = ds_list.entities[1]
        self.assertEqual(130, ds.id)
        self.assertEqual('Precipitation Recoaro 1000', ds.name)
        self.assertEqual('The Precipitation at Recoaro 1000', ds.description)

        thing = things.entities[1]
        self.assertEqual(20, thing.id)
        self.assertEqual('Valdagno', thing.name)
        self.assertEqual('Weather station Valdagno', thing.description)

        ds_list = thing.datastreams
        self.assertEqual('https://server.de/SensorThingsService/v1.0/Things(20)/Datastreams?$top=2&$skip=2&$count=true',
                         ds_list.next_link)
        # self.assertEqual(6, ds_list.count)

    def test_read_empty_entity_list(self):
        json_dict = {'value': []}
        things = frost_sta_client.utils.transform_json_to_entity_list(json_dict, 'frost_sta_client.model.thing.Thing')

        self.assertEqual(None, things.next_link)
        self.assertTrue(len(things.entities) == 0)

    def test_read_tasking_capabilities(self):
        json_dict = {
            'name': 'createNewVA',
            'description': 'Virtual Actuator Server, starts new Virtual Actuators',
            'taskingParameters': {
                'type': 'DataRecord',
                'field': [{
                    'type': 'Text',
                    'label': 'Aktor-Name',
                    'description': 'Name des neuen virtuellen Aktors',
                    'name': 'vaName'
                }, {
                    'type': 'Text',
                    'label': 'Aktor-Beschreibung',
                    'description': 'Beschreibung des neuen virtuellen Aktors',
                    'name': 'vaDescription'
                }]
            },
            'Actuator@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/Actuator',
            'Thing@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)/Thing',
            'Tasks@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)/Tasks',
            '@iot.id': 1,
            '@iot.selfLink': 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)'}

        capability = frost_sta_client.utils. \
            transform_json_to_entity(json_dict,
                                     'frost_sta_client.model.tasking_capability.TaskingCapability')

        expected = frost_sta_client.model.tasking_capability.TaskingCapability()
        expected.name = 'createNewVA'
        expected.description = 'Virtual Actuator Server, starts new Virtual Actuators'
        expected.tasking_parameters = {
            'type': 'DataRecord',
            'field': [{
                'type': 'Text',
                'label': 'Aktor-Name',
                'description': 'Name des neuen virtuellen Aktors',
                'name': 'vaName'
            }, {
                'type': 'Text',
                'label': 'Aktor-Beschreibung',
                'description': 'Beschreibung des neuen virtuellen Aktors',
                'name': 'vaDescription'
            }]
        }
        expected.id = 1
        expected.self_link = 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)'

        self.assertEqual(expected, capability)

    def test_read_tasking_capabilities_with_constraint(self):
        json_dict = {
            'name': 'DatastreamCopierCapability',
            'description': 'Copies Observations from one Datastream to another',
            'taskingParameters':
                {
                    'type': 'DataRecord',
                    'field': [{
                        'type': 'Count',
                        'name': 'sourceDatastream',
                        'label': 'Source Datastream',
                        'description': 'ID of the datastream from which the observations should be taken.',
                        'constraint': {
                            'type': 'AllowedValues',
                            'interval': [[0, 10000]]
                        }
                    },
                        {
                            'type': 'Count',
                            'name': 'destinationDatastream',
                            'label': 'Destination Datastream',
                            'description': 'ID of the datastream to which the observations should be copied.',
                            'constraint': {
                                'type': 'AllowedValues',
                                'interval': [[0, 10000]]
                            }
                        }]
                },
            'Actuator@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/Actuator',
            'Thing@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)/Thing',
            'Tasks@iot.navigationLink': 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)/Tasks',
            '@iot.id': 1,
            '@iot.selfLink': 'https://server.de/SensorThingsService/v1.0/TaskingCapabilities(1)'
        }

        entity_class = 'frost_sta_client.model.tasking_capability.TaskingCapability'
        capability = frost_sta_client.utils.transform_json_to_entity(json_dict, entity_class)

        expected = frost_sta_client.model.tasking_capability.TaskingCapability()
        expected.name = 'DatastreamCopierCapability'
        expected.description = 'Copies Observations from one Datastream to another'
        expected.id = 1
        expected.tasking_parameters = {
                    'type': 'DataRecord',
                    'field': [{
                        'type': 'Count',
                        'name': 'sourceDatastream',
                        'label': 'Source Datastream',
                        'description': 'ID of the datastream from which the observations should be taken.',
                        'constraint': {
                            'type': 'AllowedValues',
                            'interval': [[0, 10000]]
                        }
                    },
                        {
                            'type': 'Count',
                            'name': 'destinationDatastream',
                            'label': 'Destination Datastream',
                            'description': 'ID of the datastream to which the observations should be copied.',
                            'constraint': {
                                'type': 'AllowedValues',
                                'interval': [[0, 10000]]
                            }
                        }]
                }

        self.assertEqual(expected, capability)
