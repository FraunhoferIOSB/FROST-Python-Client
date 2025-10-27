from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.model.ext.data_array_value import DataArrayValue as DAV
from frost_sta_client.model.ext.data_array_document import DataArrayDocument
from frost_sta_client.model.observation import Observation
from frost_sta_client.model.datastream import Datastream
from frost_sta_client.model.feature_of_interest import FeatureOfInterest

class DummyService(SensorThingsService):
    def __init__(self, url):
        super().__init__(url)
        self.calls = []
    def execute(self, method, url, **kwargs):
        self.calls.append((method, str(url)))
        class Resp:
            status_code = 201
            text = '["http://example.org/FROST-Server/v1.1/Observations(1)", "http://example.org/FROST-Server/v1.1/Observations(2)"]'
            def raise_for_status(self):
                pass
        return Resp()

def test_observation_create_via_data_array_document_unit():
    svc = DummyService('http://example.org/FROST-Server/v1.1')
    ds = Datastream(id=99)
    foi = FeatureOfInterest(id=1)
    dav = DAV()
    dav.datastream = ds
    dav.components = {DAV.Property.PHENOMENON_TIME, DAV.Property.RESULT, DAV.Property.FEATURE_OF_INTEREST}
    o1 = Observation(result=3, phenomenon_time='2023-01-01T00:00:00Z', datastream=ds, feature_of_interest=foi)
    o2 = Observation(result=5, phenomenon_time='2023-01-01T01:00:00Z', datastream=ds, feature_of_interest=foi)
    dav.add_observation(o1)
    dav.add_observation(o2)
    dad = DataArrayDocument()
    dad.add_data_array_value(dav)
    result_list = svc.observations().create(dad)
    assert len(result_list) == 2
    assert result_list[0].self_link.endswith('Observations(1)')
    assert result_list[1].self_link.endswith('Observations(2)')
