import pytest
import requests
from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.model.thing import Thing


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
