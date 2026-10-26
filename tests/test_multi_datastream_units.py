# SPDX-FileCopyrightText: 2026 Umut Alisoglu
# SPDX-License-Identifier: LGPL-3.0-or-later

import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from frost_sta_client import MultiDatastream, SensorThingsService, UnitOfMeasurement, utils


@pytest.fixture
def units():
    return [
        UnitOfMeasurement(name='Celsius', symbol='°C', definition='temperature'),
        UnitOfMeasurement(name='Percent', symbol='%', definition='relative humidity'),
    ]


@pytest.fixture
def unit_payload():
    return [
        {'name': 'Celsius', 'symbol': '°C', 'definition': 'temperature'},
        {'name': 'Percent', 'symbol': '%', 'definition': 'relative humidity'},
    ]


@pytest.mark.parametrize('count', [1, 2])
def test_serialize_measurement_units(units, unit_payload, count):
    stream = MultiDatastream(name='Weather', unit_of_measurements=units[:count])

    payload = utils.transform_entity_to_json_dict(stream)

    assert payload['unitOfMeasurements'] == unit_payload[:count]
    assert json.loads(json.dumps(payload))['unitOfMeasurements'] == unit_payload[:count]


def test_deserialize_measurement_units_and_round_trip(units, unit_payload):
    payload = {
        'name': 'Weather',
        'observationType': 'http://www.opengis.net/def/observationType/OGC-OM/2.0/OM_ComplexObservation',
        'unitOfMeasurements': unit_payload,
        'multiObservationDataTypes': ['temperature', 'humidity'],
    }

    stream = utils.transform_json_to_entity(
        payload, 'frost_sta_client.model.multi_datastream.MultiDatastream'
    )

    assert all(isinstance(unit, UnitOfMeasurement) for unit in stream.unit_of_measurements)
    assert stream.unit_of_measurements == units
    assert utils.transform_entity_to_json_dict(stream) == payload


@pytest.mark.parametrize('unit_values', [None, []])
def test_empty_measurement_units_remain_omitted(unit_values):
    stream = MultiDatastream(unit_of_measurements=unit_values)

    assert 'unitOfMeasurements' not in utils.transform_entity_to_json_dict(stream)


def test_create_sends_measurement_units(monkeypatch, units, unit_payload):
    service = SensorThingsService('https://example.invalid/v1.1')
    execute = Mock(return_value=SimpleNamespace(
        status_code=201, headers={'location': 'MultiDatastreams(42)'}
    ))
    monkeypatch.setattr(service, 'execute', execute)
    stream = MultiDatastream(name='Weather', unit_of_measurements=units)

    service.create(stream)

    execute.assert_called_once()
    method, url = execute.call_args.args
    assert method == 'post'
    assert str(url) == 'https://example.invalid/v1.1/MultiDatastreams'
    assert execute.call_args.kwargs['json']['unitOfMeasurements'] == unit_payload
    assert stream.id == 42
    assert stream.service is service
