"""Control vocabulary, key formatting, and entity URLs.

The caller chooses the service root. The vocabulary comes from that root's
response and its ``OData-Version`` header, not from the shape of the URL.
"""

from urllib.parse import urlsplit


def choose_control(odata_version, metadata_is_csdl, service_document=None):
    """Return the write prefix for one probed service root.

    ``OData-Version: 4.01`` writes ``@id`` and ``Nav@navigationLink``.
    Any other OData response writes ``@odata.*``. ``@iot.*`` is only a
    SensorThings service document, a list of ``{name, url}`` and no CSDL.
    """
    version = _canonical_version(odata_version)
    if version == "4.01":
        return "@"
    if version is not None or metadata_is_csdl or _is_odata_document(service_document):
        return "@odata"
    if _is_sensorthings_document(service_document):
        return "@iot"
    raise ValueError(
        "OData-Version and $metadata did not identify a control vocabulary"
    )


def identity_field(prefix):
    """JSON field that carries an entity reference for this vocabulary."""
    if prefix == "@odata":
        return "@odata.id"
    if prefix == "@":
        return "@id"
    if prefix == "@iot":
        return "@iot.id"
    raise ValueError("unknown control vocabulary {!r}".format(prefix))


def format_key(value, edm):
    """Format a key for an OData path parenthesis.

    Integer keys are unquoted. Strings are quoted. Guids use the ``guid'...'``
    form. ``True`` is not an integer key.
    """
    if isinstance(value, bool) or value is None:
        raise ValueError("invalid key {!r} for {}".format(value, edm))
    edm = edm or "Edm.String"
    if edm.startswith("Edm.Int"):
        if isinstance(value, str) and _is_integer_text(value):
            value = int(value)
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValueError("invalid key {!r} for {}".format(value, edm))
        return str(value)
    if edm == "Edm.Guid":
        text = str(value)
        lowered = text.lower()
        if lowered.startswith("guid'") and text.endswith("'"):
            return text
        return "guid'{}'".format(text.strip("'"))
    text = str(value).replace("'", "''")
    return "'{}'".format(text)


def parse_key(location, edm):
    """Read a key from an entity URL.

    The whole parenthesis is kept. An unquoted string is not reduced to one
    character. A composite key comes back as a dict of component names.
    """
    inner = _key_inner(location)
    if _is_composite_key(inner):
        return _parse_composite_key(inner)
    edm = edm or "Edm.String"
    if edm.startswith("Edm.Int"):
        if not _is_integer_text(inner):
            raise ValueError("invalid key {!r} for {}".format(inner, edm))
        return int(inner)
    if edm == "Edm.Guid":
        text = inner
        if text.lower().startswith("guid'") and text.endswith("'"):
            text = text[5:-1]
        return text.strip("'")
    if len(inner) >= 2 and inner[0] == "'" and inner[-1] == "'":
        return inner[1:-1].replace("''", "'")
    return inner


def coerce_key(value, edm):
    """Normalize a key value already held in memory or read from JSON."""
    if isinstance(value, bool) or value is None:
        raise ValueError("invalid key {!r} for {}".format(value, edm))
    edm = edm or "Edm.String"
    if edm.startswith("Edm.Int"):
        if isinstance(value, str) and _is_integer_text(value):
            return int(value)
        if not isinstance(value, int):
            raise ValueError("invalid key {!r} for {}".format(value, edm))
        return value
    if edm == "Edm.Guid":
        text = str(value)
        if text.lower().startswith("guid'") and text.endswith("'"):
            return text[5:-1]
        return text.strip("'")
    return str(value)


def format_entity_key(entity):
    """Format the parenthesis of an entity URL, including a composite key."""
    from frost_sta_client.runtime.entity import key_names_of, key_type_of

    names = key_names_of(type(entity))
    if len(names) == 1:
        return format_key(entity.id, key_type_of(entity, names[0]))
    if len(names) == 0:
        raise ValueError("{} has no key".format(type(entity).__name__))
    parts = []
    for name in names:
        value = entity._key_parts.get(name)
        if value is None:
            raise ValueError("missing key component {}".format(name))
        parts.append("{}={}".format(name, format_key(value, key_type_of(entity, name))))
    return ",".join(parts)


