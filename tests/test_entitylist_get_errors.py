import pytest
from frost_sta_client.model.thing import Thing
from frost_sta_client.model.ext.entity_list import EntityList

def test_entity_list_get_index_errors():
    el = EntityList(entity_class='frost_sta_client.model.thing.Thing', entities=[Thing(id=1, name='A')])
    assert el.get(0).id == 1
    with pytest.raises(IndexError):
        el.get(-1)
    with pytest.raises(IndexError):
        el.get(5)
    with pytest.raises(IndexError):
        el.get('x')
