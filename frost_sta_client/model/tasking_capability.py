import frost_sta_client.model.task
from . import entity
from . import thing
from . import actuator

from frost_sta_client import utils
from .ext import entity_type
from .ext import entity_list

from frost_sta_client.dao.tasking_capability import TaskingCapabilityDao


class TaskingCapability(entity.Entity):

    def __init__(self,
                 name='',
                 description='',
                 properties=None,
                 tasking_parameters=None,
                 tasks=None,
                 thing=None,
                 actuator=None):
        super().__init__()
        if tasking_parameters is None:
            tasking_parameters = {}
        if properties is None:
            properties = {}
        self.name = name
        self.description = description
        self.tasking_parameters = tasking_parameters
        self.properties = properties
        self.tasks = tasks
        self.thing = thing
        self.actuator = actuator

    def __new__(cls, *args, **kwargs):
        new_tc = super().__new__(cls)
        attributes = {'_id': None, '_name': '', '_description': '', '_properties': {}, '_tasking_parameters': {},
                      '_tasks': None, '_thing': None, '_actuator': None, '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_tc.__dict__[key] = value
        return new_tc

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
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if type(value) != dict:
            raise ValueError('properties should be of type dict!')
        self._properties = value

    @property
    def tasking_parameters(self):
        return self._tasking_parameters

    @tasking_parameters.setter
    def tasking_parameters(self, value):
        if value is None:
            self._tasking_parameters = {}
            return
        if type(value) != dict:
            raise ValueError('Tasking parameters should be of type dict!')
        self._tasking_parameters = value

    @property
    def tasks(self):
        return self._tasks

    @tasks.setter
    def tasks(self, value):
        if value is None:
            self._tasks = None
            return
        if type(value) == entity_list.EntityList and all(isinstance(t, frost_sta_client.model.task.Task) for t in value):
            self._tasks = value
            return
        raise ValueError('tasks should be of type Task!')

    @property
    def thing(self):
        return self._thing

    @thing.setter
    def thing(self, value):
        if value is None:
            self._thing = None
            return
        if type(value) != thing.Thing:
            raise ValueError('thing should be of type Thing!')
        self._thing = value

    @property
    def actuator(self):
        return self._actuator

    @actuator.setter
    def actuator(self, value):
        if value is None:
            self._actuator = None
            return
        if type(value) != actuator.Actuator:
            raise ValueError('actuator should be of type Actuator!')
        self._actuator = value

    def ensure_service_on_children(self, service):
        if self.actuator is not None:
            self.actuator.set_service(service)
        if self.thing is not None:
            self.thing.set_service(service)
        if self.tasks is not None:
            self.thing.set_service(service)

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
        if self.tasking_parameters != other.tasking_parameters:
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
        data['taskingParameters'] = self.tasking_parameters
        data['properties'] = self.properties
        if self.thing is not None:
            data['Thing'] = self.thing
        if self.tasks is not None and len(self.tasks.entities) > 0:
            data['Tasks'] = self.tasks.__getstate__()
        if self.actuator is not None:
            data['Actuator'] = self.actuator
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.name = state.get('name', '')
        self.description = state.get('description', '')
        self.tasking_parameters = state.get('taskingParameters', {})
        self.properties = state.get('properties', {})
        if state.get('Tasks', None) is not None:
            entity_class = entity_type.EntityTypes['Task']['class']
            self.tasks = utils.transform_json_to_entity_list(state['Tasks'], entity_class)
            self.tasks.next_link = state.get('Tasks@iot.nextLink', None)
        if state.get('Actuator', None) is not None:
            self.actuator = frost_sta_client.model.actuator.Actuator()
            self.actuator.__setstate__(state['Actuator'])
        if state.get('Thing', None) is not None:
            self.thing = frost_sta_client.model.thing.Thing()
            self.thing.__setstate__(state['Thing'])

    def get_dao(self, service):
        return TaskingCapabilityDao(service)
