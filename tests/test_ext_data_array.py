import pytest
from frost_sta_client.model.ext.data_array_value import DataArrayValue as DAV
from frost_sta_client.model.observation import Observation
from frost_sta_client.model.datastream import Datastream
from frost_sta_client.model.feature_of_interest import FeatureOfInterest


def test_data_array_value_components_and_add_observation():
    dav = DAV()
    ds = Datastream()
    ds.id = 99
    dav.datastream = ds
    components = {DAV.Property.PHENOMENON_TIME, DAV.Property.RESULT, DAV.Property.FEATURE_OF_INTEREST}
    dav.components = components
    o = Observation(result=3, phenomenon_time='2023-01-01T00:00:00Z', feature_of_interest=FeatureOfInterest(id=1), datastream=ds)
    dav.add_observation(o)
    state = dav.__getstate__()
    assert 'components' in state and 'dataArray' in state and state['Datastream']['@iot.id'] == 99
    with pytest.raises(ValueError):
        dav.components = components
