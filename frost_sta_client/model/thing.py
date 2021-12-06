from . import entity
from . import location
from . import datastream
from . import multi_datastream
from . import historical_location
from . import tasking_capability

from frost_sta_client.dao.thing import ThingDao
from frost_sta_client import utils
from .ext import entity_list
from .ext import entity_type


class Thing(entity.Entity):

    def __init__(self,
                 name='',
                 description='',
                 properties=None,
                 locations=None,
                 historical_locations=None,
                 datastreams=None,
                 multi_datastreams=None,
                 tasking_capabilities=None):
        super().__init__()
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.properties = properties
        self.locations = locations
        self.historical_locations = historical_locations
        self.datastreams = datastreams
        self.multi_datastreams = multi_datastreams
        self.tasking_capabilities = tasking_capabilities

    def __new__(cls, *args, **kwargs):
        new_thing = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_locations': None,
                      '_historical_locations': None, '_datastreams': None, '_multi_datastreams': None,
                      '_tasking_capabilities': None, '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_thing.__dict__[key] = value
        return new_thing

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if value is None:
            self._name = None
            return
        if type(value) != str:
            raise ValueError('name should be of type str!')
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if value is None:
            self._description = None
            return
        if type(value) != str:
            raise ValueError('description should be of type str!')
        self._description = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if value is None:
            self._properties = None
            return
        if type(value) != dict:
            raise ValueError('properties should be of type dict!')
        self._properties = value

    @property
    def locations(self):
        return self._locations
    
    @locations.setter
    def locations(self, values):
        if values is None:
            self._locations = None
            return
        if type(values) != entity_list.EntityList or \
                any((not isinstance(loc, location.Location)) for loc in values.entities):
            raise ValueError('locations should be a list of locations')
        self._locations = values

    @property
    def historical_locations(self):
        return self._historical_locations

    @historical_locations.setter
    def historical_locations(self, values):
        if values is None:
            self._historical_locations = None
            return
        if type(values) != entity_list.EntityList or \
                any((not isinstance(loc, historical_location.HistoricalLocation)) for loc in values.entities):
            raise ValueError('historical_locations should be a list of historical locations')
        self._historical_locations = values

    @property
    def datastreams(self):
        return self._datastreams

    @datastreams.setter
    def datastreams(self, values):
        if values is None:
            self._datastreams = None
            return
        if type(values) != entity_list.EntityList or \
                any((not isinstance(ds, datastream.Datastream)) for ds in values.entities):
            raise ValueError('datastreams should be a list of datastreams')
        self._datastreams = values

    @property
    def multi_datastreams(self):
        return self._multi_datastreams

    @multi_datastreams.setter
    def multi_datastreams(self, values):
        if values is None:
            self._multi_datastreams = None
            return
        if type(values) != entity_list.EntityList or \
                any((not isinstance(ds, multi_datastream.MultiDatastream)) for ds in values.entities):
            raise ValueError('Multidatastreams should be a list of MultiDatastreams')
        self._multi_datastreams = values

    @property
    def tasking_capabilities(self):
        return self._tasking_capabilities

    @tasking_capabilities.setter
    def tasking_capabilities(self, values):
        if values is None:
            self._tasking_capabilities = None
            return
        if type(values) != entity_list.EntityList or \
                any((not isinstance(tc, tasking_capability.TaskingCapability)) for tc in values.entities):
            raise ValueError('Tasking capabilities should be a list of TaskingCapabilities')
        self._tasking_capabilities = values

    def ensure_service_on_children(self, service):
        if self.locations is not None:
            self.locations.set_service(service)
        if self.datastreams is not None:
            self.datastreams.set_service(service)
        if self.multi_datastreams is not None:
            self.multi_datastreams.set_service(service)
        if self.tasking_capabilities is not None:
            self.tasking_capabilities.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.name != other.name:
            return False
        if self.description != other.description:
            return False
        if self.properties != other.properties:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        data['name'] = self.name
        data['description'] = self.description
        data['properties'] = self.properties
        if self._locations is not None and len(self.locations.entities) > 0:
            data['Locations'] = self.locations.__getstate__()
        if self._historical_locations is not None and len(self.historical_locations.entities) > 0:
            data['HistoricalLocations'] = self.historical_locations.__getstate__()
        if self._datastreams is not None and len(self.datastreams.entities) > 0:
            data['Datastreams'] = self.datastreams.__getstate__()
        if self._multi_datastreams is not None and len(self.multi_datastreams.entities) > 0:
            data['MultiDatastreams'] = self.multi_datastreams.__getstate__()
        if self._tasking_capabilities is not None and len(self.tasking_capabilities.entities) > 0:
            data['TaskingCapabilities'] = self.tasking_capabilities.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get("name", None)
        self.description = state.get("description", None)
        self.properties = state.get("properties", None)

        if state.get("Locations", None) is not None and type(state["Locations"] == list):
            entity_class = entity_type.EntityTypes['Location']['class']
            self.locations = utils.transform_json_to_entity_list(state['Locations'], entity_class)
            self.locations.next_link = state.get("Locations@iot.nextLink", None)
        if state.get("HistoricalLocations", None) is not None and type(state["HistoricalLocations"] == list):
            entity_class = entity_type.EntityTypes['HistoricalLocation']['class']
            self.historical_locations = utils.transform_json_to_entity_list(state['HistoricalLocations'], entity_class)
            self.historical_locations.next_link = state.get("HistoricalLocations@iot.nextLink", None)
        if state.get("Datastreams", None) is not None and type(state["Datastreams"] == list):
            entity_class = entity_type.EntityTypes['Datastream']['class']
            self.datastreams = utils.transform_json_to_entity_list(state['Datastreams'], entity_class)
            self.datastreams.next_link = state.get("Datastreams@iot.nextLink", None)
        if state.get("MultiDatastreams", None) is not None and type(state["MultiDatastreams"] == list):
            entity_class = entity_type.EntityTypes['MultiDatastream']['class']
            self.multi_datastreams = utils.transform_json_to_entity_list(state['MultiDatastreams'], entity_class)
            self.multi_datastreams.next_link = state.get("MultiDatastreams@iot.nextLink", None)
        if state.get("TaskingCapabilities", None) is not None and type(state["TaskingCapabilities"] == list):
            entity_class = entity_type.EntityTypes['TaskingCapability']['class']
            self.tasking_capabilities = utils.transform_json_to_entity_list(state['TaskingCapabilities'], entity_class)
            self.tasking_capabilities.next_link = state.get("TaskingCapabilities@iot.nextLink", None)

    def get_dao(self, service):
        return ThingDao(service)
