import numpy as np
import pytest
from frost_sta_client import utils
from frost_sta_client.model.observation import Observation

def _obs_obj(val):
    return Observation(id=1, result=val)


def test_parse_obs_to_dict_numpy_float64_in_result():
    val = np.float64(0.15)
    data = _obs_obj(val)
    assert isinstance(obs, Observation)
    assert isinstance(obs.result, float)
    assert obs.result == pytest.approx(0.15)


def test_parse_obs_to_dict_numpy_float32_in_result():
    val = np.float32(1.25)
    data = _obs_obj(val)
    assert isinstance(obs, Observation)
    assert isinstance(obs.result, float)
    assert obs.result == pytest.approx(1.25)


def test_parse_obs_to_dict_numpy_int_in_result():
    val = np.int64(5)
    data = _obs_obj(val)
    assert isinstance(obs, Observation)
    assert isinstance(obs.result, int)
    assert obs.result == 5


def test_parse_obs_to_dict_numpy_float_dict_float64_in_result():
    val = {'v': np.float64(2.5)}
    data = _obs_obj(val)
    assert isinstance(obs, Observation)
    assert isinstance(obs.result, dict)
    assert isinstance(obs.result['v'], float)
    assert obs.result['v'] == pytest.approx(2.5)


def test_parse_obs_to_dict_numpy_array_float64_in_result():
    val = np.array([np.float64(0.15), np.float64(-1.457e5)])
    data = _obs_obj(val)
    assert isinstance(obs, Observation)
    assert isinstance(obs.result, list)
    assert obs.result == pytest.approx([0.15, -1.457e5])
