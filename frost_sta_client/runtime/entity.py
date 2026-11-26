"""Entity and complex-type base.

Generated classes declare PropertySpec and NavigationSpec tuples. Equality,
JSON, and attribute access live here, once.
"""

from frost_sta_client.runtime.control import (
    coerce_key,
    entity_url,
    identity_field,
    key_reference,
)
from frost_sta_client.runtime.registry import register_type, resolve_declared
from frost_sta_client.runtime.specs import NavigationSpec, PropertySpec
from frost_sta_client.runtime.values import (
    OMIT,
    read_structural,
    structural_equal,
    write_structural,
)

__all__ = [
    "ComplexType",
    "Entity",
    "NavigationSpec",
    "PropertySpec",
]

def key_names_of(cls):
    """CSDL key property names. A single key stays a one-tuple."""
    names = getattr(cls, "__key_names__", None)
    if names:
        return tuple(names)
    single = getattr(cls, "__key_name__", None)
    if single:
        return (single,)
    return ()


def key_type_of(entity, name):
    types = getattr(type(entity), "__key_types__", None) or {}
    if name in types:
        return types[name]
    if name == getattr(type(entity), "__key_name__", None):
        return getattr(type(entity), "__key_type__", None) or "Edm.String"
    return "Edm.String"


def _control_prefix(service):
    if service is None:
        return "@iot"
    return service.write_prefix


_CONTROL_KEYS = {
    "@iot.id",
    "@iot.selfLink",
    "@iot.nextLink",
    "@iot.count",
    "@odata.id",
    "@odata.context",
    "@odata.type",
    "@odata.editLink",
    "@odata.etag",
    "@odata.nextLink",
    "@odata.count",
    "@id",
    "@context",
    "@count",
    "@nextLink",
}


