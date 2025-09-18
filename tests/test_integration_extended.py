import pytest
import os
pytestmark = pytest.mark.skipif(os.environ.get('FROST_STA_CLIENT_RUN_INTEGRATION') != '1', reason='Integration tests require FROST server. Set FROST_STA_CLIENT_RUN_INTEGRATION=1 to run.')
from geojson import Point
from frost_sta_client.model import thing, sensor, observedproperty, datastream, feature_of_interest
from frost_sta_client.model.ext import unitofmeasurement
from frost_sta_client.model.ext.data_array_value import DataArrayValue as DAV
from frost_sta_client.model.ext.data_array_document import DataArrayDocument
from frost_sta_client.model.observation import Observation

def test_crud_feature_of_interest(sensorthings_service):
    p = Point((8.4, 49.0))
    foi = feature_of_interest.FeatureOfInterest(name='FOI IT', description='desc', encoding_type='application/geo+json', feature=p, properties={'a': 1})
    sensorthings_service.create(foi)
    assert foi.id is not None
    fetched = sensorthings_service.features_of_interest().find(foi.id)
    assert fetched.name == 'FOI IT'
    fetched.description = 'updated'
    sensorthings_service.update(fetched)
    again = sensorthings_service.features_of_interest().find(foi.id)
    assert again.description == 'updated'
    sensorthings_service.delete(again)
    with pytest.raises(Exception):
        sensorthings_service.features_of_interest().find(foi.id)

def test_crud_location(sensorthings_service):
    p = Point((7.1, 50.2))
    loc = feature_of_interest.Location if False else None  # placeholder to avoid unused import warning
    from frost_sta_client.model.location import Location
    l = Location(name='Loc IT', description='d', encoding_type='application/geo+json', location=p, properties={'x': True})
    sensorthings_service.create(l)
    assert l.id is not None
    fetched = sensorthings_service.locations().find(l.id)
    assert fetched.name == 'Loc IT'
    fetched.description = 'updated'
    sensorthings_service.update(fetched)
    again = sensorthings_service.locations().find(l.id)
    assert again.description == 'updated'
    sensorthings_service.delete(again)
    with pytest.raises(Exception):
        sensorthings_service.locations().find(l.id)

def test_create_observations_with_data_array(sensorthings_service):
    # Create dependencies
    t = thing.Thing(name='Thing DA', description='for DA')
    sensorthings_service.create(t)
    s = sensor.Sensor(name='Sensor DA', description='s', encoding_type='application/pdf', metadata='http://example.org/s.pdf')
    sensorthings_service.create(s)
    op = observedproperty.ObservedProperty(name='OP DA', definition='http://op.example.org', description='op')
    sensorthings_service.create(op)
    u = unitofmeasurement.UnitOfMeasurement(name='degree Celsius', symbol='°C', definition='ucum:Cel')
    ds = datastream.Datastream(name='DS DA', description='d', observation_type='OM_Measurement', unit_of_measurement=u, thing=t, sensor=s, observed_property=op)
    sensorthings_service.create(ds)
    foi = feature_of_interest.FeatureOfInterest(name='FOI DA', description='d', encoding_type='application/geo+json', feature=Point((9.1, 48.7)))
    sensorthings_service.create(foi)

    # Prepare DataArray
    dav = DAV()
    dav.datastream = ds
    dav.components = {DAV.Property.PHENOMENON_TIME, DAV.Property.RESULT, DAV.Property.FEATURE_OF_INTEREST}
    o1 = Observation(result=10.5, phenomenon_time='2023-01-01T00:00:00Z', datastream=ds, feature_of_interest=foi)
    o2 = Observation(result=11.0, phenomenon_time='2023-01-01T01:00:00Z', datastream=ds, feature_of_interest=foi)
    dav.add_observation(o1)
    dav.add_observation(o2)
    dad = DataArrayDocument()
    dad.add_data_array_value(dav)

    # Create via /CreateObservations
    created = sensorthings_service.observations().create(dad)
    assert isinstance(created, list) and len(created) == 2
