"""Rules of the shared runtime, checked without a live server."""

import json
import subprocess
import sys
import warnings
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests
from geojson import Point

import frost_sta_client as fsc
from frost_sta_client.runtime.control import choose_control, format_key, parse_key
from frost_sta_client.runtime.entity import Entity
from frost_sta_client.runtime.entity_list import EntityList
from frost_sta_client.runtime.geo import coerce_geometry
from frost_sta_client.runtime.service import SensorThingsService
from frost_sta_client.runtime.specs import PropertySpec
from frost_sta_client.runtime.values import read_structural, write_structural

ROOT = Path(__file__).resolve().parents[1]
V11 = "http://example.org/FROST-Server/v1.1"
ODATA = "http://example.org/FROST-Server/ODATA_4.0"
ODATA_401 = "http://example.org/FROST-Server/ODATA_4.01/"


class Response:
    def __init__(self, payload=None, status_code=200, headers=None, text=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload
        if text is None and payload is not None:
            text = json.dumps(payload)
        self.text = text if text is not None else ""
        self.content = self.text.encode("utf-8")

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON body")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class RecordingService(SensorThingsService):
    def __init__(self, url, responses=None, metadata=None, control="@iot", extensions=(True, True)):
        super().__init__(url, extensions=extensions, metadata=metadata, control=control)
        self.responses = list(responses or [])
        self.calls = []

    def _exchange(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        if self.responses:
            response = self.responses.pop(0)
            if isinstance(response, Exception):
                raise response
            return response
        return Response({"value": []})


def service(url=V11, **kwargs):
    kwargs.setdefault("control", "@iot")
    return SensorThingsService(url, **kwargs)


def point(x=1, y=2):
    return {"type": "Point", "coordinates": [x, y]}


def location(**kwargs):
    values = {
        "name": "here",
        "description": "there",
        "encoding_type": "application/geo+json",
        "location": point(),
    }
    values.update(kwargs)
    return fsc.Location(**values)


def unit(**kwargs):
    values = {"name": "degree", "symbol": "deg", "definition": "a degree"}
    values.update(kwargs)
    return fsc.UnitOfMeasurement(**values)


def datastream(**kwargs):
    values = {
        "name": "ds",
        "description": "d",
        "observation_type": "OM_Measurement",
        "unit_of_measurement": unit(),
    }
    values.update(kwargs)
    return fsc.Datastream(**values)


def test_facade_names_resolve():
    assert callable(service().things)
    assert callable(service().features_of_interest)
    assert callable(service().multi_datastreams)
    assert callable(service().historical_locations)
    assert fsc.model.ext.data_array_value.DataArrayValue is fsc.DataArrayValue
    assert fsc.model.ext.data_array_document.DataArrayDocument is fsc.DataArrayDocument
    assert hasattr(fsc.HistoricalLocation, "get_locations")
    assert hasattr(fsc.Datastream, "get_thing")
    assert hasattr(fsc.Datastream, "get_observations")
    assert callable(service().observations().create)


def test_import_does_not_touch_jsonpickle_or_warnings():
    for path in (ROOT / "frost_sta_client").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "jsonpickle" not in text
        assert "set_preferred_backend" not in text
        assert "warnings.warn" not in text
        assert "raise Warning" not in text
    completed = subprocess.run(
        [sys.executable, "-c", "import sys, frost_sta_client; raise SystemExit('jsonpickle' in sys.modules)"],
        cwd=str(ROOT),
        check=False,
    )
    assert completed.returncode == 0


def test_none_empty_and_nullable():
    sta = service()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        empty = fsc.Sensor().to_json(sta)
        assert empty == {}
        assert fsc.Sensor.from_json(empty) == fsc.Sensor()
        sensor = fsc.Sensor(name="n", description="d", encoding_type="application/pdf")
        assert "metadata" not in sensor.to_json(sta)
        sensor.metadata = ""
        assert sensor.to_json(sta)["metadata"] == ""
        with pytest.raises(ValueError, match="metadata must not be None"):
            sensor.metadata = None
        with pytest.raises(ValueError, match="metadata must not be None"):
            fsc.Sensor.from_json({
                "name": "n",
                "description": "d",
                "encodingType": "application/pdf",
                "metadata": None,
            })
        with pytest.raises(ValueError, match="name must not be None"):
            fsc.Thing(name=None, description="d")
        thing = fsc.Thing(name="n", description="d", properties={})
        assert thing.to_json(sta)["properties"] == {}
        thing.properties = None
        assert "properties" not in thing.to_json(sta)
        stream = fsc.Datastream.from_json({
            "name": "n",
            "description": "d",
            "observationType": "OM_Measurement",
            "phenomenonTime": None,
        })
        assert stream.phenomenon_time is None
        assert "phenomenonTime" not in stream.to_json(sta)
        located = location(encoding_type="")
        body = located.to_json(sta)
        assert body["encodingType"] == ""
        assert fsc.Location.from_json(body) == located


def test_equality_includes_structural_fields_and_keys():
    assert fsc.Thing(id=1, name="A", description="d") != fsc.Thing(id=1, name="B", description="d")
    assert fsc.Thing(name="A", description="d") != fsc.Thing(id=1, name="A", description="d")
    left = datastream(id=5, phenomenon_time="2020-01-01T00:00:00Z")
    right = datastream(id=5, phenomenon_time="2021-01-01T00:00:00Z")
    assert left != right
    area_a = datastream(id=5, observed_area=point(1, 2))
    area_b = datastream(id=5, observed_area=point(3, 4))
    assert area_a != area_b
    same = fsc.Thing(id=1, name="A", description="d")
    other = fsc.Thing(id=1, name="A", description="d")
    same.locations = [location(id=2)]
    assert same == other
    keyed = datastream(id=1)
    other_keyed = datastream(id=1)
    keyed.thing = fsc.Thing(id=3, name="A", description="d")
    other_keyed.thing = fsc.Thing(id=4, name="A", description="d")
    assert keyed != other_keyed
    missing_key = datastream(id=1)
    absent = datastream(id=1)
    missing_key.thing = fsc.Thing(name="A", description="d")
    assert missing_key == absent


def test_navigation_rules():
    sta = service()
    thing = fsc.Thing(id=1, name="n", description="d")
    historical = fsc.HistoricalLocation(id=3, time="2020-01-01T00:00:00Z", thing=thing)
    thing.historical_locations = [historical]
    assert thing.to_json(sta)["HistoricalLocations"] == [{"@iot.id": 3}]
    fresh_history = fsc.HistoricalLocation(time="2020-01-01T00:00:00Z", thing=thing)
    thing.historical_locations = [fresh_history]
    body = thing.to_json(sta)
    assert body["HistoricalLocations"][0]["time"] == "2020-01-01T00:00:00Z"
    assert body["HistoricalLocations"][0]["Thing"] == {"@iot.id": 1}
    thing.locations = []
    assert "Locations" not in thing.to_json(sta)
    bare = datastream()
    bare.thing = fsc.Thing()
    assert "Thing" not in bare.to_json(sta)
    linked = fsc.Thing(name="n", description="d", locations=[location(id=8)])
    assert linked.to_json(sta)["Locations"] == [{"@iot.id": 8}]
    fresh = location()
    embedded = fsc.Thing(name="n", description="d", locations=[fresh])
    assert embedded.to_json(sta)["Locations"][0]["name"] == "here"
    placed = location()
    placed.things = []
    assert "Things" not in placed.to_json(sta)
    thing.historical_locations.entities[0].set_service(None)
    thing.set_service(sta)
    assert thing.historical_locations.entities[0].service is sta
    sensor = fsc.Sensor(
        name="n",
        description="d",
        encoding_type="application/pdf",
        metadata="http://example.org/s",
        datastreams=[datastream()],
    )
    sensor.set_service(sta)
    assert sensor.datastreams.entities[0].service is sta
    historical = fsc.HistoricalLocation(id=4, time="2020-01-01T00:00:00Z")
    historical.set_service(sta)
    assert historical.get_locations().collection_url().endswith("/HistoricalLocations(4)/Locations")
    stream = datastream(id=3)
    stream.set_service(sta)
    assert stream.get_thing().collection_url().endswith("/Datastreams(3)/Thing")


def test_navigation_link_count_and_collection_shapes():
    payload = {
        "name": "T",
        "description": "D",
        "Locations@iot.navigationLink": "http://example.org/Things(1)/Locations",
        "Locations@iot.count": 2,
    }
    sta = RecordingService(V11)
    thing = fsc.Thing.from_json(payload, sta)
    assert thing.locations.navigation_link.endswith("/Locations")
    assert thing.locations.count == 2
    assert thing.locations.entities == []
    sta.responses.append(Response({"value": []}))
    thing.get_locations().query().list()
    assert sta.calls[-1][1] == "http://example.org/Things(1)/Locations"
    counted = fsc.Thing.from_json({
        "name": "T",
        "description": "D",
        "Locations": [],
        "Locations@iot.count": 4,
        "Locations@iot.nextLink": "http://example.org/next",
    })
    assert counted.locations.count == 4
    assert counted.locations.next_link == "http://example.org/next"
    wrapped = fsc.Thing.from_json({
        "name": "T",
        "description": "D",
        "Locations": {"value": [{
            "@iot.id": 2,
            "name": "L",
            "description": "d",
            "encodingType": "application/geo+json",
            "location": point(),
        }]},
    })
    assert wrapped.locations.entities[0].id == 2
    assert type(wrapped.locations.entities[0].location).__name__ == "Point"
    array = fsc.Thing.from_json({
        "name": "T",
        "description": "D",
        "Locations": [{
            "@iot.id": 3,
            "name": "L",
            "description": "d",
            "encodingType": "application/geo+json",
            "location": point(),
        }],
    })
    assert array.locations.entities[0].id == 3
    sensor = fsc.Sensor.from_json({
        "name": "S",
        "description": "d",
        "encodingType": "application/pdf",
        "metadata": "http://example.org/s",
        "Datastreams": {"value": [{"@iot.id": 9, "name": "ds", "description": "d", "observationType": "OM_Measurement"}]},
    })
    assert sensor.datastreams.entities[0].id == 9

    class ExplodingList(EntityList):
        def __iter__(self):
            raise AssertionError("assignment iterated the list")

    owner = fsc.Thing(name="n", description="d")
    owner.locations = ExplodingList(entity_class=fsc.Location, entities=[location()])
    assert len(owner.locations.entities) == 1
    with pytest.raises(ValueError, match="locations should be a list of Location"):
        owner.locations = ["nope"]


def test_geometry_time_and_complex_lists():
    multi = [[[[0, 0], [1, 0], [1, 1], [0, 0]]]]
    located = location(location={"type": "MultiPolygon", "coordinates": multi})
    assert type(located.location).__name__ == "MultiPolygon"
    stream = fsc.MultiDatastream(name="n", description="d", observed_area=point())
    assert type(stream.observed_area).__name__ == "Point"
    stream.observed_area = {"type": "MultiPolygon", "coordinates": multi}
    assert type(stream.observed_area).__name__ == "MultiPolygon"
    with pytest.raises(ValueError, match="observed_area"):
        coerce_geometry(point(), "Edm.GeographyPolygon", "observed_area")
    feature = fsc.FeatureOfInterest(
        name="n",
        description="d",
        encoding_type="application/geo+json",
        feature=point(),
    )
    assert type(feature.feature).__name__ == "Point"
    plain = fsc.FeatureOfInterest(
        name="n",
        description="d",
        encoding_type="application/pdf",
        feature=point(),
    )
    assert type(plain.feature).__name__ == "Point"

    class Holder:
        _values = {"encoding_type": "application/pdf"}

    untyped = PropertySpec("payload", "payload", "Edm.Untyped")
    assert read_structural(untyped, point(), Holder()) == point()
    Holder._values = {"encoding_type": "application/geo+json"}
    assert type(read_structural(untyped, point(), Holder())).__name__ == "Point"
    loaded = fsc.Location.from_json(location(location=Point((-115.81, 37.24))).to_json(service()))
    assert loaded.location == Point((-115.81, 37.24))
    with pytest.raises(ValueError, match="time must be"):
        fsc.HistoricalLocation(time=[datetime(2020, 1, 1, tzinfo=timezone.utc)])
    measured = fsc.MultiDatastream(
        name="n",
        description="d",
        unit_of_measurements=[unit(name="degree", symbol="", definition=None)],
    )
    body = measured.to_json(service())
    assert body["unitOfMeasurements"] == [{"name": "degree", "symbol": ""}]
    again = fsc.MultiDatastream.from_json(body)
    assert again.unit_of_measurements[0].symbol == ""
    assert again.unit_of_measurements[0].definition is None
    wrapped_units = fsc.MultiDatastream.from_json({
        "name": "n",
        "description": "d",
        "unitOfMeasurements": {"value": [{"name": "n", "symbol": "s", "definition": "d"}]},
    })
    assert wrapped_units.unit_of_measurements[0].symbol == "s"
    measured.unit_of_measurements = []
    assert "unitOfMeasurements" not in measured.to_json(service())
    with pytest.raises(ValueError, match="multi_observation_data_types"):
        fsc.MultiDatastream.from_json({
            "name": "n",
            "description": "d",
            "multiObservationDataTypes": ["a", 2],
        })
    with pytest.raises(ValueError, match="definition should be of type str"):
        fsc.ObservedProperty(name="n", definition=1, description="d")


def test_time_values_compare_by_value_and_write_one_form():
    class TimeSample(Entity):
        __csdl_name__ = "TimeSample"
        __namespace__ = "test.time"
        __entity_set__ = "TimeSamples"
        __key_name__ = "id"
        __key_type__ = "Edm.Int64"
        __open_type__ = False
        __is_entity__ = True
        __properties__ = (
            PropertySpec("when", "when", "Edm.DateTimeOffset", nullable=True),
            PropertySpec("day", "day", "Edm.Date", nullable=True),
            PropertySpec("clock", "clock", "Edm.TimeOfDay", nullable=True),
            PropertySpec("span", "span", "Edm.Duration", nullable=True),
            PropertySpec("phenomenonTime", "phenomenon_time", "Edm.String", nullable=True),
        )
        __navigations__ = ()

    utc = timezone.utc
    left = TimeSample(
        when="2020-01-01T01:00:00+01:00",
        day="2020-05-06",
        clock="07:08:09.250000",
        span="PT90M",
    )
    right = TimeSample(
        when="2019-12-31T23:00:00-01:00",
        day=date(2020, 5, 6),
        clock=time(7, 8, 9, 250000),
        span=timedelta(hours=1, minutes=30),
    )
    assert left == right
    assert type(left.when) is datetime
    assert left.when.tzinfo is not None
    assert type(left.day) is date
    assert type(left.clock) is time
    assert type(left.span) is timedelta
    body = left.to_json(service())
    assert body["when"] == "2020-01-01T00:00:00Z"
    assert body["day"] == "2020-05-06"
    assert body["clock"] == "07:08:09.25"
    assert body["span"] == "PT1H30M"
    assert right.to_json(service())["when"] == body["when"]
    with pytest.raises(ValueError, match="when must be"):
        TimeSample(when="2020-01-01T00:00:00")
    with pytest.raises(ValueError, match="when must be"):
        TimeSample(when=datetime(2020, 1, 1))
    with pytest.raises(ValueError, match="clock must be"):
        TimeSample(clock="07:08:09Z")
    days = PropertySpec("days", "days", "Collection(Edm.Date)")
    assert read_structural(days, ["2020-01-01", "2020-01-02"], None) == [
        date(2020, 1, 1),
        date(2020, 1, 2),
    ]
    assert write_structural(days, [date(2020, 1, 1)], None) == ["2020-01-01"]

    same = datastream(id=5, phenomenon_time="2020-01-01T00:00:00Z")
    spelled = datastream(id=5, phenomenon_time="2020-01-01T01:00:00+01:00")
    assert same == spelled
    assert same.phenomenon_time.start == datetime(2020, 1, 1, tzinfo=utc)
    assert same.phenomenon_time.end is None
    assert not isinstance(same.phenomenon_time.start, str)

    instant = datetime(2020, 1, 1, tzinfo=utc)
    later = datetime(2020, 1, 2, tzinfo=utc)
    paired = fsc.Observation(phenomenon_time=(instant, later))
    written = fsc.Observation(phenomenon_time="2020-01-01T00:00:00+00:00/P1D")
    shifted = fsc.Observation(phenomenon_time="P1D/2020-01-02T01:00:00+01:00")
    assert paired.phenomenon_time == written.phenomenon_time
    assert written.phenomenon_time == shifted.phenomenon_time
    assert type(paired.phenomenon_time.start) is datetime
    assert type(paired.phenomenon_time.end) is datetime
    assert paired.to_json(service())["phenomenonTime"] == {
        "start": "2020-01-01T00:00:00Z",
        "end": "2020-01-02T00:00:00Z",
    }
    named = TimeSample(phenomenon_time="2020-01-01T01:00:00+01:00/2020-01-01T03:00:00+01:00")
    assert named.phenomenon_time == (instant, datetime(2020, 1, 1, 2, tzinfo=utc))
    assert named.to_json(service())["phenomenonTime"] == "2020-01-01T00:00:00Z/2020-01-01T02:00:00Z"
    with pytest.raises(ValueError, match="phenomenon_time must be"):
        fsc.Observation(phenomenon_time=[instant])


def test_odata_and_iot_prefixes():
    sta = service(V11, control="@iot")
    odata = service(ODATA, control="@odata")
    thing = fsc.Thing(id=5, name="A", description="B")
    iot_body = thing.to_json(sta)
    assert iot_body["@iot.id"] == 5
    assert iot_body["@iot.selfLink"].endswith("/Things(5)")
    assert "id" not in iot_body
    assert "@odata.id" not in iot_body
    odata_body = thing.to_json(odata)
    assert odata_body["id"] == 5
    assert odata_body["@odata.id"] == "http://example.org/FROST-Server/ODATA_4.0/Things(5)"
    assert "@iot.id" not in odata_body
    linked = fsc.Thing(name="n", description="d", locations=[location(id=8)])
    assert linked.to_json(odata)["Locations"] == [{
        "@odata.id": "http://example.org/FROST-Server/ODATA_4.0/Locations(8)",
    }]
    odata401 = service(ODATA_401, control="@")
    assert thing.to_json(odata401)["@id"] == "http://example.org/FROST-Server/ODATA_4.01/Things(5)"
    assert "@odata.id" not in thing.to_json(odata401)
    assert linked.to_json(odata401)["Locations"] == [{
        "@id": "http://example.org/FROST-Server/ODATA_4.01/Locations(8)",
    }]
    from_401 = fsc.Thing.from_json({
        "@id": "http://example.org/FROST-Server/ODATA_4.01/Things(7)",
        "id": 7,
        "name": "A",
        "description": "B",
        "Locations@navigationLink": "http://example.org/FROST-Server/ODATA_4.01/Things(7)/Locations",
        "Locations@count": 1,
    })
    assert from_401.id == 7
    assert from_401.self_link.endswith("/Things(7)")
    assert from_401.locations.navigation_link.endswith("/Locations")
    assert from_401.locations.count == 1
    by_iot = fsc.Thing.from_json({"@iot.id": 2, "id": 9, "name": "A", "description": "B"})
    assert by_iot.id == 2
    by_key = fsc.Thing.from_json({"id": 4, "name": "A", "description": "B"})
    assert by_key.id == 4
    by_url = fsc.Thing.from_json({
        "@odata.id": "http://example.org/FROST-Server/ODATA_4.0/Things(7)",
        "name": "A",
        "description": "B",
    })
    assert by_url.id is None
    assert by_url.self_link.endswith("/Things(7)")
    assert parse_key("http://example.org/Things(abc)", "Edm.String") == "abc"
    assert parse_key("http://example.org/Things(22)", "Edm.Int64") == 22
    assert parse_key(
        "http://example.org/Widgets(tenant='a',code=2)",
        "Edm.String",
    ) == {"tenant": "a", "code": 2}
    assert format_key("abc", "Edm.String") == "'abc'"
    with pytest.raises(ValueError):
        format_key(True, "Edm.Int64")
    with pytest.raises(ValueError):
        service().things().find(True)
    assert service("http://example.org").things().query().build_url() == "http://example.org/Things"


def test_vocabulary_is_probed_from_the_root_not_the_url():
    assert choose_control("4.01", True) == "@"
    assert choose_control("4.0", True) == "@odata"
    assert choose_control(None, True) == "@odata"
    assert choose_control(
        None,
        False,
        {"value": [{"name": "Things", "url": "http://example.org/Things"}]},
    ) == "@iot"
    with pytest.raises(ValueError):
        choose_control(None, False, {"value": []})
    quiet = RecordingService("http://example.org/ODATA_4.01", control="@iot")
    assert quiet.write_prefix == "@iot"
    assert quiet.calls == []
    assert choose_control(None, False, {"@odata.context": "http://example.org/$metadata"}) == "@odata"
    versioned = RecordingService(
        V11,
        [Response(text="<edmx:Edmx></edmx:Edmx>", headers={"OData-Version": "4.0"})],
        control=None,
    )
    assert versioned.write_prefix == "@odata"
    assert versioned.calls[0][1] == V11
    newer = RecordingService(
        "http://example.org/service",
        [Response(
            {"@context": "http://example.org/$metadata", "value": []},
            headers={"OData-Version": "4.01"},
        )],
        control=None,
    )
    assert newer.write_prefix == "@"
    assert newer.calls[0][1] == "http://example.org/service"
    sta_root = RecordingService(
        "http://example.org/ODATA_4.01",
        [Response({"value": [{"name": "Things", "url": "http://example.org/Things"}]})],
        control=None,
    )
    assert sta_root.write_prefix == "@iot"
    assert sta_root.calls[0][1] == "http://example.org/ODATA_4.01"
    assert len(sta_root.calls) == 1


def test_query_defaults_and_requests():
    query = service().things().query().filter("name eq 'A'").select("name").orderby("name").top(1).skip(0).count()
    assert query.params["$orderby"] == "name asc"
    assert query.orderby("name", "DESC").params["$orderby"] == "name desc"
    url = query.build_url()
    assert url.startswith("http://example.org/FROST-Server/v1.1/Things?")
    assert "%24filter" in url
    selected = service().things().query().select("name")
    with pytest.raises(TypeError):
        selected.select(1)
    with pytest.raises(TypeError):
        selected.select()
    assert selected.params["$select"] == "name"
    recorder = RecordingService(V11, [Response({"value": [{"@iot.id": 1, "name": "A", "description": "d"}]})])
    listing = recorder.things().query().filter("name eq 'A'").list()
    assert recorder.calls[0][0] == "get"
    assert listing.entities[0].name == "A"
    assert isinstance(listing, EntityList)

    class Refusing(SensorThingsService):
        def execute(self, method, url, **kwargs):
            raise AssertionError("request")

    with pytest.raises(TypeError):
        Refusing(V11).things().query().list(callback="nope", step_size=1)
    seen = []
    entities = [
        fsc.Thing(name="a", description="d"),
        fsc.Thing(name="b", description="d"),
        fsc.Thing(name="c", description="d"),
    ]
    page = EntityList(entity_class=fsc.Thing, entities=entities)
    page.arm(seen.append, 2)
    assert [item.name for item in page] == ["a", "b", "c"]
    assert seen == [0, 2]
    page.next_link = "http://example.org/next"
    assert page.get(0).name == "a"
    with pytest.raises(ValueError, match="index must be zero or positive"):
        page.get(-1)


def test_http_errors_and_create(caplog):
    html = Response(status_code=500, text="<html>Server Error</html>")

    def fail_html(method, url, **kwargs):
        raise requests.HTTPError(response=html)

    broken = RecordingService(V11)
    broken.execute = fail_html
    with pytest.raises(requests.HTTPError):
        broken.things().query().list()
    with pytest.raises(requests.HTTPError):
        broken.things().find(1)
    message = Response(status_code=400, text='{"message": "Not a valid path for DELETE."}')
    message._payload = {"code": 400, "type": "error", "message": "Not a valid path for DELETE."}

    def fail_json(method, url, **kwargs):
        raise requests.HTTPError(response=message)

    deleting = RecordingService(V11)
    deleting.execute = fail_json
    with caplog.at_level("ERROR"):
        with pytest.raises(requests.HTTPError):
            deleting.delete(fsc.Thing(id=1, name="n", description="d"))
    assert caplog.messages[-1] == "Deleting Thing failed with status-code 400, Not a valid path for DELETE."
    creating = RecordingService(V11, [Response(
        headers={"Location": "http://example.org/FROST-Server/v1.1/Things(22)"},
        text="",
    )])
    created = creating.create(fsc.Thing(name="n", description="d"))
    assert created.id == 22
    assert creating.calls[0][0] == "post"
    assert creating.calls[0][2]["json"]["name"] == "n"


def test_data_array_facade():
    sta = service()
    stream = datastream(id=6)
    multi = fsc.MultiDatastream(id=7, name="m", description="d")
    observation = fsc.Observation(result=4, result_time="2020-01-01T00:00:00Z")
    value = fsc.DataArrayValue()
    value.components = [
        fsc.DataArrayValue.Property.PHENOMENON_TIME,
        fsc.DataArrayValue.Property.RESULT,
        fsc.DataArrayValue.Property.RESULT_TIME,
    ]
    value.datastream = stream
    value.add_observation(observation)
    assert value.data_array[0] == [None, 4, "2020-01-01T00:00:00Z"]
    ordered = fsc.DataArrayValue()
    ordered.components = ["result", "phenomenonTime"]
    ordered.multi_datastream = multi
    ordered.add_observation(fsc.Observation(result=1, phenomenon_time="2020-01-01T00:00:00Z"))
    assert ordered.data_array[0] == [1, "2020-01-01T00:00:00Z"]
    body = ordered.to_json(sta)
    assert list(body)[0] == "MultiDatastream"
    assert "Datastream" not in body
    assert body["components"] == ["result", "phenomenonTime"]
    assert body["MultiDatastream"] == {"@iot.id": 7}
    feature_cell = fsc.DataArrayValue()
    feature_cell.components = ["FeatureOfInterest/id", "result"]
    feature_cell.datastream = stream
    feature_cell.add_observation(fsc.Observation(result=3))
    assert feature_cell.data_array[0] == [None, 3]
    with pytest.raises(TypeError, match="components must be a list"):
        value.components = {fsc.DataArrayValue.Property.RESULT}
    value.multi_datastream = multi
    with pytest.raises(ValueError, match="exactly one"):
        value.to_json(sta)
    document = fsc.DataArrayDocument()
    with pytest.raises(TypeError, match="not an entity"):
        sta.create(document)
    silent = service(extensions=(True, False))
    with pytest.raises(RuntimeError, match="CreateObservations"):
        silent.invoke("CreateObservations", document.to_json(silent))
    ordered.datastream = None
    document.add_data_array_value(ordered)
    live = RecordingService(
        V11,
        [Response(["http://example.org/FROST-Server/v1.1/Observations(10)"])],
        metadata=SimpleNamespace(actions={"CreateObservations"}, functions=set()),
    )
    payload = live.invoke("CreateObservations", document.to_json(live))
    created = document.observations_from(payload, fsc.Observation, live)
    assert live.calls[0][0] == "post"
    assert live.calls[0][1].endswith("/CreateObservations")
    assert created[0].id == 10
    assert created[0].self_link.endswith("/Observations(10)")
    odata = service(ODATA, control="@odata")
    assert ordered.to_json(odata)["MultiDatastream"]["@odata.id"].endswith("/MultiDatastreams(7)")


def test_open_type_keeps_unknown_fields_and_closed_type_drops_them():
    class OpenBox(Entity):
        __csdl_name__ = "OpenBox"
        __namespace__ = "test.open"
        __entity_set__ = "OpenBoxes"
        __key_name__ = "id"
        __key_type__ = "Edm.Int64"
        __open_type__ = True
        __is_entity__ = True
        __properties__ = (PropertySpec("name", "name", "Edm.String", nullable=True),)
        __navigations__ = ()

    box = OpenBox.from_json({"name": "a", "owner": "iosb"})
    assert box.to_json(service())["owner"] == "iosb"
    thing = fsc.Thing.from_json({"name": "a", "description": "d", "owner": "iosb"})
    assert "owner" not in thing.to_json(service())


def test_server_compose_pins_2_8_2_and_leaves_multidatastream_enabled():
    text = (ROOT / "frost_server" / "docker-compose.yaml").read_text(encoding="utf-8")
    assert "fraunhoferiosb/frost-server:2.8.2" in text
    assert ":latest" not in text
    assert "plugins_odata.enable=true" in text
    assert "multiDatastream.enable=false" not in text
    assert "plugins_multiDatastream.enable=false" not in text