class Entity:
    """Base of every generated entity type."""

    __csdl_name__ = ""
    __namespace__ = ""
    __entity_set__ = None
    __key_name__ = "id"
    __key_type__ = "Edm.Int64"
    __open_type__ = False
    __is_entity__ = True
    __properties__ = ()
    __navigations__ = ()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        name = getattr(cls, "__csdl_name__", "")
        if name:
            namespace = getattr(cls, "__namespace__", "")
            qualified = "{}.{}".format(namespace, name) if namespace else name
            register_type(name, qualified, cls)
        key_names = set(key_names_of(cls))
        for spec in cls.__properties__:
            if spec.wire in key_names:
                if len(key_names) == 1:
                    continue
                setattr(cls, spec.python_name, _KeyProperty(spec))
                continue
            if spec.python_name == "id":
                continue
            setattr(cls, spec.python_name, _Property(spec))
        for nav in cls.__navigations__:
            setattr(cls, nav.python_name, _Navigation(nav))
            setattr(cls, "get_{}".format(nav.python_name), _navigation_getter(nav))

    def __init__(self, **kwargs):
        self._blank()
        if "id" in kwargs:
            self.id = kwargs.pop("id")
        if "self_link" in kwargs:
            self.self_link = kwargs.pop("self_link")
        key_names = set(key_names_of(type(self)))
        for spec in _ordered_specs(type(self)):
            if spec.wire in key_names or spec.python_name == "id":
                if spec.python_name in kwargs and spec.wire in key_names:
                    self._set_key_part(spec.wire, kwargs.pop(spec.python_name))
                continue
            if spec.python_name in kwargs:
                setattr(self, spec.python_name, kwargs.pop(spec.python_name))
        for nav in self.__navigations__:
            if nav.python_name in kwargs:
                setattr(self, nav.python_name, kwargs.pop(nav.python_name))
        if kwargs:
            if self.__open_type__:
                self._extra.update(kwargs)
            else:
                unknown = ", ".join(sorted(kwargs))
                raise TypeError("{} got unexpected arguments: {}".format(type(self).__name__, unknown))

    def _blank(self):
        self._id = None
        self._key_parts = {}
        self.self_link = None
        self._service = None
        self._values = {}
        self._navs = {}
        self._nav_links = {}
        self._extra = {}
        key_names = set(key_names_of(type(self)))
        for spec in self.__properties__:
            if spec.python_name == "id" or spec.wire in key_names:
                continue
            self._values[spec.python_name] = None
        for nav in self.__navigations__:
            self._navs[nav.python_name] = None

    @property
    def id(self):
        names = key_names_of(type(self))
        if len(names) > 1:
            if all(self._key_parts.get(name) is None for name in names):
                return None
            return tuple(self._key_parts.get(name) for name in names)
        if len(names) == 1:
            return self._key_parts.get(names[0], self._id)
        return self._id

    @id.setter
    def id(self, value):
        names = key_names_of(type(self))
        if not names:
            self._id = None if value is None else coerce_key(value, self.__key_type__)
            return
        if len(names) == 1:
            self._set_key_part(names[0], value)
            self._id = self._key_parts.get(names[0])
            return
        if value is None:
            for name in names:
                self._key_parts[name] = None
            self._id = None
            return
        if isinstance(value, dict):
            supplied = [value.get(name) for name in names]
        else:
            supplied = list(value)
        if len(supplied) != len(names):
            raise ValueError(
                "{} key requires {}".format(type(self).__name__, ", ".join(names))
            )
        for name, item in zip(names, supplied):
            self._set_key_part(name, item)
        self._id = tuple(self._key_parts.get(name) for name in names)

    def _set_key_part(self, name, value):
        if value is None:
            self._key_parts[name] = None
            return
        self._key_parts[name] = coerce_key(value, key_type_of(self, name))

    @property
    def service(self):
        return self._service

    @service.setter
    def service(self, value):
        self.set_service(value)

    def set_service(self, service, _seen=None):
        """Attach a service and pass it to every loaded child.

        Every navigation is visited, including historical locations and tasks.
        A cycle is visited once.
        """
        if service is not None and not hasattr(service, "execute"):
            raise ValueError("service must be a SensorThingsService")
        if _seen is None:
            _seen = set()
        if id(self) in _seen:
            return
        _seen.add(id(self))
        self._service = service
        for nav in self.__navigations__:
            value = self._navs.get(nav.python_name)
            if value is None:
                continue
            if nav.collection:
                value.set_service(service, _seen)
            else:
                value.set_service(service, _seen)

    def _assign(self, spec, value):
        if value is None:
            if not spec.nullable:
                raise ValueError("{} must not be None".format(spec.python_name))
            self._values[spec.python_name] = None
            return
        self._values[spec.python_name] = read_structural(spec, value, self)

    @classmethod
    def from_json(cls, data, service=None):
        """Build an instance from one entity object.

        ``@iot.id`` is the key. ``@odata.id`` is the entity URL and is not the
        key. When ``@iot.id`` is absent, the key is the CSDL key property.
        A missing property becomes None. JSON null is rejected when the
        property is not nullable. Collections are read from an array or from
        ``{"value": [...]}``.
        """
        if not isinstance(data, dict):
            raise ValueError("{} expected an object".format(cls.__name__))
        entity = cls.__new__(cls)
        entity._blank()
        entity._read_identity(data)
        known = set(_CONTROL_KEYS)
        known.update(key_names_of(cls))
        for spec in _ordered_specs(cls):
            known.add(spec.wire)
            if spec.wire in key_names_of(cls) or spec.python_name == "id":
                continue
            if spec.wire not in data:
                continue
            entity._assign(spec, data[spec.wire])
        for nav in cls.__navigations__:
            _mark_navigation(known, nav.wire)
            entity._read_navigation(nav, data, service)
        if cls.__open_type__:
            for key, value in data.items():
                if key not in known and not key.startswith("@"):
                    entity._extra[key] = value
        if service is not None:
            entity.set_service(service)
        return entity

    def _read_identity(self, data):
        if not self.__is_entity__:
            return
        names = key_names_of(type(self))
        if len(names) <= 1 and "@iot.id" in data and data.get("@iot.id") is not None:
            self.id = data["@iot.id"]
        elif len(names) == 1 and data.get(names[0]) is not None:
            self.id = data[names[0]]
        elif len(names) > 1:
            present = {
                name: data[name]
                for name in names
                if name in data and data.get(name) is not None
            }
            if present:
                self.id = present
        for key in ("@odata.id", "@iot.selfLink", "@id"):
            value = data.get(key)
            if isinstance(value, str) and ("://" in value or value.startswith("/")):
                self.self_link = value
                break

    def _read_navigation(self, nav, data, service):
        link = _present(data, nav.wire, "navigationLink")
        count = _annotation(data, nav.wire, "count")
        next_link = _present(data, nav.wire, "nextLink")
        present = nav.wire in data or link is not None or count is not _MISSING
        if not present:
            return
        if link is not None:
            self._nav_links[nav.python_name] = link
        target = _target_class(nav, self)
        if not nav.collection:
            raw = data.get(nav.wire)
            if raw is None:
                return
            if not isinstance(raw, dict):
                raise ValueError("{} should be a {}".format(nav.python_name, target.__name__))
            self._navs[nav.python_name] = target.from_json(raw, service)
            return
        from frost_sta_client.runtime.entity_list import EntityList

        raw = data.get(nav.wire)
        entities = []
        if raw is None:
            pass
        elif isinstance(raw, list):
            entities = [_read_target(target, item, nav) for item in raw]
        elif isinstance(raw, dict) and isinstance(raw.get("value"), list):
            entities = [_read_target(target, item, nav) for item in raw["value"]]
            if next_link is None:
                next_link = raw.get("@iot.nextLink") or raw.get("@odata.nextLink") or raw.get("@nextLink")
            if count is _MISSING:
                count = _inline_count(raw)
        else:
            raise ValueError("{} should be a list of {}".format(nav.python_name, target.__name__))
        listing = EntityList(entity_class=target, entities=entities)
        listing.navigation_link = link
        listing.next_link = next_link
        listing.count = None if count is _MISSING else count
        self._navs[nav.python_name] = listing

    def to_json(self, service=None, ancestors=None):
        """Write this object.

        None is omitted. ``''`` and ``{}`` are written. Empty collections are
        omitted. A related entity that only has a key becomes a key reference.
        Further fields are embedded when the navigation is containment, and
        also when the related entity has no key yet, because there is nothing
        to address it with. A cycle writes the key and stops.
        """
        service = self._service if service is None else service
        if ancestors is None:
            ancestors = set()
        if id(self) in ancestors:
            if self.id is None:
                return {}
            return key_reference(self, service)
        ancestors.add(id(self))
        try:
            return self._to_json_body(service, ancestors)
        finally:
            ancestors.discard(id(self))

    def _to_json_body(self, service, ancestors):
        data = {}
        if self.__is_entity__:
            self._write_identity(data, service)
        key_names = set(key_names_of(type(self)))
        for spec in self.__properties__:
            if spec.wire in key_names or spec.python_name == "id":
                continue
            written = write_structural(spec, self._values.get(spec.python_name), service, self)
            if written is OMIT:
                continue
            data[spec.wire] = written
        for nav in self.__navigations__:
            written = self._write_navigation(nav, service, ancestors)
            if written is OMIT:
                continue
            data[nav.wire] = written
        if self.__open_type__:
            for key, value in self._extra.items():
                if value is None:
                    continue
                data[key] = value
        return data

    def _write_identity(self, data, service):
        names = key_names_of(type(self))
        if not names or all(self._key_parts.get(name) is None for name in names):
            return
        prefix = _control_prefix(service)
        if len(names) == 1:
            value = self._key_parts.get(names[0])
            if prefix == "@iot":
                data["@iot.id"] = value
                _write_iot_self_link(self, data, service)
            else:
                data[names[0]] = value
                if service is not None:
                    data[identity_field(prefix)] = _odata_identity(self, service)
            return
        for name in names:
            value = self._key_parts.get(name)
            if value is not None:
                data[name] = value
        complete = all(self._key_parts.get(name) is not None for name in names)
        if prefix == "@iot":
            _write_iot_self_link(self, data, service)
        elif service is not None and complete:
            data[identity_field(prefix)] = _odata_identity(self, service)

    def _write_navigation(self, nav, service, ancestors):
        value = self._navs.get(nav.python_name)
        if value is None:
            return OMIT
        if nav.collection:
            entities = value.entities
            written = []
            for item in entities:
                body = _write_related(item, nav, service, ancestors)
                if body is OMIT:
                    continue
                written.append(body)
            if not written:
                return OMIT
            return written
        return _write_related(value, nav, service, ancestors)

    def _dao_for(self, nav):
        from frost_sta_client.runtime.dao import dao_for_navigation
        return dao_for_navigation(self, nav)

    def __eq__(self, other):
        if other is self:
            return True
        if type(other) is not type(self):
            return NotImplemented
        if self.__is_entity__:
            if (self.id is None) != (other.id is None):
                return False
            if self.id is not None and self.id != other.id:
                return False
        key_names = set(key_names_of(type(self)))
        for spec in self.__properties__:
            if spec.wire in key_names or spec.python_name == "id":
                continue
            left = self._values.get(spec.python_name)
            right = other._values.get(spec.python_name)
            if not structural_equal(spec, left, right):
                return False
        for nav in self.__navigations__:
            if nav.collection:
                continue
            left = self._navs.get(nav.python_name)
            right = other._navs.get(nav.python_name)
            if left is None or right is None or left.id is None or right.id is None:
                continue
            if left.id != right.id:
                return False
        if self._extra != other._extra:
            return False
        return True

    def __hash__(self):
        return None

    def __repr__(self):
        return "{}(id={!r})".format(type(self).__name__, self.id)


