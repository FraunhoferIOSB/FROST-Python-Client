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
from .data_array_value import DataArrayValue


class DataArrayDocument:
    def __init__(self, count=-1, next_link = None, value = []):
        self._count = count
        self._next_link = next_link
        self._value = value

    @property
    def count(self):
        return self._count

    @count.setter
    def count(self, value):
        if type(value) == int or value is None:
            self._count = value
        else:
            raise TypeError('count should be of type int')

    @property
    def next_link(self):
        return self._next_link

    @next_link.setter
    def next_link(self, value):
        if type(value) == str or value is None:
            self._next_link = value
        else:
            raise TypeError('nextLink should be of type str')

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if type(value) == list and all(isinstance(x, DataArrayValue) for x in value):
            self._value = value
        else:
            raise TypeError('value should be a list of type DataArrayValue')

    def get_observations(self):
        obs_list = []
        for dav in self.value:
            obs_list.concat(dav.get_observations())
        return obs_list

    def add_data_array_value(self, dav):
        self.value.append(dav)

