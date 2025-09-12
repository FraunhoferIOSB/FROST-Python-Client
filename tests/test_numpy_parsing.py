import numpy as np
import pytest
from frost_sta_client import utils
from frost_sta_client.model.observation import Observation


def _obs_json(val):
    return {'@iot.id': 1, 'result': val}


def test_parse_numpy_float64_in_result():
    data = _obs_json(np.float64(0.15))
    obs = utils.transform_json_to_entity(data, 'frost_sta_client.model.observation.Observation')
    assert isinstance(obs, Observation)
    assert isinstance(obs.result, float)
    assert obs.result == pytest.approx(0.15)


def test_parse_numpy_float32_in_result():
    data = _obs_json(np.float32(1.25))
    obs = utils.transform_json_to_entity(data, 'frost_sta_client.model.observation.Observation')
    assert isinstance(obs.result, float)
    assert obs.result == pytest.approx(1.25)


def test_parse_numpy_int_in_result():
    data = _obs_json(np.int64(5))
    obs = utils.transform_json_to_entity(data, 'frost_sta_client.model.observation.Observation')
    # accepted and converted to Python-int
    assert isinstance(obs.result, int)
    assert obs.result == 5


def test_parse_numpy_float_inside_nested_result_dict():
    data = _obs_json({'v': np.float64(2.5)})
    obs = utils.transform_json_to_entity(data, 'frost_sta_client.model.observation.Observation')
    # nested numpy.float shall be accepted and converted to float
    assert isinstance(obs.result, dict)
    assert isinstance(obs.result['v'], float)
    assert obs.result['v'] == pytest.approx(2.5)
