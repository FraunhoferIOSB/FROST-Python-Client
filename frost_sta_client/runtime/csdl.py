"""Read an OData CSDL document into a model the generator can emit."""

import xml.etree.ElementTree as ElementTree


class CsdlProperty:
    def __init__(self, name, edm, nullable):
        self.name = name
        self.edm = edm
        self.nullable = nullable


class CsdlParameter:
    def __init__(self, name, edm, nullable):
        self.name = name
        self.edm = edm
        self.nullable = nullable


class CsdlOperation:
    def __init__(self, name, namespace, kind, bound, parameters, return_type):
        self.name = name
        self.namespace = namespace
        self.kind = kind
        self.bound = bound
        self.parameters = parameters
        self.return_type = return_type


class CsdlNavigation:
    def __init__(self, name, target, collection, containment):
        self.name = name
        self.target = target
        self.collection = collection
        self.containment = containment


class CsdlType:
    def __init__(self, name, namespace, kind, open_type, abstract, base):
        self.name = name
        self.namespace = namespace
        self.kind = kind
        self.open_type = open_type
        self.abstract = abstract
        self.base = base
        self.keys = []
        self.key_types = {}
        self.key = None
        self.key_type = None
        self.properties = []
        self.navigations = []

    @property
    def qualified(self):
        if self.namespace:
            return "{}.{}".format(self.namespace, self.name)
        return self.name


class CsdlEnum:
    def __init__(self, name, namespace):
        self.name = name
        self.namespace = namespace
        self.members = []


class Model:
    """Parsed metadata. ``actions`` is the set of action names."""

    def __init__(self):
        self.namespace = ""
        self.types = {}
        self.enums = {}
        self.entity_sets = []
        self.action_bindings = {}
        self.function_bindings = {}
        self.actions = set()
        self.functions = set()
        self.action_list = []
        self.function_list = []
        self.type_definitions = {}

    def type_named(self, name):
        """Return one type by qualified or unique short name."""
        found = _find_type(self, name)
        if found is None:
            raise KeyError(name)
        return found


def parse_csdl(xml_text):
    """Parse a CSDL XML document. Unknown elements are ignored."""
    if isinstance(xml_text, bytes):
        xml_text = xml_text.decode("utf-8")
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValueError("CSDL document is not XML") from exc
    schemas = [element for element in root.iter() if _local(element.tag) == "Schema"]
    if not schemas:
        raise ValueError("CSDL document has no Schema")
    model = Model()
    model.namespace = schemas[0].attrib.get("Namespace", "")
    for schema in schemas:
        _read_schema(schema, model)
    _apply_bases(model)
    _apply_type_definitions(model)
    _fill_key_types(model)
    model.actions = set(model.action_bindings)
    model.functions = set(model.function_bindings)
    return model


def _read_schema(schema, model):
    namespace = schema.attrib.get("Namespace", "")
    for element in _children(schema, "EnumType"):
        _read_enum(element, namespace, model)
    for element in _children(schema, "TypeDefinition"):
        _read_type_definition(element, namespace, model)
    for element in _children(schema, "ComplexType"):
        _add_type(_read_structured(element, namespace, "complex"), model)
    for element in _children(schema, "EntityType"):
        _add_type(_read_structured(element, namespace, "entity"), model)
    for element in _children(schema, "Action"):
        _add_operation(_read_operation(element, namespace, "action"), model)
    for element in _children(schema, "Function"):
        _add_operation(_read_operation(element, namespace, "function"), model)
    for container in _children(schema, "EntityContainer"):
        for entity_set in _children(container, "EntitySet"):
            model.entity_sets.append((
                entity_set.attrib["Name"],
                _declared_name(entity_set.attrib.get("EntityType", "")),
            ))
        for imported in _children(container, "ActionImport"):
            _ensure_import(imported.attrib["Name"], namespace, "action", model)
        for imported in _children(container, "FunctionImport"):
            _ensure_import(imported.attrib["Name"], namespace, "function", model)


def _read_type_definition(element, namespace, model):
    name = element.attrib["Name"]
    underlying = element.attrib.get("UnderlyingType", "Edm.String")
    model.type_definitions[name] = underlying
    if namespace:
        model.type_definitions["{}.{}".format(namespace, name)] = underlying


def _apply_type_definitions(model):
    """Replace typedef names with the underlying EDM type.

    FROST declares ``org.OGC.STA.Geometry`` as a name for ``Edm.Geometry``.
    The runtime then uses one geometry codec for that property.
    """
    for item in model.types.values():
        for prop in item.properties:
            prop.edm = _underlying(prop.edm, model.type_definitions)


def _underlying(edm, definitions):
    normalized = _normalize_type(edm)
    if normalized.startswith("Collection(") and normalized.endswith(")"):
        inner = normalized[len("Collection("):-1]
        return "Collection({})".format(_lookup_type(inner, definitions))
    return _lookup_type(normalized, definitions)


def _lookup_type(edm, definitions):
    if edm in definitions:
        return definitions[edm]
    short = edm.rsplit(".", 1)[-1]
    if short in definitions and not edm.startswith("Edm."):
        return definitions[short]
    return edm


def _normalize_type(edm):
    """FROST writes ``Collection(String)`` for a list of strings.

    That list is ``Collection(Edm.String)``: a non-string element is rejected.
    A scalar type named ``String`` is left unchanged. OData 4.0 uses it for
    ``result``, which is ``Edm.Untyped`` in OData 4.01, and a number must
    still pass through.
    """
    if edm == "Collection(String)":
        return "Collection(Edm.String)"
    return edm