class ComplexType(Entity):
    """Base of every generated complex type."""

    __is_entity__ = False
    __entity_set__ = None
    __key_name__ = None
    __key_type__ = "Edm.String"


class _KeyProperty:
    """A component of a composite key."""

    def __init__(self, spec):
        self.spec = spec

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance._key_parts.get(self.spec.wire)

    def __set__(self, instance, value):
        instance._set_key_part(self.spec.wire, value)


class _Property:
    def __init__(self, spec):
        self.spec = spec

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance._values.get(self.spec.python_name)

    def __set__(self, instance, value):
        instance._assign(self.spec, value)


class _Navigation:
    def __init__(self, nav):
        self.nav = nav

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        return instance._navs.get(self.nav.python_name)

    def __set__(self, instance, value):
        nav = self.nav
        if value is None:
            instance._navs[nav.python_name] = None
            return
        target = _target_class(nav, instance)
        if nav.collection:
            instance._navs[nav.python_name] = _coerce_collection(nav, target, value)
            return
        if not isinstance(value, target):
            raise ValueError("{} should be a {}".format(nav.python_name, target.__name__))
        instance._navs[nav.python_name] = value


def _navigation_getter(nav):
    def getter(self):
        return self._dao_for(nav)

    getter.__name__ = "get_{}".format(nav.python_name)
    getter.__doc__ = "Return the DAO for the {} navigation.".format(nav.wire)
    return getter


