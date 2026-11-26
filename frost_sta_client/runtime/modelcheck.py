"""Compare a loaded model with OData metadata or a built-in SensorThings model."""

from enum import Enum

from frost_sta_client.runtime.builtin import BuiltInModel

_ACTUATION_TYPES = frozenset({"Actuator", "Task", "TaskingCapability"})
_ACTUATION_SETS = frozenset({"Actuators", "Tasks", "TaskingCapabilities"})


def assert_same_model(loaded, expected, where):
    """Raise RuntimeError when the two model signatures differ."""
    diffs = differences(signature(loaded), signature(expected))
    if diffs:
        raise RuntimeError("loaded model does not match {}: {}".format(where, "; ".join(diffs)))


def signature(model):
    """Structural signature: types, entity sets, actions, and enums."""
    if isinstance(model, BuiltInModel):
        return _module_signature(
            model._base,
            multi_datastream=model.multi_datastream,
            data_array=model.data_array,
            actuation=model.actuation,
        )
    if hasattr(model, "ENTITY_SETS"):
        return _module_signature(
            model,
            multi_datastream=None,
            data_array=None,
            actuation=None,
        )
    return _csdl_signature(model)


def differences(left, right):
    """Human-readable differences. Empty when the signatures are equal."""
    messages = []
    messages.extend(_set_diff("entity set", left["sets"], right["sets"]))
    messages.extend(_set_diff("action", left["actions"], right["actions"]))
    messages.extend(_set_diff("enum", left["enums"], right["enums"]))
    messages.extend(_type_diff(left["types"], right["types"]))
    return messages[:8]


def _module_signature(module, multi_datastream, data_array, actuation):
    types = {}
    for cls in _classes(module):
        name = _qualified(cls)
        if _hidden_type(_csdl_name(cls), multi_datastream, actuation):
            continue
        types[name] = _class_shape(cls, multi_datastream, actuation)
    sets = []
    for wire, cls in _entity_sets(module):
        if _hidden_set(wire, multi_datastream, actuation):
            continue
        sets.append((wire, _csdl_name(cls)))
    actions = _module_actions(module, data_array)
    return {
        "types": types,
        "sets": frozenset(sets),
        "actions": frozenset(actions),
        "enums": frozenset(_module_enums(module)),
    }


def _csdl_signature(model):
    types = {}
    for item in model.types.values():
        types[item.qualified] = (
            item.kind,
            bool(item.open_type),
            tuple(item.keys),
            tuple(sorted(
                (prop.name, _norm(prop.edm), bool(prop.nullable))
                for prop in item.properties
            )),
            tuple(sorted(
                (nav.name, _short(nav.target), bool(nav.collection), bool(nav.containment))
                for nav in item.navigations
            )),
        )
    sets = tuple(
        (name, _short(type_name))
        for name, type_name in model.entity_sets
    )
    actions = []
    for operation in model.action_list:
        actions.append(_operation_shape(
            operation.name,
            operation.bound,
            operation.parameters,
            operation.return_type,
        ))
    enums = []
    for enum in model.enums.values():
        qualified = enum.name
        if enum.namespace:
            qualified = "{}.{}".format(enum.namespace, enum.name)
        members = tuple(sorted((name, value) for name, value in enum.members))
        enums.append((qualified, members))
    return {
        "types": types,
        "sets": frozenset(sets),
        "actions": frozenset(actions),
        "enums": frozenset(enums),
    }


def _classes(module):
    types = getattr(module, "TYPES", {})
    seen = set()
    classes = []
    for cls in types.values():
        if not isinstance(cls, type) or cls in seen:
            continue
        if not hasattr(cls, "__properties__"):
            continue
        seen.add(cls)
        classes.append(cls)
    return classes


def _hidden_type(name, multi_datastream, actuation):
    if multi_datastream is False and name == "MultiDatastream":
        return True
    return actuation is False and name in _ACTUATION_TYPES


