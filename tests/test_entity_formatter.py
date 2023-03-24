import unittest
from geojson import Point

import frost_sta_client.model.location
import frost_sta_client.model.thing
import frost_sta_client.utils
import frost_sta_client.model.ext.entity_list
from frost_sta_client.model.ext import entity_type


class TestEntityFormatter(unittest.TestCase):
    
    def test_create_thing_basic(self):
        exp_result = dict(name='nice thing',
                          description='the description of the thing',
                          properties=dict(
                                    nice=True,
                                    level_of_niceness=1000
                                )
                          )
        entity = frost_sta_client.model.thing.Thing()
        entity.name = 'nice thing'
        entity.description = 'the description of the thing'
        properties = {'nice': True, 'level_of_niceness': 1000}
        entity.properties = properties
        entity_json = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        self.assertDictEqual(exp_result, entity_json)

    def test_write_thing_completely_empty(self):
        result = {}

        entity = frost_sta_client.model.thing.Thing()
        entity_json = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        self.assertDictEqual(result, entity_json)

    def test_write_thing_with_location(self):
        result = {'name': 'another nice thing',
                  'description': 'This thing has also a nice location',
                  'Locations': [
                      {
                          '@iot.id': 1,
                      }
                  ]}
        entity = frost_sta_client.model.thing.Thing()
        entity.name = 'another nice thing'
        entity.description = 'This thing has also a nice location'
        entity.properties = {}

        location = frost_sta_client.model.location.Location()
        location.id = 1
        entity.locations = frost_sta_client.model.ext.entity_list.EntityList(entities=[location],
                                                                             entity_class=entity_type.EntityTypes['Location']['class'])
        entity_json = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        self.assertDictEqual(result, entity_json)


    def test_write_thing_with_specified_id_and_attributes(self):
        result = {'@iot.id': 123,
                  'name': 'another nice thing',
                  'Locations': [
                      {
                          '@iot.id': 456,
                          'name': 'location with specified id'
                      }
                  ],
                  'HistoricalLocations': [
                      {
                          '@iot.id': 789
                      }
                  ],
                  'Datastreams': [
                      {
                          'name': 'Datastream without specified id'
                      }
                  ],
                  }
        entity = frost_sta_client.model.thing.Thing(id=123)
        entity.name = 'another nice thing'

        location = frost_sta_client.model.location.Location(name='location with specified id')
        location.id = 456
        historical_location = frost_sta_client.model.historical_location.HistoricalLocation(id=789)
        datastream = frost_sta_client.model.datastream.Datastream(name='Datastream without specified id')

        entity.locations = frost_sta_client.model.ext.entity_list.EntityList(entities=[location],
                                                                             entity_class=entity_type.EntityTypes['Location']['class'])
        entity.historical_locations = frost_sta_client.model.ext.entity_list.EntityList(entities=[historical_location],
                                                                             entity_class=entity_type.EntityTypes['HistoricalLocation']['class'])
        entity.datastreams = frost_sta_client.model.ext.entity_list.EntityList(entities=[datastream], entity_class=entity_type.EntityTypes['Datastream']['class'])
        entity_json = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        self.assertDictEqual(result, entity_json)


    def test_incorrect_collection(self):
        exp_result = {
            'name': 'test thing',
            'description': 'incorrect thing for testing',
            'Locations': [
                {
                    'name': 'favorite place',
                    'description': 'this is my favorite place',
                    'encodingType': 'application/vnd.geo+json',
                    'location': {
                        'type': 'Point',
                        'coordinates': [-49.593, 85.23]
                    }
                }
            ]
        }

        entity = frost_sta_client.model.thing.Thing()
        entity.name = 'test thing'
        entity.description = 'incorrect thing for testing'
        
        location = frost_sta_client.model.location.Location()
        location.name = 'favorite place'
        location.description = 'this is my favorite place'
        location.encoding_type = 'application/vnd.geo+json'
        location.location = Point((-49.593, 85.23))
        
        entity.locations = frost_sta_client.model.ext.entity_list.EntityList(entities=[location],
                                                                             entity_class=entity_type.EntityTypes['Location']['class'])
        entity_json = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        self.assertDictEqual(exp_result, entity_json)

    def test_write_location_geojson(self):
        input_json = {
            '@iot.id': 1,
            'name': 'Treasure',
            'description': 'location of the treasure',
            'encodingType': 'application/vnd.geo+json',
            'location': {
                'type': 'Point',
                'coordinates': [-49.593, 85.23]
            }
        }
        exp_result = frost_sta_client.model.location.Location()
        exp_result.id = 1
        exp_result.name = 'Treasure'
        exp_result.description = 'location of the treasure'
        exp_result.encoding_type = 'application/vnd.geo+json'
        exp_result.location = Point((-49.593, 85.23))
        result = frost_sta_client.utils.transform_json_to_entity(input_json, 'frost_sta_client.model.location.Location')
        self.assertEqual(result, exp_result)


if __name__ == '__main__':
    unittest.main()
