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

import requests
from furl import furl
import logging
import importlib
import sys

from frost_sta_client.dao.base import BaseDao
from frost_sta_client.service import auth_handler
from frost_sta_client.model.ext import entity_type


class SensorThingsService:

    def __init__(self, url, auth_handler=None, proxies=None):
        self.url = url
        self.auth_handler = auth_handler
        self.proxies = proxies

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, value):
        if value is None:
            self._url = value
            return
        try:
            self._url = furl(value)
        except ValueError as e:
            logging.error("received invalid url")
            raise e


    @property
    def auth_handler(self):
        return self._auth_handler

    @auth_handler.setter
    def auth_handler(self, value):
        if value is None:
            self._auth_handler = None
            return
        if not isinstance(value, auth_handler.AuthHandler):
            raise ValueError('auth should be of type AuthHandler!')
        self._auth_handler = value

    
    @property
    def proxies(self):
        return self._proxies

    @proxies.setter
    def proxies(self, value):
        if value is None:
            self._proxies = None
            return
        elif not isinstance(value, dict):
            raise ValueError('Proxies must be a Dictionary!')
        self._proxies = value
    
    
    def execute(self, method, url, **kwargs):
        if self.auth_handler is not None:
            response = requests.request(method, url, proxies=self.proxies, auth=self.auth_handler.add_auth_header(), **kwargs)
        else:
            response = requests.request(method, url, proxies=self.proxies, **kwargs)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise e

        return response

    def get_path(self, parent, relation):
        if parent is None:
            return relation
        this_entity_type = entity_type.get_list_for_class(type(parent))
        _id = f"'{parent.id}'" if isinstance(parent.id, str) else parent.id
        return "{entity_type}({id})/{relation}".format(entity_type=this_entity_type, id=_id, relation=relation)

    def get_full_path(self, parent, relation):
        slash = "" if str(self.url.path).endswith('/') else "/"
        url = self.url.url + slash + self.get_path(parent, relation)
        return furl(url)

    def _generic_odata_dao_for_entity(self, entity):
        """Return GenericODataDao if entity is from a code-generated OData module; otherwise None."""
        try:
            mod_name = entity.__class__.__module__
            mod = sys.modules.get(mod_name) or importlib.import_module(mod_name)
            mapping = getattr(mod, 'ENTITY_SETS', None)
            if not isinstance(mapping, dict):
                return None
            entity_set = None
            for es_name, cls in mapping.items():
                if cls is entity.__class__ or isinstance(entity, cls):
                    entity_set = es_name
                    break
            if not entity_set:
                return None
            from frost_sta_client.dao.generic_odata import GenericODataDao
            return GenericODataDao(self, entity_set, mod)
        except Exception:
            return None

    def create(self, entity):
        dao_getter = getattr(entity, 'get_dao', None)
        if callable(dao_getter):
            entity.get_dao(self).create(entity)
            return
        gen = self._generic_odata_dao_for_entity(entity)
        if gen:
            gen.create(entity)
            return
        raise ValueError('No DAO found for entity and it is not a generated OData class')

    def update(self, entity):
        dao_getter = getattr(entity, 'get_dao', None)
        if callable(dao_getter):
            entity.get_dao(self).update(entity)
            return
        gen = self._generic_odata_dao_for_entity(entity)
        if gen:
            gen.update(entity)
            return
        raise ValueError('No DAO found for entity and it is not a generated OData class')

    def patch(self, entity, patches):
        dao_getter = getattr(entity, 'get_dao', None)
        if callable(dao_getter):
            entity.get_dao(self).patch(entity, patches)
            return
        gen = self._generic_odata_dao_for_entity(entity)
        if gen:
            gen.patch(entity, patches)
            return
        raise ValueError('No DAO found for entity and it is not a generated OData class')

    def delete(self, entity):
        dao_getter = getattr(entity, 'get_dao', None)
        if callable(dao_getter):
            entity.get_dao(self).delete(entity)
            return
        gen = self._generic_odata_dao_for_entity(entity)
        if gen:
            gen.delete(entity)
            return
        raise ValueError('No DAO found for entity and it is not a generated OData class')
    def __getattr__(self, name):
        """Dynamic DAO factory methods for entity collections.
        
        Example: service.things(), service.datastreams(), service.features_of_interest(), ...
        """
        # lazy import to avoid circular imports
        from frost_sta_client.model.ext.entity_type import EntityTypes
        import re
        
        def _to_snake(s: str) -> str:
            s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)
            return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        
        for singular, meta in EntityTypes.items():
            plural = meta.get('plural')
            if not plural:
                continue
            meth = _to_snake(plural)
            if name == meth:
                return lambda: BaseDao(self, meta)
        raise AttributeError(name)
