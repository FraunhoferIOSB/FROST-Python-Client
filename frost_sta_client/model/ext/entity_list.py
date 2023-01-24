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

import logging
import requests
import frost_sta_client


class EntityList:
    def __init__(self, entity_class, entities=None):
        if entities is None:
            entities = []
        self.entities = entities
        self.entity_class = entity_class
        self.next_link = None
        self.service = None
        self.iterable_entities = None
        self.count = None
        self.callback = None
        self.step_size = None

    def __new__(cls, *args, **kwargs):
        new_entity_list = super().__new__(cls)
        attributes = {'_entities': None, '_entity_class': '', '_next_link': '', '_service': {}, '_count': '',
                      '_iterable_entities': None, '_callback': None,
                      '_step_size': None}
        for key, value in attributes.items():
            new_entity_list.__dict__[key] = value
        return new_entity_list

    def __iter__(self):
        self.iterable_entities = iter(enumerate(self.entities))
        return self

    def __next__(self):
        idx, next_entity = next(self.iterable_entities, (len(self.entities), None))
        if self.step_size is not None and idx is not None and idx % self.step_size == 0:
            self.callback(idx)
        if next_entity is not None:
            return next_entity
        if self.next_link is not None:
            try:
                response = self.service.execute('get', self.next_link)
            except requests.exceptions.HTTPError as e:
                error_json = e.response.json()
                error_message = error_json['message']
                logging.error("Query failed with status-code {}, {}".format(e.response.status_code, error_message))
                raise e
            logging.debug('Received response: {} from {}'.format(response.status_code, self.next_link))
            try:
                json_response = response.json()
            except ValueError:
                raise ValueError('Cannot find json in http response')

            result_list = frost_sta_client.utils.transform_json_to_entity_list(json_response, self.entity_class)
            self.entities += result_list.entities
            self.set_service(self.service)
            self.next_link = json_response.get("@iot.nextLink", None)
            self.iterable_entities = iter(enumerate(self.entities[-len(result_list.entities):], start=idx))
            return next(self.iterable_entities)[1]
        raise StopIteration

    def get(self, index):
        if not isinstance(index, int):
            raise IndexError('index must be an integer')
        if index >= len(self.entities):
            raise IndexError('index exceeds total number of entities')
        if index < 0:
            raise IndexError('negative indices cannot be accessed')
        return self.entities[index]

    @property
    def entity_class(self):
        return self._entity_class

    @entity_class.setter
    def entity_class(self, value):
        if isinstance(value, str):
            self._entity_class = value
            return
        raise ValueError('entity_class should be of type str')

    @property
    def entities(self):
        return self._entities

    @entities.setter
    def entities(self, values):
        if isinstance(values, list) and all(isinstance(v, frost_sta_client.model.entity.Entity) for v in values):
            self._entities = values
            return
        raise ValueError('entities should be a list of entities')

    @property
    def callback(self):
        return self._callback

    @callback.setter
    def callback(self, callback):
        if callable(callback) or callback is None:
            self._callback = callback

    @property
    def step_size(self):
        return self._step_size

    @step_size.setter
    def step_size(self, value):
        if isinstance(value, int) or value is None:
            self._step_size = value
            return
        raise ValueError('step_size should be of type int')

    @property
    def next_link(self):
        return self._next_link

    @next_link.setter
    def next_link(self, value):
        if value is None or isinstance(value, str):
            self._next_link = value
            return
        raise ValueError('next_link should be of type string')

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value):
        if value is None or isinstance(value, frost_sta_client.service.sensorthingsservice.SensorThingsService):
            self._service = value
            return
        raise ValueError('service should be of type SensorThingsService')

    def set_service(self, service):
        self.service = service
        for entity in self.entities:
            entity.set_service(service)

    def __getstate__(self):
        data = []
        for entity in self.entities:
            data.append(entity.__getstate__())
        return data

    def __setstate__(self, state):
        self._next_link = state.get(self.entities + '@nextLink')
        pass
