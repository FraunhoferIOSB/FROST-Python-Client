import pytest
from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.model import thing, location, sensor, observedproperty, datastream, observation, feature_of_interest, multi_datastream, actuator, task, tasking_capability, historical_location

class MockResponse:
    def __init__(self, status_code=200, json_data=None, headers=None, text=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.headers = headers or {}
        self.text = text or ''
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
        if method == 'post':
            return MockResponse(201, {}, headers={'location': 'Entity(100)'})
        if method == 'get':
            return MockResponse(200, {'@iot.id': 5})
        return MockResponse(200, {})

ENTITIES = [
    ('things', thing.Thing),
    ('locations', location.Location),
    ('sensors', sensor.Sensor),
    ('observed_properties', observedproperty.ObservedProperty),
    ('datastreams', datastream.Datastream),
    ('observations', observation.Observation),
    ('features_of_interest', feature_of_interest.FeatureOfInterest),
    ('actuators', actuator.Actuator),
    ('tasks', task.Task),
    ('tasking_capabilities', tasking_capability.TaskingCapability),
    ('historical_locations', historical_location.HistoricalLocation),
    ('multi_datastreams', multi_datastream.MultiDatastream),
]

@pytest.mark.parametrize('dao_method, entity_cls', ENTITIES)
def test_crud_create_find_update_delete_unit(dao_method, entity_cls):
    svc = DummyService('http://example.org/FROST-Server/v1.1')
    e = entity_cls()
    # Create
    svc.create(e)
    assert e.id == 100
    assert e.service is svc
    # Read
    found = getattr(svc, dao_method)().find(5)
    assert found.id == 5
    assert found.service is svc
    # Update
    e.id = 5
    svc.update(e)
    assert svc.calls[-1][0] == 'put'
    # Delete
    svc.delete(e)
    assert svc.calls[-1][0] == 'delete'
