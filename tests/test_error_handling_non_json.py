import pytest
import requests
import json
from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.utils import transform_json_to_entity_list
from frost_sta_client.model.thing import Thing


class DummyService(SensorThingsService):
    def __init__(self, url):
        super().__init__(url)

    def execute(self, method, url, **kwargs):
        class Resp:
            status_code = 500
            text = "<html>Server Error</html>"

            def json(self):
                raise ValueError("No JSON body")

        raise requests.exceptions.HTTPError(response=Resp())


def test_query_handles_non_json_error():
    svc = DummyService('http://example.org/FROST-Server/v1.1')
    with pytest.raises(requests.exceptions.HTTPError):
        svc.things().query().list()


def test_basedao_handles_non_json_error():
    svc = DummyService('http://example.org/FROST-Server/v1.1')
    with pytest.raises(requests.exceptions.HTTPError):
        svc.things().find(1)


def test_entitylist_iter_handles_non_json_error():
    svc = DummyService('http://example.org/FROST-Server/v1.1')
    page = {"value": [], "@iot.nextLink": "http://example.org/next"}
    elist = transform_json_to_entity_list(page, 'frost_sta_client.model.thing.Thing')
    elist.set_service(svc)
    it = iter(elist)
    with pytest.raises(requests.exceptions.HTTPError):
        next(it)


class WorkingService(SensorThingsService):
    def __init__(self, url):
        super().__init__(url)

    def execute(self, method, url, **kwargs):
        class Resp:
            status_code = 400
            text = '{"code":400,"type":"error","message":"Not a valid path for DELETE."}'

            def json(self):
                return json.loads(self.text)

        raise requests.exceptions.HTTPError(response=Resp())


def test_basedao_handles_json_error(caplog):
    svc = WorkingService('http://example.org/FROST-Server/v1.1/Things')
    with pytest.raises(requests.exceptions.HTTPError):
        thing = Thing(id=1)
        svc.delete(thing)
    assert caplog.messages[-1] == "Deleting Thing failed with status-code 400, Not a valid path for DELETE."
