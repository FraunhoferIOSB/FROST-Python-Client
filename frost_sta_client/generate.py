"""Generate Python types from a CSDL ``$metadata`` document.

The command is::

    python -m frost_sta_client.generate --url http://example/service --out my_model

``--url`` is the service root whose ``$metadata`` is read. ``--out`` is the
directory the program loads with ``load_model`` or ``SensorThingsService.open``.
``--xml`` reads a local document instead of a service root. The written module
declares types, navigations, enums, actions, and action parameters. It does
not copy equality, serialization, or setters per type.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from frost_sta_client.runtime.csdl import parse_csdl
from frost_sta_client.runtime.names import ident, snake

_PROTECTED = {
    "create",
    "update",
    "patch",
    "delete",
    "execute",
    "join",
    "invoke",
    "advertises",
    "live_model",
    "url",
    "write_prefix",
    "id",
    "service",
    "self_link",
}


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] not in ("generate", "-h", "--help"):
        argv = ["generate", *argv]
    parser = argparse.ArgumentParser(prog="frost-client")
    sub = parser.add_subparsers(dest="command", required=True)
    generate = sub.add_parser("generate", help="read $metadata and write a Python model")
    generate.add_argument("--url", help="service root whose /$metadata document is read")
    generate.add_argument("--xml", help="CSDL file to read instead of --url")
    generate.add_argument("--out", required=True, help="directory of the generated package")
    generate.add_argument("--username", help="basic-auth user for --url")
    generate.add_argument("--password", help="basic-auth password for --url")
    args = parser.parse_args(argv)
    if args.command == "generate":
        if bool(args.url) == bool(args.xml):
            parser.error("generate requires exactly one of --url or --xml")
        if args.url:
            auth = None
            if args.username is not None or args.password is not None:
                auth = (args.username or "", args.password or "")
            xml_text = fetch_metadata(args.url, auth=auth)
            service_root = args.url.rstrip("/")
        else:
            xml_text = Path(args.xml).read_text(encoding="utf-8")
            service_root = None
        write_package(xml_text, args.out, service_root=service_root)
    return 0


def fetch_metadata(url, auth=None):
    """GET ``$metadata`` of the service root the caller named.

    No other root is tried. A SensorThings ``/v1.1`` root that does not
    publish ``$metadata`` fails here; the caller passes the root that has it.
    """
    import requests

    root = url.rstrip("/")
    response = requests.get(root + "/$metadata", timeout=60, auth=auth)
    if response.status_code != 200 or not (response.text or "").lstrip().startswith("<"):
        response.raise_for_status()
        raise ValueError("no CSDL $metadata at {}".format(root))
    return response.text


def write_package(xml_text, out_dir, service_root=None):
    model = parse_csdl(xml_text)
    digest = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files = render(model, {"service_root": service_root, "metadata_sha256": digest})
    for name, content in files.items():
        (out / name).write_text(content, encoding="utf-8")
    return model


def render(model, source):
    """Return the generated package files for a parsed model."""
    class_names = {}
    used_class_names = set()
    short_counts = {}
    for enum in model.enums.values():
        short_counts[enum.name] = short_counts.get(enum.name, 0) + 1
    for item in model.types.values():
        short_counts[item.name] = short_counts.get(item.name, 0) + 1
    for enum in model.enums.values():
        class_names[("enum", _enum_key(enum))] = _unique_name(
            enum.name, enum.namespace, short_counts, used_class_names
        )
    for item in model.types.values():
        class_names[("type", item.qualified)] = _unique_name(
            item.name, item.namespace, short_counts, used_class_names
        )
    lines = [
        '"""Generated from a CSDL metadata document. Do not edit by hand.',
        "",
        "Regenerate with frost_sta_client.generate. Equality, JSON, and",
        "attribute access are implemented once on the runtime base classes.",
        '"""',
        "",
    ]
    imports = ["from frost_sta_client.runtime.entity import ComplexType, Entity, NavigationSpec, PropertySpec"]
    if model.enums:
        imports.insert(0, "from frost_sta_client.runtime.enums import RegisteredEnum")
    if model.action_list or model.function_list:
        imports.append("from frost_sta_client.runtime.specs import OperationSpec, ParameterSpec")
    if _has_ambiguous_short_name(model):
        imports.append("from frost_sta_client.runtime.registry import AMBIGUOUS")
    lines.extend(imports)
    lines.append("")
    lines.append("")
    for enum in model.enums.values():
        lines.extend(_render_enum(enum, class_names[("enum", _enum_key(enum))]))
        lines.append("")
        lines.append("")
    for item in model.types.values():
        if item.kind != "complex":
            continue
        lines.extend(_render_type(item, None, class_names[("type", item.qualified)]))
        lines.append("")
        lines.append("")
    set_for_type = {}
    for set_name, type_name in model.entity_sets:
        try:
            found = model.type_named(type_name)
        except KeyError:
            continue
        set_for_type.setdefault(found.qualified, set_name)
    for item in model.types.values():
        if item.kind != "entity":
            continue
        lines.extend(_render_type(item, set_for_type.get(item.qualified), class_names[("type", item.qualified)]))
        lines.append("")
        lines.append("")
    lines.extend(_render_type_map(model, class_names))
    lines.append("")
    lines.extend(_render_tables(model, class_names, set_for_type))
    model_py = "\n".join(lines).rstrip() + "\n"
    init_py = _render_init(model, class_names)
    source_json = json.dumps({
        "service_root": source.get("service_root"),
        "metadata_sha256": source.get("metadata_sha256"),
        "note": "Generated from this metadata document. Behavior is not copied per type.",
    }, indent=2, sort_keys=True) + "\n"
    return {"model.py": model_py, "__init__.py": init_py, "SOURCE.json": source_json}


