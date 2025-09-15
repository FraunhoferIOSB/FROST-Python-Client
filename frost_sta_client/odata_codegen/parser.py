import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Tuple

EDMX_NS = "http://docs.oasis-open.org/odata/ns/edmx"
EDM_NS = "http://docs.oasis-open.org/odata/ns/edm"
NS = {"edmx": EDMX_NS, "edm": EDM_NS}

def _is_true(val: str) -> bool:
    return str(val).lower() in ("true", "1", "yes")

def _parse_type(type_str: str) -> Tuple[bool, str]:
    # Returns (is_collection, inner_type)
    if type_str.startswith("Collection(") and type_str.endswith(")"):
        return True, type_str[len("Collection("):-1]
    return False, type_str

def parse_metadata(xml_text: str) -> Dict[str, Any]:
    """Parse OData $metadata (CSDL) XML and return an in-memory model.

    Returns:
        {
            'entity_types': {
                'FQN': {
                    'name': str,
                    'namespace': str,
                    'keys': [str, ...],
                    'properties': [
                        {'name': str, 'type': str, 'nullable': bool}
                    ],
                    'navigation_properties': [
                        {'name': str, 'type': str, 'collection': bool}
                    ]
                }
            },
            'complex_types': { 'FQN': {...} },
            'enum_types': { 'FQN': {'name': str, 'namespace': str, 'members': [(name, value), ...]} },
            'entity_sets': { 'Name': 'FQN' },
            'type_defs': { 'FQN': {'name': str, 'namespace': str, 'underlying': str} }
        }
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"Invalid OData metadata XML: {e}")

    model: Dict[str, Any] = {
        "entity_types": {},
        "complex_types": {},
        "enum_types": {},
        "entity_sets": {},
        "type_defs": {},
    }

    schemas = root.findall("./edmx:DataServices/edm:Schema", NS)
    for schema in schemas:
        namespace = schema.attrib.get("Namespace", "Default")

        # EnumTypes
        for enum in schema.findall("edm:EnumType", NS):
            en_name = enum.attrib.get("Name")
            if not en_name:
                continue
            members: List[Tuple[str, int]] = []
            for mem in enum.findall("edm:Member", NS):
                mname = mem.attrib.get("Name")
                mval = mem.attrib.get("Value")
                try:
                    ival = int(mval) if mval is not None else None
                except Exception:
                    ival = None
                members.append((mname, ival))
            fqn = f"{namespace}.{en_name}"
            model["enum_types"][fqn] = {
                "name": en_name,
                "namespace": namespace,
                "members": members,
            }

        # TypeDefinitions (aliases for EDM types)
        for td in schema.findall("edm:TypeDefinition", NS):
            td_name = td.attrib.get("Name")
            underlying = td.attrib.get("UnderlyingType")
            if not td_name or not underlying:
                continue
            fqn = f"{namespace}.{td_name}"
            model["type_defs"][fqn] = {
                "name": td_name,
                "namespace": namespace,
                "underlying": underlying,
            }

        # ComplexTypes
        for cplx in schema.findall("edm:ComplexType", NS):
            c_name = cplx.attrib.get("Name")
            if not c_name:
                continue
            props: List[Dict[str, Any]] = []
            for p in cplx.findall("edm:Property", NS):
                pname = p.attrib.get("Name")
                ptype = p.attrib.get("Type", "Edm.String")
                pnull = _is_true(p.attrib.get("Nullable", "true"))
                props.append({"name": pname, "type": ptype, "nullable": pnull})
            fqn = f"{namespace}.{c_name}"
            model["complex_types"][fqn] = {
                "name": c_name,
                "namespace": namespace,
                "properties": props,
            }

        # EntityTypes
        for et in schema.findall("edm:EntityType", NS):
            e_name = et.attrib.get("Name")
            if not e_name:
                continue
            keys: List[str] = []
            key = et.find("edm:Key", NS)
            if key is not None:
                for pref in key.findall("edm:PropertyRef", NS):
                    kname = pref.attrib.get("Name")
                    if kname:
                        keys.append(kname)
            props: List[Dict[str, Any]] = []
            for p in et.findall("edm:Property", NS):
                pname = p.attrib.get("Name")
                ptype = p.attrib.get("Type", "Edm.String")
                pnull = _is_true(p.attrib.get("Nullable", "true"))
                props.append({"name": pname, "type": ptype, "nullable": pnull})
            navs: List[Dict[str, Any]] = []
            for np in et.findall("edm:NavigationProperty", NS):
                nname = np.attrib.get("Name")
                ntype = np.attrib.get("Type") or "Edm.EntityType"
                is_coll, inner = _parse_type(ntype)
                navs.append({"name": nname, "type": inner, "collection": is_coll})
            fqn = f"{namespace}.{e_name}"
            model["entity_types"][fqn] = {
                "name": e_name,
                "namespace": namespace,
                "keys": keys,
                "properties": props,
                "navigation_properties": navs,
            }

        # EntityContainer -> EntitySets
        for container in schema.findall("edm:EntityContainer", NS):
            for eset in container.findall("edm:EntitySet", NS):
                es_name = eset.attrib.get("Name")
                es_type = eset.attrib.get("EntityType")
                if es_name and es_type:
                    model["entity_sets"][es_name] = es_type

    return model
