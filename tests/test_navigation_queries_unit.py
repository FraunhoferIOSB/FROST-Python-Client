import pytest
import frost_sta_client.model.ext.entity_list
from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.model import thing, location, sensor, observedproperty, datastream, observation, feature_of_interest, multi_datastream, task, tasking_capability, historical_location

class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
    def json(self):
        return self._json
    def raise_for_status(self):
        pass

class DummyService(SensorThingsService):
    def __init__(self, url):
        super().__init__(url)
        self.calls = []
    def execute(self, method, url, **kwargs):
        self.calls.append((method, str(url)))
        return MockResponse(200, {'value': [{'@iot.id': 1}]})

SCENARIOS = [
    (thing.Thing, 'get_datastreams', datastream.Datastream, 'Things(1)/Datastreams'),
    (thing.Thing, 'get_locations', location.Location, 'Things(1)/Locations'),
    (thing.Thing, 'get_historical_locations', historical_location.HistoricalLocation, 'Things(1)/HistoricalLocations'),
    (thing.Thing, 'get_tasking_capabilities', tasking_capability.TaskingCapability, 'Things(1)/TaskingCapabilities'),
    (thing.Thing, 'get_multi_datastreams', multi_datastream.MultiDatastream, 'Things(1)/MultiDatastreams'),
    (datastream.Datastream, 'get_observations', observation.Observation, 'Datastreams(1)/Observations'),
    (feature_of_interest.FeatureOfInterest, 'get_observations', observation.Observation, 'FeaturesOfInterest(1)/Observations'),
    (sensor.Sensor, 'get_datastreams', datastream.Datastream, 'Sensors(1)/Datastreams'),
    (sensor.Sensor, 'get_multi_datastreams', multi_datastream.MultiDatastream, 'Sensors(1)/MultiDatastreams'),
    (location.Location, 'get_things', thing.Thing, 'Locations(1)/Things'),
    (location.Location, 'get_historical_locations', historical_location.HistoricalLocation, 'Locations(1)/HistoricalLocations'),
    (observedproperty.ObservedProperty, 'get_datastreams', datastream.Datastream, 'ObservedProperties(1)/Datastreams'),
    (observedproperty.ObservedProperty, 'get_multi_datastreams', multi_datastream.MultiDatastream, 'ObservedProperties(1)/MultiDatastreams'),
    (multi_datastream.MultiDatastream, 'get_observations', observation.Observation, 'MultiDatastreams(1)/Observations'),
    (multi_datastream.MultiDatastream, 'get_observed_properties', observedproperty.ObservedProperty, 'MultiDatastreams(1)/ObservedProperties'),
    (tasking_capability.TaskingCapability, 'get_tasks', task.Task, 'TaskingCapabilities(1)/Tasks'),
]

@pytest.mark.parametrize('parent_cls, accessor, expected_type, path_contains', SCENARIOS)
def test_navigation_queries_build_and_list(parent_cls, accessor, expected_type, path_contains):
    svc = DummyService('http://example.org/FROST-Server/v1.1')
    parent = parent_cls(id=1)
    parent.set_service(svc)
    dao = getattr(parent, accessor)()
    lst = dao.query().list()
    assert len(svc.calls) >= 1
    assert svc.calls[-1][0] == 'get'
    assert path_contains in svc.calls[-1][1]
    assert isinstance(lst, frost_sta_client.model.ext.entity_list.EntityList)
    assert isinstance(lst.entities[0], expected_type)