def _hidden_set(wire, multi_datastream, actuation):
    if multi_datastream is False and wire == "MultiDatastreams":
        return True
    return actuation is False and wire in _ACTUATION_SETS


def _class_shape(cls, multi_datastream, actuation):
    kind = "entity" if getattr(cls, "__is_entity__", False) else "complex"
    keys = tuple(getattr(cls, "__key_names__", ()) or ())
    props = tuple(sorted(
        (spec.wire, _norm(spec.edm), bool(spec.nullable))
        for spec in cls.__properties__
    ))
    navs = []
    for nav in cls.__navigations__:
        target = _short(nav.target)
        if _hidden_type(target, multi_datastream, actuation):
            continue
        navs.append((nav.wire, target, bool(nav.collection), bool(nav.containment)))
    return (kind, bool(getattr(cls, "__open_type__", False)), keys, props, tuple(sorted(navs)))


def _entity_sets(module):
    for value in module.ENTITY_SETS.values():
        yield value[0], value[1]


def _module_actions(module, data_array):
    from frost_sta_client.runtime.builtin import CREATE_OBSERVATIONS

    actions = []
    for item in getattr(module, "ACTIONS", ()):
        if data_array is False and item.name == "CreateObservations":
            continue
        actions.append(_operation_shape(item.name, item.bound, item.parameters, item.return_type))
    names = {item[0] for item in actions}
    if data_array and "CreateObservations" not in names:
        actions.append(_operation_shape(
            CREATE_OBSERVATIONS.name,
            CREATE_OBSERVATIONS.bound,
            CREATE_OBSERVATIONS.parameters,
            CREATE_OBSERVATIONS.return_type,
        ))
    return actions


def _module_enums(module):
    enums = []
    for value in vars(module).values():
        if not isinstance(value, type) or not issubclass(value, Enum):
            continue
        if not hasattr(value, "__csdl_name__"):
            continue
        qualified = _qualified(value)
        members = tuple(sorted((member.name, member.value) for member in value))
        enums.append((qualified, members))
    return enums


def _operation_shape(name, bound, parameters, return_type):
    params = tuple(sorted(
        (param.name, _norm(param.edm), bool(param.nullable))
        for param in parameters
    ))
    returned = None if return_type is None else _norm(return_type)
    return (name, bool(bound), params, returned)


def _set_diff(label, left, right):
    left_names = {_label_of(item) for item in left}
    right_names = {_label_of(item) for item in right}
    messages = []
    for name in sorted(left_names - right_names):
        messages.append("{} {}".format(label, name))
    for name in sorted(right_names - left_names):
        messages.append("{} {}".format(label, name))
    common = left_names & right_names
    left_by_name = {_label_of(item): item for item in left}
    right_by_name = {_label_of(item): item for item in right}
    for name in sorted(common):
        if left_by_name[name] != right_by_name[name]:
            messages.append("{} {}".format(label, name))
    return messages


def _type_diff(left, right):
    messages = []
    for name in sorted(set(left) | set(right)):
        if name not in left or name not in right or left[name] != right[name]:
            messages.append("type {}".format(_short(name)))
    return messages


def _label_of(item):
    return item[0]


def _qualified(cls):
    name = _csdl_name(cls)
    namespace = getattr(cls, "__namespace__", "") or ""
    if namespace:
        return "{}.{}".format(namespace, name)
    return name


def _csdl_name(cls):
    return getattr(cls, "__csdl_name__", None) or cls.__name__


def _short(name):
    text = (name or "").strip()
    if text.startswith("Collection(") and text.endswith(")"):
        return text
    return text.rsplit(".", 1)[-1]


def _norm(edm):
    text = (edm or "").strip()
    if text.startswith("Collection(") and text.endswith(")"):
        inner = text[len("Collection("):-1].strip()
        return "Collection({})".format(_norm(inner))
    if text.startswith("Edm."):
        return text
    return text.rsplit(".", 1)[-1]
