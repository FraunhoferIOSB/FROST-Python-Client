"""One GeoJSON codec for every geography and geometry property."""

import geojson

_GEO_CLASSES = {
    "Point": geojson.Point,
    "LineString": geojson.LineString,
    "Polygon": geojson.Polygon,
    "MultiPoint": geojson.MultiPoint,
    "MultiLineString": geojson.MultiLineString,
    "MultiPolygon": geojson.MultiPolygon,
    "GeometryCollection": geojson.GeometryCollection,
}

_ALLOWED = {
    "Edm.Geography": set(_GEO_CLASSES),
    "Edm.Geometry": set(_GEO_CLASSES),
    "Edm.GeographyPoint": {"Point"},
    "Edm.GeometryPoint": {"Point"},
    "Edm.GeographyLineString": {"LineString"},
    "Edm.GeometryLineString": {"LineString"},
    "Edm.GeographyPolygon": {"Polygon"},
    "Edm.GeometryPolygon": {"Polygon"},
    "Edm.GeographyMultiPoint": {"MultiPoint"},
    "Edm.GeometryMultiPoint": {"MultiPoint"},
    "Edm.GeographyMultiLineString": {"MultiLineString"},
    "Edm.GeometryMultiLineString": {"MultiLineString"},
    "Edm.GeographyMultiPolygon": {"MultiPolygon"},
    "Edm.GeometryMultiPolygon": {"MultiPolygon"},
    "Edm.GeographyCollection": {"GeometryCollection"},
    "Edm.GeometryCollection": {"GeometryCollection"},
}


def is_geography(edm):
    if not isinstance(edm, str):
        return False
    return edm.startswith("Edm.Geography") or edm.startswith("Edm.Geometry")


def is_geo_media(value):
    if not isinstance(value, str):
        return False
    lowered = value.lower().replace(" ", "")
    return "application/geo+json" in lowered or "application/vnd.geo+json" in lowered


def coerce_geometry(value, edm, property_name):
    """Return a geojson geometry accepted by the declared type.

    A dict with ``type`` and coordinates is turned into the same class a read
    would produce.
    """
    if isinstance(value, geojson.GeoJSON):
        geom = value
    elif isinstance(value, dict) and "type" in value:
        geom = _from_mapping(value, property_name)
    else:
        raise ValueError("{} should be a GeoJSON geometry".format(property_name))
    type_name = geom.get("type") if isinstance(geom, dict) else None
    allowed = _allowed_for(edm)
    if type_name not in allowed:
        raise ValueError("{} does not accept {}".format(property_name, type_name))
    return geom


def geometry_to_json(value):
    """Plain GeoJSON object for a geometry."""
    type_name = value.get("type")
    if type_name == "GeometryCollection":
        return {"type": type_name, "geometries": value.get("geometries")}
    return {"type": type_name, "coordinates": value.get("coordinates")}


def _allowed_for(edm):
    if edm in _ALLOWED:
        return _ALLOWED[edm]
    if isinstance(edm, str) and (edm.startswith("Edm.Geography") or edm.startswith("Edm.Geometry")):
        return set(_GEO_CLASSES)
    return set()


def _from_mapping(value, property_name):
    type_name = value.get("type")
    cls = _GEO_CLASSES.get(type_name)
    if cls is None:
        raise ValueError("{} should be a GeoJSON geometry".format(property_name))
    if type_name == "GeometryCollection":
        return cls(value.get("geometries"), validate=False)
    return cls(value.get("coordinates"), validate=False)