def _has_ambiguous_short_name(model):
    counts = {}
    for enum in model.enums.values():
        counts[enum.name] = counts.get(enum.name, 0) + 1
    for item in model.types.values():
        counts[item.name] = counts.get(item.name, 0) + 1
    return any(count > 1 for count in counts.values())


def _render_type_map(model, class_names):
    rows = []
    for enum in model.enums.values():
        rows.append((_enum_key(enum), enum.name, class_names[("enum", _enum_key(enum))]))
    for item in model.types.values():
        rows.append((item.qualified, item.name, class_names[("type", item.qualified)]))
    counts = {}
    for _qualified, short, _class_name in rows:
        counts[short] = counts.get(short, 0) + 1
    lines = ["TYPES = {"]
    for qualified, short, class_name in rows:
        lines.append("    {}: {},".format(repr(qualified), class_name))
        if counts[short] == 1 and short != qualified:
            lines.append("    {}: {},".format(repr(short), class_name))
    for short in sorted(name for name, count in counts.items() if count > 1):
        lines.append("    {}: AMBIGUOUS,".format(repr(short)))
    lines.append("}")
    return lines


def _enum_key(enum):
    if enum.namespace:
        return "{}.{}".format(enum.namespace, enum.name)
    return enum.name


def _unique_name(label, namespace, counts, used):
    if counts.get(label, 0) > 1 and namespace:
        base = ident("{}_{}".format(namespace, label))
    else:
        base = ident(label)
    name = base
    while name in used:
        name = name + "_type"
    used.add(name)
    return name


def _render_enum(enum, class_name):
    lines = [
        "class {}(RegisteredEnum):".format(class_name),
        '    """Generated enum {}."""'.format(enum.name),
        "",
        "    __csdl_name__ = {}".format(repr(enum.name)),
        "    __namespace__ = {}".format(repr(enum.namespace)),
    ]
    if not enum.members:
        lines.append("    pass")
        return lines
    for name, value in enum.members:
        lines.append("    {} = {}".format(ident(name), repr(value)))
    return lines


