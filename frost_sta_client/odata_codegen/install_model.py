import argparse
import importlib
import os
import sys
from typing import Dict, List, Optional, Tuple

from frost_sta_client.odata_codegen.generator import generate_from_url

ENTITY_FILE_MAP: Dict[str, Optional[str]] = {
    'Actuator': 'actuator',
    'Datastream': 'datastream',
    'FeatureOfInterest': 'feature_of_interest',
    'HistoricalLocation': 'historical_location',
    'Location': 'location',
    'MultiDatastream': 'multi_datastream',
    'Observation': 'observation',
    'ObservedProperty': 'observedproperty',
    'Sensor': 'sensor',
    'Task': 'task',
    'TaskingCapability': 'tasking_capability',
    'Thing': 'thing',
    # Not materialized as entity modules:
    'UnitOfMeasurement': None,
    'EntityList': None,
}

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_entity_base(model_dir: str) -> None:
    path = os.path.join(model_dir, 'entity.py')
    lines = [
        "from abc import ABC",
        "from frost_sta_client.service.sensorthingsservice import SensorThingsService",
        "",
        "class Entity(ABC):",
        "    \"\"\"Base class for entities with id, self_link and service propagation.\"\"\"",
        "    def __init__(self, id=None, self_link='', service=None):",
        "        self.id = id",
        "        self.self_link = self_link",
        "        self.service = service",
        "",
        "    @property",
        "    def id(self):",
        "        return self._id",
        "",
        "    @id.setter",
        "    def id(self, value):",
        "        if value is None:",
        "            self._id = None",
        "            return",
        "        if isinstance(value, int) or isinstance(value, str):",
        "            self._id = value",
        "            return",
        "        raise ValueError('id of entity should be of type int or str!')",
        "",
        "    @property",
        "    def self_link(self):",
        "        return self._self_link",
        "",
        "    @self_link.setter",
        "    def self_link(self, value):",
        "        if not isinstance(value, str):",
        "            raise ValueError('self_link should be of type str!')",
        "        self._self_link = value",
        "",
        "    @property",
        "    def service(self):",
        "        return self._service",
        "",
        "    @service.setter",
        "    def service(self, value):",
        "        if value is None or isinstance(value, SensorThingsService):",
        "            self._service = value",
        "            return",
        "        raise ValueError('service should be of type SensorThingsService')",
        "",
        "    def set_service(self, service):",
        "        if self.service != service:",
        "            self.service = service",
        "            self.ensure_service_on_children(service)",
        "",
        "    @property",
        "    def IOT_COUNT(self):",
        "        return 'iot.count'",
        "",
        "    @property",
        "    def AT_IOT_COUNT(self):",
        "        return '@iot.count'",
        "",
        "    @property",
        "    def IOT_NAVIGATION_LINK(self):",
        "        return 'iot.navigationLink'",
        "",
        "    @property",
        "    def AT_IOT_NAVIGATION_LINK(self):",
        "        return '@iot.navigationLink'",
        "",
        "    @property",
        "    def IOT_NEXT_LINK(self):",
        "        return 'iot.nextLink'",
        "",
        "    @property",
        "    def AT_IOT_NEXT_LINK(self):",
        "        return '@iot.nextLink'",
        "",
        "    @property",
        "    def IOT_SELF_LINK(self):",
        "        return 'iot.selfLink'",
        "",
        "    @property",
        "    def AT_IOT_SELF_LINK(self):",
        "        return '@iot.selfLink'",
        "",
        "    def __eq__(self, other):",
        "        if other is None:",
        "            return False",
        "        if not isinstance(other, type(self)):",
        "            return False",
        "        if id(self) == id(other):",
        "            return True",
        "        if self.id is not None and other.id is not None:",
        "            if self.id != other.id:",
        "                return False",
        "        return True",
        "",
        "    def __ne__(self, other):",
        "        return not self == other",
        "",
        "    def __getstate__(self):",
        "        data = {}",
        "        if self.id is not None and self.id != '':",
        "            data['@iot.id'] = self.id",
        "        return data",
        "",
        "    def __setstate__(self, state):",
        "        self.id = state.get('@iot.id', None)",
        "        self.self_link = state.get('@iot.selfLink', '')",
        "",
            ]
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')