def _ordered_specs(cls):
    specs = [spec for spec in cls.__properties__]
    specs.sort(key=lambda spec: spec.python_name != "encoding_type")
    return specs


def _target_class(nav, owner):
    target = resolve_declared(nav.target, owner)
    if target is None:
        raise ValueError("unknown navigation target {}".format(nav.target))
    return target


def _read_target(target, item, nav):
    if not isinstance(item, dict):
        raise ValueError("{} should be a list of {}".format(nav.python_name, target.__name__))
    return target.from_json(item)


def _coerce_collection(nav, target, value):
    from frost_sta_client.runtime.entity_list import EntityList

    if isinstance(value, EntityList):
        entities = list(value.entities)
        next_link = value.next_link
        count = value.count
        navigation_link = value.navigation_link
    elif isinstance(value, list):
        entities = list(value)
        next_link = None
        count = None
        navigation_link = None
    else:
        raise ValueError("{} should be a list of {}".format(nav.python_name, target.__name__))
    for item in entities:
        if not isinstance(item, target):
            raise ValueError("{} should be a list of {}".format(nav.python_name, target.__name__))
    listing = EntityList(entity_class=target, entities=entities)
    listing.next_link = next_link
    listing.count = count
    listing.navigation_link = navigation_link
    return listing


def _write_related(item, nav, service, ancestors):
    """Write one related entity as an embed or as a key reference."""
    if item is None:
        return OMIT
    if id(item) in ancestors:
        if item.id is None:
            return OMIT
        return key_reference(item, service)
    content = _has_content(item)
    if item.id is None and not content:
        return OMIT
    if item.id is not None and (not content or not nav.containment):
        return key_reference(item, service)
    return item.to_json(service, ancestors)


def _has_content(entity):
    for spec in entity.__properties__:
        if spec.wire == entity.__key_name__ or spec.python_name == "id":
            continue
        value = entity._values.get(spec.python_name)
        if value is None:
            continue
        if is_empty_collection(spec, value):
            continue
        return True
    for nav in entity.__navigations__:
        value = entity._navs.get(nav.python_name)
        if value is None:
            continue
        if nav.collection:
            if value.entities:
                return True
            continue
        return True
    return bool(entity._extra)


def is_empty_collection(spec, value):
    return spec.edm.startswith("Collection(") and len(value) == 0


def _write_iot_self_link(entity, data, service):
    """SensorThings writes the entity URL in ``@iot.selfLink`` next to the key."""
    if entity.self_link:
        data["@iot.selfLink"] = entity.self_link
        return
    if service is None:
        return
    try:
        data["@iot.selfLink"] = entity_url(entity, service)
    except ValueError:
        return


def _odata_identity(entity, service):
    if entity.self_link:
        return entity.self_link
    from frost_sta_client.runtime.control import entity_url
    return entity_url(entity, service)


def _annotation(data, wire, suffix):
    value = _present(data, wire, suffix)
    if value is None:
        return _MISSING
    return value


def _present(data, wire, suffix):
    for key in (
        "{}@iot.{}".format(wire, suffix),
        "{}@odata.{}".format(wire, suffix),
        "{}@{}".format(wire, suffix),
    ):
        if key in data:
            return data[key]
    return None


def _inline_count(raw):
    for key in ("@iot.count", "@odata.count", "@count"):
        if key in raw:
            return raw[key]
    return _MISSING


def _mark_navigation(known, wire):
    known.add(wire)
    for suffix in ("navigationLink", "count", "nextLink"):
        known.add("{}@iot.{}".format(wire, suffix))
        known.add("{}@odata.{}".format(wire, suffix))
        known.add("{}@{}".format(wire, suffix))


class _MissingType:
    pass


_MISSING = _MissingType()
