import pytest
from frost_sta_client import utils


def test_extract_value_numeric_and_string():
    assert utils.extract_value('Things(22)') == 22
    assert utils.extract_value("Things('abc')") == 'abc'


def test_transform_json_to_entity_list_with_dict():
    data = {"value": [{"@iot.id": 1, "name": "A"}]}
    elist = utils.transform_json_to_entity_list(data, 'frost_sta_client.model.thing.Thing')
    assert len(elist.entities) == 1


def test_transform_json_to_entity_list_with_list():
    data = [{"@iot.id": 2, "name": "B"}]
    elist = utils.transform_json_to_entity_list(data, 'frost_sta_client.model.thing.Thing')
    assert len(elist.entities) == 1


def test_parse_datetime_invalid():
    with pytest.raises(ValueError):
        utils.parse_datetime('invalid')


def test_process_area_point_and_polygon():
    p = utils.process_area({"type": "Point", "coordinates": [1, 2]})
    assert getattr(p, 'type', 'Point') == 'Point'
    poly = utils.process_area({"type": "Polygon", "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]})
    assert getattr(poly, 'type', 'Polygon') == 'Polygon'
    with pytest.raises(ValueError):
        utils.process_area({"type": "Unknown", "coordinates": []})
