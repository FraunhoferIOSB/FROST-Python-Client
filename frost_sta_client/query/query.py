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

import frost_sta_client.utils
import frost_sta_client.model.ext.entity_list

from furl import furl
import logging
import json
import requests


class Query:
    def __init__(self, service, entity, entitytype_plural, entity_class):
        self.service = service
        self.entity = entity
        self.entitytype_plural = entitytype_plural
        self.entity_class = entity_class
        self.params = {}

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, service):
        if service is None:
            self._service = service
            return
        if not isinstance(service, frost_sta_client.service.sensorthingsservice.SensorThingsService):
            raise ValueError('service should be of type SensorThingsService')
        self._service = service

    @property
    def entity(self):
        return self._entity

    @entity.setter
    def entity(self, value):
        if value is None or isinstance(value, str):
            self._entity = value
            return
        raise ValueError('entity should be of type String')

    @property
    def entitytype_plural(self):
        return self._entitytype_plural

    @entitytype_plural.setter
    def entitytype_plural(self, value):
        if value is None or isinstance(value, str):
            self._entitytype_plural = value
            return
        raise ValueError('entitytype_plural should be of type String')

    @property
    def entity_class(self):
        return self._entity_class

    @entity_class.setter
    def entity_class(self, value):
        if value is None or isinstance(value, str):
            self._entity_class = value
            return
        raise ValueError('entity_class should be of type string')

    def remove_all_params(self, key):
        self.params.pop(key, None)

    def count(self):
        self.remove_all_params('$count')
        self.params['$count'] = 'true'
        return self

    def top(self, num):
        self.remove_all_params('$top')
        self.params['$top'] = num
        return self

    def skip(self, num):
        self.remove_all_params('$skip')
        self.params['$skip'] = num
        return self

    def select(self, *args):
        self.remove_all_params('$select')
        if args is None:
            return self
        values = ''
        for item in args:
            if not isinstance(item, str):
                return self
            values = values + item + ','
        values = values[:-1]
        self.params['$select'] = values
        return self

    def filter(self, statement=None):
        self.remove_all_params('$filter')
        if statement is None:
            return self
        self.params['$filter'] = statement
        return self

    def orderby(self, criteria, order='DESC'):
        self.remove_all_params('$orderby')
        self.params['$orderby'] = criteria + ' ' + order
        return self

    def expand(self, expansion):
        self.remove_all_params('$expand')
        self.params['$expand'] = expansion
        return self

    # exception: similar functions in basedao
    def list(self):
        """
        Get an entity collection as a dictionary
        """
        url = furl(self.service.url)
        url.path.add(self.entitytype_plural)
        url.args = self.params
        try:
            response = self.service.execute('get', url)
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json['message']
            logging.error("Query failed with status-code {}, {}".format(e.response.status_code, error_message))
            raise e
        logging.debug('Received response: {} from {}'.format(response.status_code, url))
        try:
            json_response = response.json()
        except ValueError:
            raise ValueError('Cannot find json in http response')
        entity_list = frost_sta_client.utils.transform_json_to_entity_list(json_response, self.entity_class)
        entity_list.set_service(self.service)
        return entity_list
