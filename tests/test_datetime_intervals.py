import datetime

import pytest

from frost_sta_client.model.observation import Observation
from frost_sta_client.utils import parse_datetime


@pytest.mark.parametrize('offset', [None, datetime.timezone.utc, datetime.timezone(datetime.timedelta(hours=2))])
def test_datetime_list_matches_string_interval(offset):
    start = datetime.datetime(2024, 4, 17, 12, tzinfo=offset)
    end = start + datetime.timedelta(hours=1)
    interval = f'{start.isoformat()}/{end.isoformat()}'

    assert parse_datetime([start, end]) == parse_datetime(interval)


@pytest.mark.parametrize('length', [0, 1, 3])
def test_datetime_list_requires_two_endpoints(length):
    values = [datetime.datetime(2024, 4, 17, 12)] * length

    with pytest.raises(ValueError, match='two datetimes'):
        parse_datetime(values)


@pytest.mark.parametrize('attribute, key', [('phenomenon_time', 'phenomenonTime'), ('valid_time', 'validTime')])
def test_observation_serializes_datetime_interval(attribute, key):
    start = datetime.datetime(2024, 4, 17, 12, tzinfo=datetime.timezone.utc)
    end = start + datetime.timedelta(hours=1)
    observation = Observation(result=42, **{attribute: [start, end]})

    assert observation.__getstate__()[key] == '2024-04-17T12:00:00+00:00/2024-04-17T13:00:00+00:00'


def test_datetime_list_rejects_non_datetime_endpoint():
    with pytest.raises(ValueError, match='two datetimes'):
        parse_datetime([datetime.datetime(2024, 4, 17, 12), '2024-04-17T13:00:00Z'])
