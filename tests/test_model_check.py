"""Built-in combinations, conformance, and the OData model check."""

from pathlib import Path

import pytest

import frost_sta_client as fsc
from frost_sta_client.runtime.builtin import (
    DATA_ARRAY_CONFORMANCE,
    MULTIDATASTREAM_CONFORMANCE,
)
from frost_sta_client.runtime.csdl import parse_csdl
from frost_sta_client.runtime.modelcheck import assert_same_model, differences, signature
from frost_sta_client.runtime.service import SensorThingsService
from tests.test_rules import RecordingService, Response

ROOT = Path(__file__).resolve().parents[1]
METADATA = ROOT / "frost_sta_client" / "metadata" / "frost-2.8.2-odata-4.01.csdl.xml"
ODATA = "http://example.org/FROST-Server/ODATA_4.01"
STA = "http://example.org/FROST-Server/v1.1"


def _conformance(multi_datastream, data_array):
    values = []
    if multi_datastream:
        values.append(MULTIDATASTREAM_CONFORMANCE)
    if data_array:
        values.append(DATA_ARRAY_CONFORMANCE)
    return {
        "value": [{"name": "Things", "url": STA + "/Things"}],
        "serverSettings": {"conformance": values},
    }


def _odata_root():
    return Response(
        {"@odata.context": ODATA + "/$metadata", "value": []},
        headers={"OData-Version": "4.01"},
    )


def test_second_argument_selects_the_builtin_combination():
    both = SensorThingsService(STA, control="@iot")
    assert callable(both.create_observations)
    assert callable(both.multi_datastreams)
    neither = SensorThingsService(STA, (False, False), control="@iot")
    assert getattr(neither, "create_observations", None) is None
    assert getattr(neither, "multi_datastreams", None) is None
    data_array_only = SensorThingsService(STA, "", (False, True), control="@iot")
    assert callable(data_array_only.create_observations)
    assert getattr(data_array_only, "multi_datastreams", None) is None
    with pytest.raises(ValueError, match="extensions"):
        SensorThingsService(STA, (True, "no"), control="@iot")


def test_four_combinations_follow_sensorthings_conformance():
    for multi_datastream, data_array in ((True, True), (True, False), (False, True), (False, False)):
        service = RecordingService(
            STA,
            [Response(_conformance(multi_datastream, data_array)), Response({"value": []})],
            control=None,
            extensions=(multi_datastream, data_array),
        )
        assert service.things().query().list().entities == []
        assert service.calls[0][1] == STA
        assert not any(call[1].endswith("/$metadata") for call in service.calls)
        assert callable(getattr(service, "multi_datastreams", None)) is multi_datastream
        assert callable(getattr(service, "create_observations", None)) is data_array
        assert service.write_prefix == "@iot"
        assert len([call for call in service.calls if call[1] == STA]) == 1


def test_sensorthings_conformance_mismatch_raises():
    service = RecordingService(
        STA,
        [Response(_conformance(False, True))],
        control=None,
        extensions=(True, True),
    )
    with pytest.raises(RuntimeError, match="MultiDatastream"):
        service.things().query().list()
    assert not any(call[1].endswith("/$metadata") for call in service.calls)


def test_multidatastream_builtin_matches_frost_2_8_2_odata_metadata():
    parsed = parse_csdl(METADATA.read_text(encoding="utf-8"))
    loaded = SensorThingsService(ODATA, extensions=(True, False), control="@odata").model
    both = SensorThingsService(ODATA, extensions=(True, True), control="@odata").model
    assert differences(signature(loaded), signature(parsed)) == []
    assert_same_model(loaded, parsed, ODATA + " $metadata")
    with pytest.raises(RuntimeError, match="CreateObservations"):
        assert_same_model(both, parsed, ODATA + " $metadata")


def test_default_model_mismatches_odata_metadata_and_dialect_is_cached():
    xml = METADATA.read_text(encoding="utf-8")
    matched = RecordingService(
        ODATA,
        [_odata_root(), Response({"value": []})],
        metadata=xml,
        control=None,
        extensions=(True, False),
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
        extensions=(True, True),
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