def load_entity_types():
    from frost_sta_client.model.ext.entity_type import EntityTypes
    return EntityTypes

def find_rel_info(entity_types: Dict[str, Dict[str, str]], name: str) -> Optional[Tuple[str, Dict[str, str]]]:
    if name in entity_types:
        return name, entity_types[name]
    # Try by plural
    for k, v in entity_types.items():
        if v.get('plural') == name:
            return k, v
    return None

def write_wrapper(model_dir: str, singular: str, relations: List[str]) -> None:
    file_name = ENTITY_FILE_MAP.get(singular)
    if not file_name:
        return
    path = os.path.join(model_dir, f"{file_name}.py")
    imports: List[str] = []
    imports.append("from frost_sta_client.generated.odata import datamodel as _mdl")
    imports.append("from frost_sta_client.model.ext import entity_type as _etype")
    # DAO imports
    dao_mod = file_name
    dao_class = singular + 'Dao'
    imports.append(f"from frost_sta_client.dao.{dao_mod} import {dao_class}")
    imports.append("")
    body: List[str] = []
    body.append(f"class {singular}(_mdl.{singular}):")
    body.append(f"    \"\"\"Compatibility wrapper around code-generated {singular} to provide DAO accessors.\"\"\"")
    body.append("    def get_dao(self, service):")
    body.append(f"        return {dao_class}(service)")
    body.append("")
    # Navigation accessors
    etypes = load_entity_types()
    for rel in relations:
        info = find_rel_info(etypes, rel)
        if not info:
            continue
        rel_singular, rel_meta = info
        plural = rel_meta.get('plural', rel + 's')
        method = plural.lower()
        accessor = f"get_{method}"
        body.append(f"    def {accessor}(self):")
        body.append(f"        result = self.service.{method}()")
        body.append("        result.parent = self")
        body.append("        return result")
        body.append("")
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(imports + body) + '\n')

def write_model_init(model_dir: str, entities: List[str]) -> None:
    path = os.path.join(model_dir, '__init__.py')
    parts = [
        "# Auto-generated by install_model to expose model submodules for class resolution",
    ]
    # Import submodules so they are present in sys.modules (used by utils.class_from_string)
    subs: List[str] = []
    for singular in entities:
        mod = ENTITY_FILE_MAP.get(singular)
        if mod:
            subs.append(mod)
    if subs:
        joined = ', '.join(subs)
        parts.append(f"from frost_sta_client.model import {joined}")
    parts.append("")
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(parts) + '\n')

def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Generate and install OData model into frost_sta_client/model')
    parser.add_argument('--url', '-u', required=True, help='Base URL of FROST-Server (e.g., http://localhost:8080/FROST-Server)')
    parser.add_argument('--username', help='Basic auth username', default=None)
    parser.add_argument('--password', help='Basic auth password', default=None)
    parser.add_argument('--out', '-o', default='frost_sta_client/generated/odata', help='Output dir for generated datamodel module')
    parser.add_argument('--module', '-m', default='datamodel', help='Module name for generated file (default: datamodel)')
    args = parser.parse_args(argv)

    auth = None
    if args.username is not None:
        auth = (args.username, args.password or '')

    # 1) Generate datamodel module
    ensure_dir(args.out)
    generate_from_url(args.url, args.out, args.module, auth=auth)

    # 2) Create model files (entity base + wrappers)
    model_dir = os.path.join('frost_sta_client', 'model')
    ensure_dir(model_dir)
    write_entity_base(model_dir)

    # 3) Build wrappers for each known entity
    from frost_sta_client.model.ext.entity_type import EntityTypes
    entities = [k for k in EntityTypes.keys() if ENTITY_FILE_MAP.get(k)]
    for singular in entities:
        relations = EntityTypes[singular].get('relations_list', [])
        write_wrapper(model_dir, singular, relations)

    # 4) Write __init__.py to preload submodules
    write_model_init(model_dir, entities)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
