"""Equivalent SensorThings time encodings compare by value, without mutation."""
import datetime

import pytest

from frost_sta_client.model.observation import Observation

UTC = datetime.timezone.utc
INSTANT = datetime.datetime(2024, 4, 17, 12, tzinfo=UTC)


@pytest.mark.parametrize("field", ["phenomenon_time", "result_time", "valid_time"])
@pytest.mark.parametrize("left,right", [
    ("2024-04-17T12:00:00Z", "2024-04-17T12:00:00.000+00:00"),
    ("2024-04-17T12:00:00Z", "2024-04-17T14:00:00+02:00"),
    ("2024-04-17T12:00:00Z", INSTANT),
    ("2024-04-17T12:00:00.123Z", "2024-04-17T12:00:00.123000+00:00"),
    ("2024-04-17T12:00:00Z/2024-04-17T13:00:00Z",
     "2024-04-17T14:00:00+02:00/2024-04-17T15:00:00+02:00"),
    ("2024-04-17T12:00:00Z/2024-04-17T13:00:00Z",
     [INSTANT, INSTANT + datetime.timedelta(hours=1)]),
])
def test_equivalent_time_encodings(field, left, right):
    first = Observation(result=10, **{field: left})
    second = Observation(result=10, **{field: right})
    assert first == second
    assert second == first
    assert not (first != second)
    assert getattr(first, field) is left
    assert getattr(second, field) is right


@pytest.mark.parametrize("field", ["phenomenon_time", "result_time", "valid_time"])
@pytest.mark.parametrize("other", [
    None,
    "2024-04-17T12:00:01Z",
    "2024-04-17T12:00:00.000001Z",
    "2024-04-17T12:00:00",
    "2024-04-17T12:00:00Z/2024-04-17T13:00:00Z",
])
def test_different_times_stay_unequal(field, other):
    first = Observation(result=10, **{field: "2024-04-17T12:00:00Z"})
    second = Observation(result=10, **{field: other})
    assert first != second
    assert second != first


def test_other_observation_fields_still_participate():
    first = Observation(result=10, phenomenon_time="2024-04-17T12:00:00Z")
    second = Observation(result=11, phenomenon_time="2024-04-17T12:00:00.000+00:00")
    assert first != second
    assert first.__eq__(None) is False
    assert first != object()
    assert Observation() == Observation()
