from frost_sta_client.dao.actuator import ActuatorDao

from . import entity
from . import tasking_capability

from .ext import entity_list
from .ext import entity_type
from frost_sta_client import utils


class Actuator(entity.Entity):

    def __init__(self,
                 name='',
                 description='',
                 encoding_type='',
                 tasking_capabilities=None,
                 metadata=None,
                 properties=None,
                 **kwargs):
        super().__init__(**kwargs)
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.encoding_type = encoding_type
        self.tasking_capabilities = tasking_capabilities
        self.metadata = metadata
        self.properties = properties

    def __new__(cls, *args, **kwargs):
        new_actuator = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_encoding_type': '',
                      '_metadata': None, '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_actuator.__dict__[key] = value
        return new_actuator
    
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if type(value) != str:
            raise ValueError('name should be of type str!')
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if type(value) != str:
            raise ValueError('description should be of type str!')
        self._description = value

    @property
    def encoding_type(self):
        return self._encoding_type

    @encoding_type.setter
    def encoding_type(self, value):
        if type(value) != str:
            raise ValueError('encodingtype should be of type str!')
        self._encoding_type = value

    @property
    def metadata(self):
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if value is None:
            self._metadata = None
            return
        if type(value) == dict:
            self._metadata = value
            return
        raise ValueError('metadata should be of type dict!')

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if type(value) != dict:
            raise ValueError('properties should be of type dict!')
        self._properties = value

    @property
    def tasking_capabilities(self):
        return self._tasking_capabilities

    @tasking_capabilities.setter
    def tasking_capabilities(self, values):
        if type(values) != entity_list.EntityList or \
                any((not isinstance(tc, tasking_capability.TaskingCapability)) for tc in values.entities):
            raise ValueError('Tasking capabilities should be a list of TaskingCapabilities')
        self._tasking_capabilities = values

    def ensure_service_on_children(self, service):
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
        if self.encoding_type != other.encoding_type:
            return False
        if self.metadata != other.metadata:
            return False
        if self.properties != other.properties:
            return False

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        data['name'] = self.name
        data['description'] = self.description
        data['encodingType'] = self.encoding_type
        data['metadata'] = self.metadata
        data['properties'] = self.properties
        if self.tasking_capabilities is not None and len(self.tasking_capabilities.entities) > 0:
            data['taskingCapabilities'] = self.tasking_capabilities.__getstate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get("name", None)
        self.description = state.get("description", None)
        self.encoding_type = state.get("encodingType", None)
        self.metadata = state.get("metadata", None)
        self.properties = state.get("properties", None)
        if state.get("TaskingCapabilities", None) is not None and type(state["TaskingCapabilities"] == list):
            entity_class = entity_type.EntityTypes['TaskingCapability']['class']
            self.tasking_capabilities = utils.transform_json_to_entity_list(state['TaskingCapabilities'], entity_class)
            self.tasking_capabilities.next_link = state.get("TaskingCapabilities@iot.nextLink", None)

    def get_dao(self, service):
        return ActuatorDao(service)
