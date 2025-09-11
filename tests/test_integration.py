import pytest
import os
pytestmark = pytest.mark.skipif(os.environ.get('FROST_STA_CLIENT_RUN_INTEGRATION') != '1', reason='Integration tests require FROST server. Set FROST_STA_CLIENT_RUN_INTEGRATION=1 to run.')
from geojson import Point
from frost_sta_client.model import thing, sensor, observedproperty, datastream, observation, feature_of_interest
from frost_sta_client.model.ext import unitofmeasurement


def test_create_thing(sensorthings_service):
    t = thing.Thing(
        name='Test Thing',
        description='A test thing')
    sensorthings_service.create(t)
    assert t.id is not None
    
    retrieved = sensorthings_service.things().find(t.id)
    assert retrieved.name == 'Test Thing'

    
def test_crud_datastream(sensorthings_service):
    # Create dependencies
    t = thing.Thing(
        name='Test Thing DS',
        description='Thing for DS')
    sensorthings_service.create(t)
    s = sensor.Sensor(
        name='Test Sensor',
        description='Sensor',
        encoding_type='application/pdf',
        metadata='http://example.org/sensor.pdf')
    sensorthings_service.create(s)
    op = observedproperty.ObservedProperty(
        name='Test OP',
        definition='http://www.example.org/op',
        description='OP')
    sensorthings_service.create(op)
    um = unitofmeasurement.UnitOfMeasurement(
        name="degree Celsius",
        symbol="°C",
        definition="physical definition...")
    
    # Create Datastream
    ds = datastream.Datastream(
        name='Test DS',
        description='DS',
        observation_type='OM_Measurement',
        unit_of_measurement=um,
        thing=t,
        sensor=s,
        observed_property=op)
    sensorthings_service.create(ds)
    assert ds.id is not None
    
    # Read
    retrieved_ds = sensorthings_service.datastreams().find(ds.id)
    assert retrieved_ds.name == 'Test DS'
    
    # Update
    retrieved_ds.description = 'Updated DS'
    sensorthings_service.update(retrieved_ds)
    updated_ds = sensorthings_service.datastreams().find(ds.id)
    assert updated_ds.description == 'Updated DS'
    
    # Delete
    sensorthings_service.delete(updated_ds)
    with pytest.raises(Exception):
        sensorthings_service.datastreams().find(ds.id)

        
def test_crud_observation(sensorthings_service):
    # Create dependencies
    t = thing.Thing(
        name='Test Thing Obs',
        description='Thing for Obs')
    sensorthings_service.create(t)
    s = sensor.Sensor(
        name='Test Sensor Obs',
        description='Sensor Obs',
        encoding_type='application/pdf',
        metadata='http://example.org/sensor_obs.pdf')
    sensorthings_service.create(s)
    op = observedproperty.ObservedProperty(
        name='Test OP Obs',
        definition='http://www.example.org/op_obs',
        description='OP Obs')
    sensorthings_service.create(op)
    um = unitofmeasurement.UnitOfMeasurement(
        name="degree Celsius",
        symbol="°C",
        definition="physical definition...")
    ds = datastream.Datastream(
        name='Test DS Obs',
        description='DS Obs',
        observation_type='OM_Measurement',
        unit_of_measurement=um,
        thing=t,
        sensor=s,
        observed_property=op)
    sensorthings_service.create(ds)
    point = Point((-115.81, 37.24))
    foi = feature_of_interest.FeatureOfInterest(name="here", description="and there", feature=point, encoding_type='application/geo+json')
    
    # Create Observation
    obs = observation.Observation(
        result=25.0,
        phenomenon_time='2023-01-01T00:00:00Z',
        datastream=ds,
        feature_of_interest=foi)
    sensorthings_service.create(obs)
    assert obs.id is not None
    
    # Read
    retrieved_obs = sensorthings_service.observations().find(obs.id)
    assert retrieved_obs.result == 25.0
    
    # Update
    retrieved_obs.result = 30.0
    sensorthings_service.update(retrieved_obs)
    updated_obs = sensorthings_service.observations().find(obs.id)
    assert updated_obs.result == 30.0
    
    # Delete
    sensorthings_service.delete(updated_obs)
    with pytest.raises(Exception):
        sensorthings_service.observations().find(obs.id)
