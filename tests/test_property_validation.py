import pytest
from frost_sta_client.model.sensor import Sensor
from frost_sta_client.model.datastream import Datastream
from frost_sta_client.model.multi_datastream import MultiDatastream
from frost_sta_client.model.observation import Observation
from frost_sta_client.model.observedproperty import ObservedProperty
from frost_sta_client.model.feature_of_interest import FeatureOfInterest
from frost_sta_client.model.task import Task
from frost_sta_client.model.tasking_capability import TaskingCapability
from frost_sta_client.model.actuator import Actuator
from frost_sta_client.model.historical_location import HistoricalLocation
from frost_sta_client.model.location import Location
from frost_sta_client.generated.odata.datamodel import UnitOfMeasurement

def test_observed_property_properties_must_be_dict():
    op = ObservedProperty()
    with pytest.raises(ValueError):
        op.properties = 'not-a-dict'

def test_sensor_encoding_type_str():
    s = Sensor()
    with pytest.raises(ValueError):
        s.encoding_type = 123

def test_datastream_unit_of_measurement_type():
    ds = Datastream()
    with pytest.raises(ValueError):
        ds.unit_of_measurement = 'mismatch'
    ds.unit_of_measurement = UnitOfMeasurement(name='n', symbol='s', definition='d')

def test_multi_datastream_observed_area_type():
    mds = MultiDatastream()
    with pytest.raises(ValueError):
        mds.observed_area = 'invalid'

def test_observation_parameters_must_be_dict():
    o = Observation()
    with pytest.raises(ValueError):
        o.parameters = 'x'

def test_task_tasking_capability_type():
    t = Task()
    with pytest.raises(ValueError):
        t.tasking_capability = 'x'
    t.tasking_capability = TaskingCapability()

def test_feature_of_interest_feature_serializable():
    foi = FeatureOfInterest()
    with pytest.raises(TypeError):
        foi.feature = set([1, 2])

def test_actuator_tasking_capabilities_collection():
    a = Actuator()
    with pytest.raises(ValueError):
        a.tasking_capabilities = ['x']

def test_historical_location_locations_collection_types():
    hl = HistoricalLocation()
    with pytest.raises(ValueError):
        hl.locations = [Location(), 'x']
