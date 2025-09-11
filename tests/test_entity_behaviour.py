from frost_sta_client.service.sensorthingsservice import SensorThingsService
from frost_sta_client.model.thing import Thing
from frost_sta_client.model.location import Location
from frost_sta_client.model.ext.entity_list import EntityList
from frost_sta_client.model.ext.entity_type import EntityTypes


def test_entity_equality_by_id():
    a = Thing(id=1, name='A')
    b = Thing(id=1, name='B')
    assert a != b


def test_set_service_propagates_to_children():
    t = Thing(name='T')
    loc = Location(name='L')
    t.locations = EntityList(entity_class=EntityTypes['Location']['class'], entities=[loc])
    svc = SensorThingsService('http://example.org/FROST-Server/v1.1')
    t.set_service(svc)
    assert t.service is svc
    assert t.locations.entities[0].service is svc
