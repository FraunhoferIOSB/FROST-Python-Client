"""Built-in combinations, conformance, and the OData model check."""

import itertools
from pathlib import Path

import pytest

import frost_sta_client as fsc
from frost_sta_client.runtime.builtin import (
    ACTUATION_CONFORMANCE,
    DATA_ARRAY_CONFORMANCE,
    MULTIDATASTREAM_CONFORMANCE,
)
from frost_sta_client.runtime.csdl import parse_csdl
from frost_sta_client.runtime.modelcheck import assert_same_model, differences, signature
from frost_sta_client.runtime.service import SensorThingsService
from tests.test_rules import RecordingService, Response

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "frost_sta_client" / "metadata" / "frost-2.8.2-odata-4.01.csdl.xml"
ACTUATION_METADATA = (
    ROOT / "frost_sta_client" / "metadata" / "frost-2.8.2-odata-4.01-actuation.csdl.xml"
)
ODATA = "http://example.org/FROST-Server/ODATA_4.01"
STA = "http://example.org/FROST-Server/v1.1"


def _conformance(multi_datastream, data_array, actuation):
    values = []
    if multi_datastream:
        values.append(MULTIDATASTREAM_CONFORMANCE)
    if data_array:
        values.append(DATA_ARRAY_CONFORMANCE)
    if actuation:
        values.append(ACTUATION_CONFORMANCE)
    return {
        "value": [{"name": "Things", "url": STA + "/Things"}],
        "serverSettings": {"conformance": values},
    }


def _odata_root():
    return Response(
        {"@odata.context": ODATA + "/$metadata", "value": []},
        headers={"OData-Version": "4.01"},
    )


def _has(service, name):
    return callable(getattr(service, name, None))


def test_default_is_the_frost_2_8_2_image_default():
    service = SensorThingsService(STA, control="@iot")
    assert service.extensions == (False, True, False)
    assert fsc.Actuator.__csdl_name__ == "Actuator"
    assert not _has(service, "multi_datastreams")
    assert not _has(service, "actuators")
    assert not _has(service, "tasks")
    assert not _has(service, "tasking_capabilities")
    assert _has(service, "create_observations")
    assert _has(service, "things")


def test_second_argument_selects_the_builtin_combination():
    data_array_only = SensorThingsService(STA, (False, True, False), control="@iot")
    assert _has(data_array_only, "create_observations")
    assert not _has(data_array_only, "actuators")
    neither = SensorThingsService(STA, (False, False, False), control="@iot")
    assert not _has(neither, "create_observations")
    assert not _has(neither, "multi_datastreams")
    assert not _has(neither, "actuators")
    actuation = SensorThingsService(STA, "", (False, False, True), control="@iot")
    assert _has(actuation, "actuators")
    assert _has(actuation, "tasks")
    assert _has(actuation, "tasking_capabilities")
    assert not _has(actuation, "create_observations")
    with pytest.raises(ValueError, match="extensions"):
        SensorThingsService(STA, (True, True), control="@iot")


def test_eight_combinations_follow_sensorthings_conformance():
    flags = (False, True)
    for multi_datastream, data_array, actuation in itertools.product(flags, flags, flags):
        service = RecordingService(
            STA,
            [
                Response(_conformance(multi_datastream, data_array, actuation)),
                Response({"value": []}),
            ],
            control=None,
            extensions=(multi_datastream, data_array, actuation),
        )
        assert service.things().query().list().entities == []
        assert service.calls[0][1] == STA
        assert not any(call[1].endswith("/$metadata") for call in service.calls)
        assert _has(service, "multi_datastreams") is multi_datastream
        assert _has(service, "create_observations") is data_array
        assert _has(service, "actuators") is actuation
        assert _has(service, "tasks") is actuation
        assert _has(service, "tasking_capabilities") is actuation
        assert service.write_prefix == "@iot"
        assert len([call for call in service.calls if call[1] == STA]) == 1


def test_sensorthings_conformance_mismatch_raises():
    service = RecordingService(
        STA,
        [Response(_conformance(False, True, False))],
        control=None,
        extensions=(False, True, True),
    )
    with pytest.raises(RuntimeError, match="Actuator"):
        service.things().query().list()
    assert not any(call[1].endswith("/$metadata") for call in service.calls)


def test_default_matches_data_array_conformance_only():
    service = RecordingService(
        STA,
        [Response(_conformance(False, True, False)), Response({"value": []})],
        control=None,
    )
    assert service.things().query().list().entities == []
    assert service.extensions == (False, True, False)


def test_multidatastream_builtin_matches_frost_2_8_2_odata_metadata():
    parsed = parse_csdl(METADATA.read_text(encoding="utf-8"))
    loaded = SensorThingsService(ODATA, extensions=(True, False, False), control="@odata").model
    both = SensorThingsService(ODATA, extensions=(True, True, False), control="@odata").model
    actuated = parse_csdl(ACTUATION_METADATA.read_text(encoding="utf-8"))
    with_actuation = SensorThingsService(ODATA, extensions=(True, False, True), control="@odata").model
    assert differences(signature(loaded), signature(parsed)) == []
    assert_same_model(loaded, parsed, ODATA + " $metadata")
    assert differences(signature(with_actuation), signature(actuated)) == []
    with pytest.raises(RuntimeError, match="CreateObservations"):
        assert_same_model(both, parsed, ODATA + " $metadata")


def test_default_model_mismatches_odata_metadata_and_dialect_is_cached():
    xml = METADATA.read_text(encoding="utf-8")
    matched = RecordingService(
        ODATA,
        [_odata_root(), Response({"value": []})],
        metadata=xml,
        control=None,
        extensions=(True, False, False),
    )
    assert matched.things().query().list().entities == []
    assert matched.write_prefix == "@"
    assert matched.calls[0][1] == ODATA
    assert not any(call[1].endswith("/$metadata") for call in matched.calls)
    again = matched.write_prefix
    assert again == "@"
    assert len([call for call in matched.calls if call[1] == ODATA]) == 1

    mismatch = RecordingService(
        ODATA,
        [_odata_root()],
        metadata=xml,
        control=None,
        extensions=(True, True, False),
    )
    with pytest.raises(RuntimeError, match="CreateObservations"):
        mismatch.things().query().list()


def test_references_follow_the_dialect():
    sta = SensorThingsService(STA, control="@iot")
    thing = fsc.Thing(id=5, name="A", description="B", locations=[
        fsc.Location(
            id=8,
            name="here",
            description="there",
            encoding_type="application/geo+json",
            location={"type": "Point", "coordinates": [1, 2]},
        ),
    ])
    body = thing.to_json(sta)
    assert body["@iot.id"] == 5
    assert body["@iot.selfLink"].endswith("/Things(5)")
    assert body["Locations"] == [{"@iot.id": 8}]
    odata = SensorThingsService(ODATA, control="@")
    assert thing.to_json(odata)["@id"].endswith("/Things(5)")
    assert thing.to_json(odata)["Locations"] == [{"@id": ODATA + "/Locations(8)"}]
