import requests
import frost_sta_client.model.ext.entity_list
from frost_sta_client.service.sensorthingsservice import SensorThingsService


class MockResponse:
    def __init__(self, status_code=200, json_data=None):
        self.status_code = status_code
        self._json = json_data if json_data is not None else {}

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.exceptions.HTTPError(response=self)


class DummyService(SensorThingsService):
    def __init__(self, url, responses):
        super().__init__(url)
        self.responses = list(responses)
        self.calls = []

    def execute(self, method, url, **kwargs):
        self.calls.append((method, str(url)))
        if self.responses:
            return self.responses.pop(0)
        return MockResponse(200, {"value": [], "@iot.nextLink": None})


def test_query_builds_and_lists():
    first = MockResponse(200, {"value": [{"@iot.id": 1, "name": "A"}], "@iot.nextLink": None})
    svc = DummyService('http://example.org/FROST-Server/v1.1', [first])
    lst = svc.things().query().filter("name eq 'A'").select('name').orderby('name', 'ASC').top(1).skip(0).expand('Datastreams').list()
    assert len(svc.calls) == 1
    assert 'get' == svc.calls[0][0]
    assert 'Things' in svc.calls[0][1]
    assert '%24filter' in svc.calls[0][1]
    assert len(lst.entities) == 1
    assert isinstance(lst, frost_sta_client.model.ext.entity_list.EntityList)
    assert isinstance(lst.entities[0], frost_sta_client.model.thing.Thing)
