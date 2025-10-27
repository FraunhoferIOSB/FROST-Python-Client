from frost_sta_client.model.ext.entity_type import EntityTypes, get_list_for_class
from frost_sta_client.model import thing, location, sensor, observedproperty, datastream, observation, feature_of_interest, multi_datastream, actuator, task, tasking_capability, historical_location

def test_get_list_for_all_core_classes():
    pairs = [
        (thing.Thing, 'Thing'),
        (location.Location, 'Location'),
        (sensor.Sensor, 'Sensor'),
        (observedproperty.ObservedProperty, 'ObservedProperty'),
        (datastream.Datastream, 'Datastream'),
        (observation.Observation, 'Observation'),
        (feature_of_interest.FeatureOfInterest, 'FeatureOfInterest'),
        (multi_datastream.MultiDatastream, 'MultiDatastream'),
        (actuator.Actuator, 'Actuator'),
        (task.Task, 'Task'),
        (tasking_capability.TaskingCapability, 'TaskingCapability'),
        (historical_location.HistoricalLocation, 'HistoricalLocation'),
    ]
    for clazz, key in pairs:
        assert get_list_for_class(clazz) == EntityTypes[key]['plural']

def test_relations_lists_contain_expected_entries():
    assert 'Datastreams' in EntityTypes['Thing']['relations_list']
    assert 'Locations' in EntityTypes['Thing']['relations_list']
    assert 'Datastreams' in EntityTypes['Sensor']['relations_list']
    assert 'Observations' in EntityTypes['Datastream']['relations_list']
    assert 'Tasks' in EntityTypes['TaskingCapability']['relations_list']
