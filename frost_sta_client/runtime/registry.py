"""Type registry filled by generated classes."""

import sys

REGISTRY = {}
AMBIGUOUS = object()
_MISSING = object()


def register_type(short, qualified, cls):
    """Register a class under its CSDL name.

    A short name that belongs to two namespaces is marked ambiguous so a
    lookup cannot silently pick one of them. The qualified name stays unique.
    """
    if qualified:
        REGISTRY[qualified] = cls
    current = REGISTRY.get(short)
    if current is None:
        REGISTRY[short] = cls
    elif current is not cls:
        REGISTRY[short] = AMBIGUOUS


def unwrap_type(edm):
    """Return the type name inside a Collection(...), or the name itself."""
    text = (edm or "").strip()
    if text.startswith("Collection(") and text.endswith(")"):
        text = text[len("Collection("):-1].strip()
    if text.startswith("self."):
        text = text[len("self."):]
    return text


def resolve(edm):
    """Return a generated class for an EDM type name, or None."""
    return _lookup(REGISTRY, unwrap_type(edm))


def resolve_declared(edm, owner):
    """Resolve a type from the model that declared ``owner``, then the registry.

    Two loaded copies of the same CSDL name stay on the module that defined
    the instance. A short name shared by two types in that module does not
    fall through to another copy.
    """
    name = unwrap_type(edm)
    types = _types_of(owner)
    if types is not None:
        found = _lookup_map(types, name)
        if found is not _MISSING:
            return None if found is AMBIGUOUS else found
    return resolve(name)


def _types_of(owner):
    if owner is None:
        return None
    direct = getattr(owner, "TYPES", None)
    if isinstance(direct, dict):
        return direct
    cls = owner if isinstance(owner, type) else type(owner)
    module = sys.modules.get(getattr(cls, "__module__", ""))
    types = getattr(module, "TYPES", None) if module is not None else None
    if isinstance(types, dict):
        return types
    service = getattr(owner, "service", None)
    model = getattr(service, "model", None) if service is not None else None
    types = getattr(model, "TYPES", None) if model is not None else None
    if isinstance(types, dict):
        return types
    return None


def _lookup(mapping, name):
    found = _lookup_map(mapping, name)
    if found is _MISSING or found is AMBIGUOUS:
        return None
    return found


def _lookup_map(mapping, name):
    if not name or name.startswith("Edm.") or mapping is None:
        return _MISSING
    if name in mapping:
        return mapping[name]
    short = name.rsplit(".", 1)[-1]
    if short != name and short in mapping:
        return mapping[short]
    return _MISSING


def is_collection(edm):
    return isinstance(edm, str) and edm.startswith("Collection(") and edm.endswith(")")
