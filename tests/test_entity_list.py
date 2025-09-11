from frost_sta_client.utils import transform_json_to_entity_list
from frost_sta_client.service.sensorthingsservice import SensorThingsService


class MockResponse:
    def __init__(self, json_data):
        self._json = json_data
        self.status_code = 200

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


class DummyService(SensorThingsService):
    def __init__(self, url, page2):
        super().__init__(url)
        self.page2 = page2
        self.calls = 0

    def execute(self, method, url, **kwargs):
        self.calls += 1
        return MockResponse(self.page2)


def test_entity_list_iterates_across_pages():
    page1 = {
        "value": [
            {"@iot.id": 1, "name": "A"},
            {"@iot.id": 2, "name": "B"},
        ],
        "@iot.nextLink": "http://example.org/FROST-Server/v1.1/Things?$skip=2"
    }
    page2 = {
        "value": [
            {"@iot.id": 3, "name": "C"},
            {"@iot.id": 4, "name": "D"},
        ]
    }
    elist = transform_json_to_entity_list(page1, 'frost_sta_client.model.thing.Thing')
    svc = DummyService('http://example.org/FROST-Server/v1.1', page2)
    elist.set_service(svc)
    called = []
    elist.step_size = 2
    elist.callback = lambda idx: called.append(idx)
    names = [e.name for e in elist]
    assert names == ['A', 'B', 'C', 'D']
    assert called == [0, 2]
