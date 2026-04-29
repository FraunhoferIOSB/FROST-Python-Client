import argparse
import os
import re
from typing import Dict, List, Optional, Tuple

from frost_sta_client.odata_codegen.generator import generate_from_url

# Map entity names to model file names
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

# Map entity names to DAO module filenames where they differ from model filenames
DAO_FILE_MAP: Dict[str, Optional[str]] = {
    'FeatureOfInterest': 'features_of_interest',
}

# Map entity names to DAO class names where they differ from the default <Singular>Dao
DAO_CLASS_MAP: Dict[str, Optional[str]] = {
    'FeatureOfInterest': 'FeaturesOfInterestDao',
}

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def write_entity_base(model_dir: str) -> None:
    """Write a base Entity class used by generated datamodel classes and wrappers."""
    path = os.path.join(model_dir, 'entity.py')
    lines = [
        "from abc import ABC",
        "from typing import TYPE_CHECKING, Any",
        "if TYPE_CHECKING:",
        "    from frost_sta_client.service.sensorthingsservice import SensorThingsService",
        "",
        "class Entity(ABC):",
        "    \"\"\"Base class for entities with id, self_link and service propagation.\"\"\"",
        "    def __init__(self, id=None, self_link: str = '', service=None, **kwargs: Any):",
        "        # Accept **kwargs to stay forward-compatible with generated models.",
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
        "        if value is None:",
        "            self._service = None",
        "            return",
        "        try:",
        "            from frost_sta_client.service.sensorthingsservice import SensorThingsService as STS",
        "        except Exception:",
        "            STS = None",
        "        if STS is not None and isinstance(value, STS):",
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

def _to_snake(name: str) -> str:
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def write_wrapper(model_dir: str, singular: str, relations: List[str]) -> None:
    """No-op: Wrapper functionality is now embedded in the generated datamodel classes.
    The compatibility import modules under frost_sta_client/model are provided statically.
    """
    return
    
def write_model_init(model_dir: str, entities: List[str]) -> None:
    """Write a minimal __init__ for frost_sta_client.model to avoid circular imports."""
    path = os.path.join(model_dir, '__init__.py')
    parts = [
        "# Auto-generated by install_model: keep package lightweight to avoid circular imports.",
        "# Entity wrappers are imported on-demand by user code and utils.class_from_string.",
        ""
    ]
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

    # 1) Generate datamodel module (will fallback to metadata.xml if OData unavailable)
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

    # 4) Write __init__.py to keep package lightweight
    write_model_init(model_dir, entities)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
