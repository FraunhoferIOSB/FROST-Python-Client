import pytest
import requests
from requests.auth import HTTPBasicAuth
from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.service.auth_handler import AuthHandler
from frost_sta_client.model.thing import Thing


def test_get_path_numeric_id():
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1')
    t = Thing(id=1)
    assert svc.get_path(t, 'Datastreams') == 'Things(1)/Datastreams'


def test_get_path_string_id():
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1/')
    t = Thing(id='abc')
    assert svc.get_path(t, 'Locations') == "Things('abc')/Locations"


def test_get_full_path_handles_trailing_slash():
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1/')
    t = Thing(id=2)
    full = svc.get_full_path(t, 'Datastreams')
    assert str(full) == 'http://example.org/FROST-Server/v1.1/Things(2)/Datastreams'


def test_auth_handler_type_check():
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1')
    with pytest.raises(ValueError):
        svc.auth_handler = 'not-auth'


def test_proxies_type_check():
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1')
    with pytest.raises(ValueError):
        svc.proxies = 'not-a-dict'
    svc.proxies = {'http': 'http://proxy'}


def test_execute_uses_auth(monkeypatch):
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1')
    svc.auth_handler = AuthHandler('user', 'pass')
    captured = {}

    def fake_request(method, url, proxies=None, auth=None, **kwargs):
        captured['auth'] = auth
        class R:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {}
        return R()

    monkeypatch.setattr(requests, 'request', fake_request)
    svc.execute('get', 'http://example.org')
    assert isinstance(captured['auth'], HTTPBasicAuth)
