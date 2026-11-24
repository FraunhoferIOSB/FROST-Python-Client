"""Data access for every entity set.

Key parentheses follow the EDM type of the key. A composite key is written as
``Name=value`` components. Actions are not called from here.
"""

from frost_sta_client.runtime.control import format_entity_key, format_key, parse_key
from frost_sta_client.runtime.entity import key_names_of
from frost_sta_client.runtime.errors import call, response_json
from frost_sta_client.runtime.query import Query


class Dao:
    def __init__(self, service, entity_class, entity_set, parent=None, navigation=None, absolute_url=None):
        self.service = service
        self.entity_class = entity_class
        self.entity_set = entity_set
        self.parent = parent
        self.navigation = navigation
        self.absolute_url = absolute_url

    def query(self):
        return Query(self)

    def collection_url(self):
        if self.absolute_url:
            return self.absolute_url
        if self.parent is None:
            return self.service.join(self.entity_set)
        if self.parent.id is None:
            raise ValueError("parent id is required to address this navigation")
        key = format_key(self.parent.id, self.parent.__key_type__)
        parent_set = self.parent.__entity_set__
        wire = self.navigation.wire if self.navigation is not None else self.entity_set
        return self.service.join("{parent}({key})/{wire}".format(parent=parent_set, key=key, wire=wire))

    def entity_url(self, key):
        formatted = self._format_lookup(key)
        if self.parent is None and not self.absolute_url:
            return self.service.join("{}({})".format(self.entity_set, formatted))
        return "{}({})".format(self.collection_url(), formatted)

    def _format_lookup(self, key):
        names = key_names_of(self.entity_class)
        if len(names) > 1 or isinstance(key, (tuple, list, dict)):
            entity = self.entity_class.__new__(self.entity_class)
            entity._blank()
            entity.id = key
            return format_entity_key(entity)
        return format_key(key, self.entity_class.__key_type__)

    def find(self, key):
        url = self.entity_url(key)
        response = call(self.service, "get", url, "Finding {}".format(self.entity_class.__name__))
        return self.entity_class.from_json(response_json(response), self.service)

    def create(self, entity):
        payload = entity.to_json(self.service)
        response = call(
            self.service,
            "post",
            self.collection_url(),
            "Creating {}".format(self.entity_class.__name__),
            json=payload,
        )
        location = _location_header(response)
        if location:
            entity.self_link = location
            entity.id = parse_key(location, self.entity_class.__key_type__)
        entity.set_service(self.service)
        return entity

    def update(self, entity):
        if entity.id is None:
            raise ValueError("update requires an id")
        payload = entity.to_json(self.service)
        call(
            self.service,
            "put",
            self.entity_url(entity.id),
            "Updating {}".format(self.entity_class.__name__),
            json=payload,
        )
        entity.set_service(self.service)
        return entity

    def patch(self, entity, body):
        if entity.id is None:
            raise ValueError("patch requires an id")
        if not isinstance(body, dict):
            raise TypeError("patch body must be a dictionary")
        call(
            self.service,
            "patch",
            self.entity_url(entity.id),
            "Patching {}".format(self.entity_class.__name__),
            json=body,
        )
        entity.set_service(self.service)
        return entity

    def delete(self, entity):
        if entity.id is None:
            raise ValueError("delete requires an id")
        call(
            self.service,
            "delete",
            self.entity_url(entity.id),
            "Deleting {}".format(self.entity_class.__name__),
        )


def dao_for_navigation(entity, nav):
    """Build the DAO ``get_<navigation>`` returns.

    A stored navigation link is used as the request URL when one was read.
    """
    if entity.service is None:
        raise ValueError("service is not set")
    target = _target(nav, entity)
    absolute = entity._nav_links.get(nav.python_name)
    return Dao(
        entity.service,
        target,
        target.__entity_set__,
        parent=entity,
        navigation=nav,
        absolute_url=absolute,
    )


def _target(nav, owner):
    from frost_sta_client.runtime.registry import resolve_declared

    target = resolve_declared(nav.target, owner)
    if target is None:
        raise ValueError("unknown navigation target {}".format(nav.target))
    return target


def _location_header(response):
    headers = getattr(response, "headers", None) or {}
    location = headers.get("Location")
    if location is None:
        location = headers.get("location")
    return location