def _render_type(item, entity_set, class_name):
    base = "ComplexType" if item.kind == "complex" else "Entity"
    properties, navigations = _names(item)
    lines = [
        "class {}({}):".format(class_name, base),
        '    """Generated {} {}."""'.format(item.kind, item.name),
        "",
        "    __csdl_name__ = {}".format(repr(item.name)),
        "    __namespace__ = {}".format(repr(item.namespace)),
        "    __entity_set__ = {}".format(repr(entity_set)),
        "    __key_names__ = {}".format(repr(tuple(item.keys) if item.kind == "entity" else ())),
        "    __key_types__ = {}".format(repr(dict(item.key_types) if item.kind == "entity" else {})),
        "    __key_name__ = {}".format(repr(item.key if item.kind == "entity" else None)),
        "    __key_type__ = {}".format(repr(item.key_type or "Edm.String")),
        "    __open_type__ = {}".format(bool(item.open_type)),
        "    __is_entity__ = {}".format(item.kind == "entity"),
    ]
    lines.append("    __properties__ = (")
    if not properties:
        lines[-1] = "    __properties__ = ()"
    else:
        for prop, python_name in properties:
            lines.append("        PropertySpec(")
            lines.append("            {},".format(repr(prop.name)))
            lines.append("            {},".format(repr(python_name)))
            lines.append("            {},".format(repr(prop.edm)))
            lines.append("            nullable={},".format(bool(prop.nullable)))
            lines.append("        ),")
        lines.append("    )")
    lines.append("    __navigations__ = (")
    if not navigations:
        lines[-1] = "    __navigations__ = ()"
    else:
        for nav, python_name in navigations:
            lines.append("        NavigationSpec(")
            lines.append("            {},".format(repr(nav.name)))
            lines.append("            {},".format(repr(python_name)))
            lines.append("            {},".format(repr(nav.target)))
            lines.append("            collection={},".format(bool(nav.collection)))
            lines.append("            containment={},".format(bool(nav.containment)))
            lines.append("        ),")
        lines.append("    )")
    return lines


def _names(item):
    used = {"id", "service", "self_link"}
    properties = []
    for prop in item.properties:
        if len(item.keys) == 1 and prop.name == item.keys[0]:
            properties.append((prop, "id"))
            continue
        properties.append((prop, _take(snake(prop.name), used)))
    navigations = []
    for nav in item.navigations:
        navigations.append((nav, _take(snake(nav.name), used)))
    return properties, navigations


def _take(base, used):
    name = base or "field"
    if (not name.isidentifier()) or name in used:
        name = name + "_value"
        while name in used or not name.isidentifier():
            name = name + "_value"
    used.add(name)
    return name


def _render_tables(model, class_names, set_for_type):
    del set_for_type
    used = set(_PROTECTED)
    lines = ["ENTITY_SETS = {"]
    for set_name, type_name in model.entity_sets:
        py_name = _take(snake(set_name), used)
        try:
            found = model.type_named(type_name)
            class_name = class_names[("type", found.qualified)]
        except KeyError:
            class_name = ident(type_name.rsplit(".", 1)[-1])
        lines.append("    {}: ({}, {}),".format(repr(py_name), repr(set_name), class_name))
    lines.append("}")
    lines.append("")
    lines.extend(_render_operations("ACTIONS", model.action_list))
    lines.append("")
    lines.extend(_render_operations("FUNCTIONS", model.function_list))
    lines.append("")
    return lines


def _render_operations(label, operations):
    lines = ["{} = (".format(label)]
    for operation in operations:
        lines.append("    OperationSpec(")
        lines.append("        {},".format(repr(operation.name)))
        lines.append("        {},".format(bool(operation.bound)))
        if operation.parameters:
            lines.append("        parameters=(")
            for param in operation.parameters:
                lines.append(
                    "            ParameterSpec({name}, {edm}, nullable={nullable}),".format(
                        name=repr(param.name),
                        edm=repr(param.edm),
                        nullable=bool(param.nullable),
                    )
                )
            lines.append("        ),")
        if operation.return_type:
            lines.append("        return_type={},".format(repr(operation.return_type)))
        lines.append("    ),")
    lines.append(")")
    return lines


def _render_init(model, class_names):
    names = []
    for enum in model.enums.values():
        names.append(class_names[("enum", _enum_key(enum))])
    for item in model.types.values():
        names.append(class_names[("type", item.qualified)])
    lines = [
        '"""Generated model package."""',
        "",
        "from .model import (",
    ]
    for name in names:
        lines.append("    {},".format(name))
    lines.extend([
        "    ACTIONS,",
        "    ENTITY_SETS,",
        "    FUNCTIONS,",
        ")",
        "",
        "__all__ = [",
    ])
    for name in names + ["ACTIONS", "ENTITY_SETS", "FUNCTIONS"]:
        lines.append("    {},".format(repr(name)))
    lines.append("]")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
