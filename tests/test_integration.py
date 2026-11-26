import os

import pytest
from geojson import Point

import frost_sta_client as fsc

pytestmark = pytest.mark.skipif(
    os.environ.get("FROST_STA_CLIENT_RUN_INTEGRATION") != "1",
    reason="Integration tests require FROST server. Set FROST_STA_CLIENT_RUN_INTEGRATION=1 to run.",
)


def test_create_thing(sensorthings_service):
    thing = fsc.Thing(name="Test Thing", description="A test thing")
    sensorthings_service.create(thing)
    assert thing.id is not None
    retrieved = sensorthings_service.things().find(thing.id)
    assert retrieved.name == "Test Thing"


def test_crud_datastream(sensorthings_service):
    thing = fsc.Thing(name="Test Thing DS", description="Thing for DS")
    sensorthings_service.create(thing)
    sensor = fsc.Sensor(
        name="Test Sensor",
        description="Sensor",
        encoding_type="application/pdf",
        metadata="http://example.org/sensor.pdf",
    )
    sensorthings_service.create(sensor)
    observed = fsc.ObservedProperty(
        name="Test OP",
        definition="http://www.example.org/op",
        description="OP",
    )
    sensorthings_service.create(observed)
    unit = fsc.UnitOfMeasurement(name="degree Celsius", symbol="°C", definition="physical definition...")
    datastream = fsc.Datastream(
        name="Test DS",
        description="DS",
        observation_type="OM_Measurement",
        unit_of_measurement=unit,
        thing=thing,
        sensor=sensor,
        observed_property=observed,
    )
    sensorthings_service.create(datastream)
    assert datastream.id is not None
    retrieved = sensorthings_service.datastreams().find(datastream.id)
    assert retrieved.name == "Test DS"
    retrieved.description = "Updated DS"
    sensorthings_service.update(retrieved)
    updated = sensorthings_service.datastreams().find(datastream.id)
    assert updated.description == "Updated DS"
    sensorthings_service.delete(updated)
    with pytest.raises(Exception):
        sensorthings_service.datastreams().find(datastream.id)


def test_crud_observation(sensorthings_service):
    thing = fsc.Thing(name="Test Thing Obs", description="Thing for Obs")
    sensorthings_service.create(thing)
    sensor = fsc.Sensor(
        name="Test Sensor Obs",
        description="Sensor Obs",
        encoding_type="application/pdf",
        metadata="http://example.org/sensor_obs.pdf",
    )
    sensorthings_service.create(sensor)
    observed = fsc.ObservedProperty(
        name="Test OP Obs",
        definition="http://www.example.org/op_obs",
        description="OP Obs",
    )
    sensorthings_service.create(observed)
    unit = fsc.UnitOfMeasurement(name="degree Celsius", symbol="°C", definition="physical definition...")
    datastream = fsc.Datastream(
        name="Test DS Obs",
        description="DS Obs",
        observation_type="OM_Measurement",
        unit_of_measurement=unit,
        thing=thing,
        sensor=sensor,
        observed_property=observed,
    )
    sensorthings_service.create(datastream)
    point = Point((-115.81, 37.24))
    feature = fsc.FeatureOfInterest(
        name="here",
        description="and there",
        feature=point,
        encoding_type="application/geo+json",
    )
    observation = fsc.Observation(
        result=25.0,
        phenomenon_time="2023-01-01T00:00:00Z",
        datastream=datastream,
        feature_of_interest=feature,
    )
    sensorthings_service.create(observation)
    assert observation.id is not None
    retrieved = sensorthings_service.observations().find(observation.id)
    assert retrieved.result == 25.0
    assert retrieved.phenomenon_time == observation.phenomenon_time
    retrieved.result = 30.0
    sensorthings_service.update(retrieved)
    updated = sensorthings_service.observations().find(observation.id)
    assert updated.result == 30.0
    sensorthings_service.delete(updated)
    with pytest.raises(Exception):
        sensorthings_service.observations().find(observation.id)


