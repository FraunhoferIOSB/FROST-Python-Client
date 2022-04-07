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

import frost_sta_client.query.query
import frost_sta_client.utils

import logging
import requests
import jsonpatch
import json
from furl import furl


class BaseDao:
    """
    The entity independent implementation of a data access object. Specific entity Daos
    can be implemented by inheriting from this class.
    """
    APPLICATION_JSON_PATCH = {'Content-type': 'application/json-patch+json'}

    def __init__(self, service, entitytype):
        """
        Constructor.
        params:
            service: the service to operate on
            entitytype: a dictionary describing the type of the entity
        """
        self.service = service
        self.entitytype = entitytype["singular"]
        self.entitytype_plural = entitytype["plural"]
        self.entity_class = entitytype["class"]

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value):
        if value is None or isinstance(value, frost_sta_client.service.sensorthingsservice.SensorThingsService):
            self._service = value
            return
        raise ValueError('service should be of type SensorThingsService')

    @property
    def entitytype(self):
        return self._entitytype

    @entitytype.setter
    def entitytype(self, value):
        if value is None or isinstance(value, str):
            self._entitytype = value
            return
        raise ValueError('entitytype should be of type String')

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

    def create(self, entity):
        url = furl(self.service.url)
        url.path.add(self.entitytype_plural)
        logging.debug('Posting to ' + str(url.url))
        json_dict = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        try:
            response = self.service.execute('post', url, json=json_dict)
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json['message']
            logging.error("Creating {} failed with status-code {}, {}".format(type(entity).__name__,
                                                                            e.response.status_code,
                                                                            error_message))
            raise e
        entity.id = int(frost_sta_client.utils.extract_value(response.headers['location']))
        entity.service = self.service
        logging.debug('Received response: ' + str(response.status_code))

    def patch(self, entity, patches):
        """
        method to patch STA entities
        param entity: entity, that the patches should be applied to
        param patches: either a JsonPatch object or list of dictionaries, containing jsonpatch commands
        """
        url = furl(self.service.url)
        if entity.id is None or entity.id == '':
            raise AttributeError('please provide an entity with a valid id')
        url.path.add(self.entity_path(entity.id))
        logging.debug(f'Patching to {url.url}')
        headers = self.APPLICATION_JSON_PATCH
        if patches is None:
            raise ValueError('please provide a list of patches, either as a jsonpatch object or a '
                             'list of dictionaries')
        if not isinstance(patches, jsonpatch.JsonPatch) and \
                not (isinstance(patches, list) and all(isinstance(x, dict) for x in patches)):
            raise ValueError('please provide a list of patches, either as a jsonpatch object or a '
                             'list of dictionaries')
        if isinstance(patches, jsonpatch.JsonPatch):
            patches = patches.patch
        try:
            response = self.service.execute('patch', url, json=patches, headers=headers)
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json['message']
            logging.error("Patching {} failed with status-code {}, {}".format(type(entity).__name__,
                                                                            e.response.status_code,
                                                                            error_message))
            raise e
        logging.debug(f'Received response: {str(response.status_code)}')

    def update(self, entity):
        url = furl(self.service.url)
        if entity.id is None or entity.id == '':
            raise AttributeError('please provide an entity with a valid id')
        url.path.add(self.entity_path(entity.id))
        logging.debug('Updating to {}'.format(url.url))
        json_dict = frost_sta_client.utils.transform_entity_to_json_dict(entity)
        try:
            response = self.service.execute('put', url, json=json_dict)
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json['message']
            logging.error("Updating {} failed with status-code {}, {}".format(type(entity).__name__,
                                                                            e.response.status_code,
                                                                            error_message))
            raise e
        logging.debug('Received response: {}'.format(str(response.status_code)))

    def find(self, id):
        url = furl(self.service.url)
        url.path.add(self.entity_path(id))
        logging.debug('Fetching: {}'.format(url.url))
        try:
            response = self.service.execute('get', url)
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json['message']
            logging.error("Finding {} failed with status-code {}, {}".format(id,
                                                                            e.response.status_code,
                                                                            error_message))
            raise e
        logging.debug('Received response: {}'.format(response.status_code))
        json_response = response.json()
        json_response['id'] = json_response['@iot.id']
        entity = frost_sta_client.utils.transform_json_to_entity(json_response, self.entity_class)
        return entity

    def delete(self, entity):
        url = furl(self.service.url)
        url.path.add(self.entity_path(entity.id))
        logging.debug('Deleting: {}'.format(url.url))
        try:
            response = self.service.execute('delete', url)
        except requests.exceptions.HTTPError as e:
            error_json = e.response.json()
            error_message = error_json['message']
            logging.error("Deleting {} failed with status-code {}, {}".format(type(entity).__name__,
                                                                            e.response.status_code,
                                                                            error_message))
            raise e
        logging.debug('Received response: {}'.format(response.status_code))

    def entity_path(self, id):
        return "{}({})".format(self.entitytype_plural, id)

    def query(self):
        return frost_sta_client.query.query.Query(self.service, self.entitytype, self.entitytype_plural, self.entity_class)
