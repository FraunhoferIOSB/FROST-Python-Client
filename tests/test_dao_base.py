from unittest.mock import Mock

import pytest
import requests
from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.model.thing import Thing
from frost_sta_client.utils import transform_entity_to_json_dict


class MockResponse:
    def __init__(self, status_code=200, json_data=None, headers=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}
        self.headers = headers or {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)


class DummyService(SensorThingsService):
    def __init__(self):
        super().__init__('http://example.org/FROST-Server/v1.1')
        self.calls = []

    def execute(self, method, url, **kwargs):
        self.calls.append((method, str(url), kwargs))
        if method == 'post':
            return MockResponse(201, {}, headers={'location': 'Things(42)'})
        if method == 'get':
            return MockResponse(200, {"@iot.id": 5, "name": "MyThing"})
        return MockResponse(200, {})


def test_base_dao_create_sets_id_and_service():
    svc = DummyService()
    t = Thing(name='X')
    svc.create(t)
    assert t.id == 42
    assert t.service is svc


@pytest.mark.parametrize(
    'location, response_url, expected_link, expected_id',
    [
        ('https://example.org/v1.1/Things(42)', None,
         'https://example.org/v1.1/Things(42)', 42),
        ('/FROST-Server/v1.1/Things(42)', None,
         'http://example.org/FROST-Server/v1.1/Things(42)', 42),
        ('Things(42)', None,
         'http://example.org/FROST-Server/v1.1/Things(42)', 42),
        ("Things('sensor-42')", None,
         "http://example.org/FROST-Server/v1.1/Things('sensor-42')", 'sensor-42'),
        ('Things(42)', 'https://example.org/redirected/v1.1/Things',
         'https://example.org/redirected/v1.1/Things(42)', 42),
    ],
)
def test_created_entity_self_link(monkeypatch, location, response_url, expected_link, expected_id):
    svc = DummyService()
    response = MockResponse(201, headers={'location': location})
    response.url = response_url
    execute = Mock(return_value=response)
    monkeypatch.setattr(svc, 'execute', execute)
    entity = Thing(name='X')

    svc.create(entity)

    assert entity.id == expected_id
    assert entity.service is svc
    assert entity.self_link == expected_link
    assert transform_entity_to_json_dict(entity) == {'@iot.id': expected_id, 'name': 'X'}
    execute.assert_called_once()
    assert execute.call_args.kwargs['json'] == {'name': 'X'}


def test_base_dao_find_returns_entity():
    svc = DummyService()
    found = svc.things().find(5)
    assert found.id == 5
    assert found.name == 'MyThing'
    assert found.service is svc


def test_base_dao_update_without_id_raises():
    svc = DummyService()
    t = Thing(name='noid')
    with pytest.raises(AttributeError):
        svc.update(t)


def test_base_dao_patch_validates_and_sends_headers():
    svc = DummyService()
    t = Thing(id=7)
    patches = [{"op": "replace", "path": "/name", "value": "new"}]
    svc.patch(t, patches)
    method, url, kwargs = svc.calls[-1]
    assert method == 'patch'
    assert kwargs['headers']['Content-type'] == 'application/json-patch+json'


def test_entity_path_formats_string_and_int():
    svc = DummyService()
    assert svc.things().entity_path(1) == 'Things(1)'
    assert svc.things().entity_path('abc') == "Things('abc')"
