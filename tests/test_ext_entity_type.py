from frost_sta_client.model.ext.entity_type import get_list_for_class
from frost_sta_client.model.thing import Thing


def test_get_list_for_class():
    t = Thing()
    assert get_list_for_class(type(t)) == 'Things'