def entity_url(entity, service):
    """Absolute URL of an entity with a key."""
    if getattr(entity, "self_link", None):
        return entity.self_link
    if service is None:
        raise ValueError("cannot build an entity URL without a service or self link")
    entity_set = entity.__entity_set__
    if not entity_set:
        raise ValueError("{} has no entity set".format(type(entity).__name__))
    if entity.id is None:
        raise ValueError("cannot build an entity URL without a key")
    return service.join("{}({})".format(entity_set, format_entity_key(entity)))


def key_reference(entity, service):
    """JSON link that carries only the key.

    Under ``@iot`` a single key is the raw value. A composite SensorThings key
    is the key properties, because ``@iot.id`` holds one value. Under OData the
    value is the entity URL, in ``@odata.id`` or, for OData 4.01, in ``@id``.
    """
    from frost_sta_client.runtime.entity import key_names_of

    prefix = "@iot" if service is None else service.write_prefix
    names = key_names_of(type(entity))
    if prefix == "@iot":
        if len(names) > 1:
            return {
                name: entity._key_parts.get(name)
                for name in names
                if entity._key_parts.get(name) is not None
            }
        return {"@iot.id": entity.id}
    return {identity_field(prefix): entity_url(entity, service)}


def _canonical_version(value):
    if value is None:
        return None
    text = str(value).strip().split(";", 1)[0].strip()
    if not text:
        return None
    if text.startswith("4.01"):
        return "4.01"
    return text


def _is_odata_document(document):
    """An OData service document names its context. It is not a SensorThings index."""
    if not isinstance(document, dict):
        return False
    return "@odata.context" in document or "@context" in document


def _is_sensorthings_document(document):
    """A SensorThings index lists entity sets and is not an OData document."""
    if not isinstance(document, dict):
        return False
    if "@odata.context" in document or "@context" in document:
        return False
    rows = document.get("value")
    if not isinstance(rows, list) or not rows:
        return False
    for row in rows:
        if not isinstance(row, dict) or "name" not in row or "url" not in row:
            return False
    return True


def _is_integer_text(value):
    if isinstance(value, bool) or not isinstance(value, str):
        return False
    if value.startswith("-"):
        return value[1:].isdigit() and len(value) > 1
    return value.isdigit() and len(value) > 0


def _is_composite_key(inner):
    """True when the parenthesis uses name=value components."""
    in_string = False
    for character in inner:
        if character == "'":
            in_string = not in_string
        elif character == "=" and not in_string:
            return True
    return False


def _parse_composite_key(inner):
    values = {}
    for part in _split_key_parts(inner):
        name, separator, raw = part.partition("=")
        if not separator or not name:
            raise ValueError("invalid composite key {!r}".format(inner))
        values[name] = _parse_single(raw, _edm_hint(raw))
    return values


def _edm_hint(raw):
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        return "Edm.String"
    if raw.lower().startswith("guid'"):
        return "Edm.Guid"
    if _is_integer_text(raw):
        return "Edm.Int64"
    return "Edm.String"


def _parse_single(raw, edm):
    if edm.startswith("Edm.Int"):
        if not _is_integer_text(raw):
            raise ValueError("invalid key {!r} for {}".format(raw, edm))
        return int(raw)
    if edm == "Edm.Guid":
        text = raw
        if text.lower().startswith("guid'") and text.endswith("'"):
            text = text[5:-1]
        return text.strip("'")
    if len(raw) >= 2 and raw[0] == "'" and raw[-1] == "'":
        return raw[1:-1].replace("''", "'")
    return raw


def _split_key_parts(inner):
    parts = []
    start = 0
    in_string = False
    for index, character in enumerate(inner):
        if character == "'":
            in_string = not in_string
        elif character == "," and not in_string:
            parts.append(inner[start:index])
            start = index + 1
    parts.append(inner[start:])
    return parts


def _key_inner(location):
    if not isinstance(location, str) or not location:
        raise ValueError("cannot read a key from {!r}".format(location))
    path = urlsplit(location).path or location.split("?", 1)[0].split("#", 1)[0]
    if "(" not in path or not path.endswith(")"):
        raise ValueError("cannot read a key from {!r}".format(location))
    return path[path.rfind("(") + 1:-1]
