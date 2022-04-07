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

import frost_sta_client.model.tasking_capability
from . import entity
from . import tasking_capability

from frost_sta_client.dao.task import TaskDao

from frost_sta_client import utils


class Task(entity.Entity):
    def __init__(self,
                 tasking_parameters=None,
                 creation_time=None,
                 tasking_capability=None,
                 **kwargs):
        super().__init__(**kwargs)
        if tasking_parameters is None:
            tasking_parameters = {}
        self.tasking_parameters = tasking_parameters
        self.creation_time = creation_time
        self.tasking_capability = tasking_capability

    def __new__(cls, *args, **kwargs):
        new_task = super().__new__(cls)
        attributes = {'_id': None, '_tasking_parameters': {}, '_creation_time': None, '_tasking_capability': None,
                      '_self_link': '', '_service': None}
        for key, value in attributes.items():
            new_task.__dict__[key] = value
        return new_task

    @property
    def tasking_parameters(self):
        return self._tasking_parameters

    @tasking_parameters.setter
    def tasking_parameters(self, value):
        if value is None or not isinstance(value, dict):
            raise ValueError('tasking parameter should be of type dict!')
        self._tasking_parameters = value

    @property
    def creation_time(self):
        return self._creation_time

    @creation_time.setter
    def creation_time(self, value):
        self._creation_time = utils.check_datetime(value, 'creation_time')

    @property
    def tasking_capability(self):
        return self._tasking_capability

    @tasking_capability.setter
    def tasking_capability(self, value):
        if value is None:
            self._tasking_capability = None
            return
        if not isinstance(value, tasking_capability.TaskingCapability):
            raise ValueError('tasking capability should be of type TaskingCapability!')
        self._tasking_capability = value

    def ensure_service_on_children(self, service):
        if self.tasking_capability is not None:
            self.tasking_capability.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.tasking_parameters != other.tasking_parameters:
            return False
        if self.creation_time != other.creation_time:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        if data.get('@iot.id', None) is not None:
            return data
        if self.tasking_parameters is not None and self.tasking_parameters != {}:
            data['taskingParameters'] = self.tasking_parameters
        if self.creation_time is not None:
            data['creationTime'] = utils.parse_datetime(self.creation_time)
        if self.tasking_capability is not None:
            data['TaskingCapability'] = self.tasking_capability
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.tasking_parameters = state.get('taskingParameters', {})
        self.creation_time = state.get('creationTime', None)
        if state.get('taskingCapability', None) is not None:
            self.tasking_capability = frost_sta_client.model.tasking_capability.TaskingCapability()
            self.tasking_capability.__setstate__(state['taskingCapability'])

    def get_dao(self, service):
        return TaskDao(service)