def test_default_model_does_not_match_the_fully_enabled_server(sensorthings_service):
    auth = sensorthings_service.auth_handler
    service = fsc.SensorThingsService(
        "http://localhost:8080/FROST-Server/v1.1",
        auth_handler=auth,
    )
    assert service.extensions == (False, True, False)
    with pytest.raises(RuntimeError, match="does not match"):
        service.things().query().list()


def test_actuation_model_follows_the_plugin(sensorthings_service):
    auth = sensorthings_service.auth_handler
    enabled = fsc.SensorThingsService(
        "http://localhost:8080/FROST-Server/v1.1",
        (True, True, True),
        auth_handler=auth,
    )
    assert enabled.things().query().top(1).list() is not None
    assert callable(enabled.actuators)
    plain = fsc.SensorThingsService(
        "http://localhost:8082/FROST-Server/v1.1",
        (False, True, True),
        auth_handler=auth,
    )
    with pytest.raises(RuntimeError, match="Actuator"):
        plain.things().query().list()


def test_default_model_matches_unchanged_frost_2_8_2(sensorthings_service):
    service = fsc.SensorThingsService(
        "http://localhost:8082/FROST-Server/v1.1",
        auth_handler=sensorthings_service.auth_handler,
    )
    assert service.things().query().list() is not None
    assert getattr(service, "multi_datastreams", None) is None
    assert getattr(service, "actuators", None) is None
    assert callable(service.create_observations)


def test_default_model_does_not_match_odata_on_frost_2_8_2(sensorthings_service):
    auth = sensorthings_service.auth_handler
    for root in (
        "http://localhost:8080/FROST-Server/ODATA_4.0",
        "http://localhost:8080/FROST-Server/ODATA_4.01",
    ):
        service = fsc.SensorThingsService(root, auth_handler=auth)
        with pytest.raises(RuntimeError, match="CreateObservations"):
            service.create(fsc.Thing(name="OData thing", description="default model"))


def test_odata_roots_roundtrip_a_linked_location(sensorthings_service, tmp_path):
    auth = sensorthings_service.auth_handler
    for root in (
        "http://localhost:8080/FROST-Server/ODATA_4.0",
        "http://localhost:8080/FROST-Server/ODATA_4.01",
    ):
        service = fsc.SensorThingsService.open(root, tmp_path / root.rstrip("/").split("/")[-1], auth_handler=auth)
        located = fsc.Location(
            name="OData location",
            description="linked",
            encoding_type="application/geo+json",
            location=Point((8.4, 49.0)),
        )
        service.create(located)
        thing = fsc.Thing(name="OData thing", description="linked", locations=[located])
        service.create(thing)
        retrieved = service.things().find(thing.id)
        assert retrieved.name == "OData thing"
        assert retrieved.self_link.startswith(root)
        linked = retrieved.get_locations().query().list()
        assert linked.entities[0].id == located.id


def test_v11_calls_create_observations_from_the_loaded_model(sensorthings_service):
    import requests

    try:
        sensorthings_service.invoke("CreateObservations", [])
    except requests.HTTPError:
        return


def test_open_loads_the_model_of_that_root(sensorthings_service, tmp_path):
    import frost_sta_client.generated.model as bundled

    auth = sensorthings_service.auth_handler
    root = "http://localhost:8080/FROST-Server/ODATA_4.0"
    opened = fsc.SensorThingsService.open(root, tmp_path / "odata40", auth_handler=auth)
    assert opened.model is not bundled
    assert opened.write_prefix == "@odata"
    loaded = opened.things().entity_class
    assert loaded is not fsc.Thing
    thing = loaded(name="loaded model", description="from this root")
    opened.create(thing)
    assert thing.id is not None
    retrieved = opened.things().find(thing.id)
    assert retrieved.name == "loaded model"
    assert type(retrieved) is loaded
    opened.delete(thing)
    with pytest.raises(RuntimeError, match="CreateObservations"):
        opened.invoke("CreateObservations", [])
