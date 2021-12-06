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

from abc import ABC
from frost_sta_client.service.sensorthingsservice import SensorThingsService


class Entity(ABC):
    """
    An abstract representation of an entity.
    """
    def __init__(self,
                 id=None,
                 self_link='',
                 service=None):
        self.id = id
        self.self_link = self_link
        self.service = service

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        if value is None:
            self._id = None
            return
        if isinstance(value, int) or isinstance(value, str):
            self._id = value
            return
        raise ValueError('id of entity should be of type int!')

    @property
    def self_link(self):
        return self._self_link

    @self_link.setter
    def self_link(self, value):
        if not isinstance(value, str):
            raise ValueError('self_link should be of type str!')
        self._self_link = value

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value):
        if value is None or isinstance(value, SensorThingsService):
            self._service = value
            return
        raise ValueError('service should be of type SensorThingsService')

    def set_service(self, service):
        if self.service != service:
            self.service = service
            self.ensure_service_on_children(service)

    @property
    def IOT_COUNT(self):
        return 'iot.count'

    @property
    def AT_IOT_COUNT(self):
        return '@iot.count'

    @property
    def IOT_NAVIGATION_LINK(self):
        return 'iot.navigationLink'

    @property
    def AT_IOT_NAVIGATION_LINK(self):
        return '@iot.navigationLink'

    @property
    def IOT_NEXT_LINK(self):
        return 'iot.nextLink'

    @property
    def AT_IOT_NEXT_LINK(self):
        return '@iot.nextLink'

    @property
    def IOT_SELF_LINK(self):
        return 'iot.selfLink'

    @property
    def AT_IOT_SELF_LINK(self):
        return '@iot.selfLink'

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.id != other.id:
            return False
        if self.self_link != other.self_link:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = {}
        if self.id is not None and self.id != '':
            data['@iot.id'] = self.id
        return data

    def __setstate__(self, state):
        self.id = state.get('@iot.id', None)
        self.self_link = state.get('@iot.selfLink', '')