def _read_enum(element, namespace, model):
    name = element.attrib["Name"]
    if name in model.enums:
        raise ValueError("duplicate enum {}".format(name))
    enum = CsdlEnum(name, namespace)
    for member in _children(element, "Member"):
        member_name = member.attrib["Name"]
        raw = member.attrib.get("Value", member_name)
        value = int(raw) if _integer_text(raw) else raw
        enum.members.append((member_name, value))
    model.enums[name] = enum


def _read_structured(element, namespace, kind):
    item = CsdlType(
        name=element.attrib["Name"],
        namespace=namespace,
        kind=kind,
        open_type=_flag(element.attrib.get("OpenType")),
        abstract=_flag(element.attrib.get("Abstract")),
        base=_declared_name(element.attrib.get("BaseType")) if element.attrib.get("BaseType") else None,
    )
    if kind == "entity":
        for key in _children(element, "Key"):
            for ref in _children(key, "PropertyRef"):
                item.keys.append(ref.attrib["Name"])
    for prop in _children(element, "Property"):
        nullable = True
        if "Nullable" in prop.attrib:
            nullable = _flag(prop.attrib.get("Nullable"))
        item.properties.append(CsdlProperty(
            prop.attrib["Name"],
            prop.attrib.get("Type", "Edm.String"),
            nullable,
        ))
    for nav in _children(element, "NavigationProperty"):
        declared = nav.attrib.get("Type", "")
        item.navigations.append(CsdlNavigation(
            nav.attrib["Name"],
            _declared_name(declared),
            declared.strip().startswith("Collection("),
            _flag(nav.attrib.get("ContainsTarget")),
        ))
    return item


def _add_type(item, model):
    qualified = item.qualified
    if qualified in model.types:
        raise ValueError("duplicate type {}".format(qualified))
    model.types[qualified] = item


def _read_operation(element, namespace, kind):
    parameters = []
    for param in _children(element, "Parameter"):
        nullable = True
        if "Nullable" in param.attrib:
            nullable = _flag(param.attrib.get("Nullable"))
        parameters.append(CsdlParameter(
            param.attrib.get("Name", ""),
            param.attrib.get("Type", "Edm.String"),
            nullable,
        ))
    return_type = None
    for returned in _children(element, "ReturnType"):
        return_type = returned.attrib.get("Type")
    bound = _flag(element.attrib.get("IsBound"))
    return CsdlOperation(
        element.attrib["Name"],
        namespace,
        kind,
        bound,
        parameters,
        return_type,
    )


def _add_operation(operation, model):
    if operation.kind == "action":
        model.action_list.append(operation)
        model.action_bindings[operation.name] = operation.bound
    else:
        model.function_list.append(operation)
        model.function_bindings[operation.name] = operation.bound


def _ensure_import(name, namespace, kind, model):
    bindings = model.action_bindings if kind == "action" else model.function_bindings
    listing = model.action_list if kind == "action" else model.function_list
    if name in bindings:
        return
    bindings[name] = False
    listing.append(CsdlOperation(name, namespace, kind, False, [], None))


def _apply_bases(model):
    seen = {item.qualified for item in model.types.values() if not item.base}
    pending = [item for item in model.types.values() if item.base]
    while pending:
        next_pending = []
        for item in pending:
            base = _find_type(model, item.base)
            if base is None:
                raise ValueError("unknown base type {} of {}".format(item.base, item.name))
            if base.qualified not in seen:
                next_pending.append(item)
                continue
            _inherit(item, base)
            seen.add(item.qualified)
        if len(next_pending) == len(pending):
            raise ValueError("cyclic base types")
        pending = next_pending


def _inherit(item, base):
    names = {prop.name for prop in item.properties}
    inherited = [prop for prop in base.properties if prop.name not in names]
    item.properties = inherited + item.properties
    nav_names = {nav.name for nav in item.navigations}
    inherited_navs = [nav for nav in base.navigations if nav.name not in nav_names]
    item.navigations = inherited_navs + item.navigations
    if not item.keys and base.keys:
        item.keys = list(base.keys)
        item.key_types = dict(base.key_types)


def _fill_key_types(model):
    for item in model.types.values():
        if item.kind != "entity":
            continue
        if not item.keys:
            item.keys = ["id"]
        for name in item.keys:
            for prop in item.properties:
                if prop.name == name:
                    item.key_types[name] = prop.edm
                    break
            item.key_types.setdefault(name, "Edm.Int64")
        if len(item.keys) == 1:
            item.key = item.keys[0]
            item.key_type = item.key_types[item.key]
        else:
            item.key = None
            item.key_type = None


def _find_type(model, name):
    if name in model.types:
        return model.types[name]
    matches = [item for item in model.types.values() if item.name == name or item.qualified == name]
    if len(matches) == 1:
        return matches[0]
    return None


def _declared_name(value):
    text = (value or "").strip()
    if text.startswith("Collection(") and text.endswith(")"):
        text = text[len("Collection("):-1].strip()
    if text.startswith("self."):
        text = text[len("self."):]
    return text


def _children(element, name):
    return [child for child in list(element) if _local(child.tag) == name]


def _local(tag):
    if not isinstance(tag, str):
        return ""
    return tag.rsplit("}", 1)[-1]


def _short(name):
    text = (name or "").strip()
    if text.startswith("Collection(") and text.endswith(")"):
        text = text[len("Collection("):-1].strip()
    if text.startswith("self."):
        text = text[len("self."):]
    return text.rsplit(".", 1)[-1]


def _flag(value):
    return str(value).lower() == "true"


def _integer_text(value):
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("-"):
        return value[1:].isdigit()
    return value.isdigit()
