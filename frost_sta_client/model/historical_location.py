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

import frost_sta_client.model
from . import entity
from . import location
from . import thing

from frost_sta_client.dao.historical_location import HistoricalLocationDao

from frost_sta_client import utils
from .ext import entity_list
from .ext import entity_type


class HistoricalLocation(entity.Entity):

    def __init__(self,
                 location=None,
                 time=None,
                 thing=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.location = location
        self.time = time
        self.thing = thing

    def __new__(cls, *args, **kwargs):
        new_h_loc = super().__new__(cls)
        attributes = {'_id': None, '_location': None, '_time': None, '_thing': None, '_self_link': None,
                      '_service': None}
        for key, value in attributes.items():
            new_h_loc.__dict__[key] = value
        return new_h_loc

    @property
    def time(self):
        return self._time

    @time.setter
    def time(self, value):
        self._time = utils.check_datetime(value, 'time')

    @property
    def location(self):
        return self._location

    @location.setter
    def location(self, value):
        if value is None or isinstance(value, location.Location):
            self._location = value
            return
        raise ValueError("location should be of type Location!")

    @property
    def thing(self):
        return self._thing

    @thing.setter
    def thing(self, value):
        if value is None or isinstance(value, thing.Thing):
            self._thing = value
            return
        raise ValueError('thing should be of type Thing!')

    def ensure_service_on_children(self, service):
        if self.locations is not None:
            self.locations.set_service(service)
        if self.thing is not None:
            self.thing.set_service(service)

    def __eq__(self, other):
        if other is None:
            return False
        if not isinstance(other, type(self)):
            return False
        if id(self) == id(other):
            return True
        if self.time != other.time:
            return False
        return True

    def __ne__(self, other):
        return not self == other

    def __getstate__(self):
        data = super().__getstate__()
        if data.get('@iot.id', None) is not None:
            return data
        if self.time is not None:
            data['Time'] = utils.parse_datetime(self.time)
        if self.thing is not None:
            data['Thing'] = self.thing
        if self.locations is not None and len(self.locations.entities) > 0:
            data['Locations'] = self.locations.__gestate__()
        return data

    def __setstate__(self, state):
        super().__setstate__(state)
        self.time = state.get("Time", None)
        if state.get("Thing", None) is not None:
            self.thing = frost_sta_client.model.thing.Thing()
            self.thing.__setstate__(state["Thing"])
        if state.get("Location", None) is not None:
            self.thing = frost_sta_client.model.location.Location()
            self.thing.__setstate__(state["Location"])

    def get_dao(self, service):
        return HistoricalLocationDao(service)
