from frost_sta_client.model.thing import Thing
from frost_sta_client.model.location import Location
from frost_sta_client.model.sensor import Sensor
from frost_sta_client.model.observedproperty import ObservedProperty
from frost_sta_client.model.datastream import Datastream
from frost_sta_client.model.observation import Observation
from frost_sta_client.model.feature_of_interest import FeatureOfInterest
from frost_sta_client.model.multi_datastream import MultiDatastream
from frost_sta_client.model.actuator import Actuator
from frost_sta_client.model.tasking_capability import TaskingCapability
from frost_sta_client.model.task import Task
from frost_sta_client.model.ext.unitofmeasurement import UnitOfMeasurement

def test_equality_thing():
    a = Thing(id=1, name='A', description='d', properties={'x': 1})
    b = Thing(id=1, name='A', description='d', properties={'x': 1})
    assert a == b
    b.description = 'changed'
    assert a != b

def test_equality_location():
    a = Location(id=2, name='L', description='d', encoding_type='application/geo+json')
    b = Location(id=2, name='L', description='d', encoding_type='application/geo+json')
    assert a == b
    b.encoding_type = 'application/vnd.geo+json'
    assert a != b

def test_equality_sensor():
    a = Sensor(id=3, name='S', description='d', encoding_type='application/pdf', metadata='http://example.org/sensor.pdf', properties={'a': 1})
    b = Sensor(id=3, name='S', description='d', encoding_type='application/pdf', metadata='http://example.org/sensor.pdf', properties={'a': 1})
    assert a == b
    b.metadata = 'http://example.org/other.pdf'
    assert a != b

def test_equality_observed_property():
    a = ObservedProperty(id=4, name='OP', definition='http://def', description='d', properties={'p': 1})
    b = ObservedProperty(id=4, name='OP', definition='http://def', description='d', properties={'p': 1})
    assert a == b
    b.definition = 'http://changed'
    assert a != b

def test_equality_feature_of_interest():
    feat = {'type': 'Point', 'coordinates': [0, 0]}
    a = FeatureOfInterest(id=5, name='FOI', description='d', encoding_type='application/geo+json', feature=feat, properties={'p': True})
    b = FeatureOfInterest(id=5, name='FOI', description='d', encoding_type='application/geo+json', feature=feat, properties={'p': True})
    assert a == b
    b.description = 'changed'
    assert a != b

def test_equality_unit_of_measurement():
    u1 = UnitOfMeasurement(name='degree Celsius', symbol='°C', definition='ucum:Cel')
    u2 = UnitOfMeasurement(name='degree Celsius', symbol='°C', definition='ucum:Cel')
    assert u1 == u2
    u2.symbol = 'K'
    assert u1 != u2

def test_equality_datastream():
    u1 = UnitOfMeasurement(name='degree Celsius', symbol='°C', definition='ucum:Cel')
    a = Datastream(id=6, name='DS', description='d', observation_type='OM_Measurement', unit_of_measurement=u1, properties={'x': 1})
    u2 = UnitOfMeasurement(name='degree Celsius', symbol='°C', definition='ucum:Cel')
    b = Datastream(id=6, name='DS', description='d', observation_type='OM_Measurement', unit_of_measurement=u2, properties={'x': 1})
    assert a == b
    b.observation_type = 'Other'
    assert a != b

def test_equality_observation():
    a = Observation(id=7, result=1.0, phenomenon_time='2023-01-01T00:00:00Z', parameters={'a': 1})
    b = Observation(id=7, result=1.0, phenomenon_time='2023-01-01T00:00:00Z', parameters={'a': 1})
    assert a == b
    b.result = 2.0
    assert a != b

def test_equality_multi_datastream():
    a = MultiDatastream(id=8, name='MDS', description='d', observation_type='OM_Complex', multi_observation_data_types=['int', 'double'])
    b = MultiDatastream(id=8, name='MDS', description='d', observation_type='OM_Complex', multi_observation_data_types=['int', 'double'])
    assert a == b
    b.multi_observation_data_types = ['int']
    assert a != b

def test_equality_actuator():
    a = Actuator(id=9, name='A', description='d', encoding_type='application/json', metadata='{}', properties={'x': 1})
    b = Actuator(id=9, name='A', description='d', encoding_type='application/json', metadata='{}', properties={'x': 1})
    assert a == b
    b.description = 'changed'
    assert a != b

def test_equality_tasking_capability():
    a = TaskingCapability(id=10, name='TC', description='d', tasking_parameters={'a': 1}, properties={'x': 1})
    b = TaskingCapability(id=10, name='TC', description='d', tasking_parameters={'a': 1}, properties={'x': 1})
    assert a == b
    b.name = 'changed'
    assert a != b

def test_equality_task():
    a = Task(id=11, tasking_parameters={'a': 1}, creation_time='2023-01-01T00:00:00Z')
    b = Task(id=11, tasking_parameters={'a': 1}, creation_time='2023-01-01T00:00:00Z')
    assert a == b
    b.creation_time = '2023-01-02T00:00:00Z'
    assert a != b
