# Copyright (C) 2021 Fraunhofer Institut IOSB, Fraunhoferstr. 1, D 76131
# Karlsruhe, Germany.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

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
                 actuator=None,
                 **kwargs):
        super().__init__(**kwargs)
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
        if not isinstance(value, str):
            raise ValueError('name should be of type str!')
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        if not isinstance(value, str):
            raise ValueError('description should be of type str!')
        self._description = value

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, value):
        if not isinstance(value, dict):
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
        if not isinstance(value, dict):
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
        if not isinstance(value, list) and all(isinstance(t, frost_sta_client.model.task.Task) for t in value):
            entity_class = entity_type.EntityTypes['Task']['class']
            self._tasks = entity_list.EntityList(entity_class=entity_class, entities=value)
            return
        if isinstance(value, entity_list.EntityList) \
                and all(isinstance(t, frost_sta_client.model.task.Task) for t in value.entities):
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
        if not isinstance(value, thing.Thing):
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
        if not isinstance(value, actuator.Actuator):
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
        if data.get('@iot.id', None) is not None:
            return data
        if self.name is not None and self.name != '':
            data['name'] = self.name
        if self.description is not None and self.description != '':
            data['description'] = self.description
        if self.tasking_parameters is not None and self.tasking_parameters != {}:
            data['taskingParameters'] = self.tasking_parameters
        if self.properties is not None and self.properties != {}:
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
