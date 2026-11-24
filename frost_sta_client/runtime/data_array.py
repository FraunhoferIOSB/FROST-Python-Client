"""Data-array documents.

Components are a sequence, and that sequence is the column order. None stays
in its column. Exactly one of Datastream or MultiDatastream is written, as a
key reference. A set is rejected because it has no order.
"""

from collections.abc import Sequence
from enum import Enum

from frost_sta_client.runtime.control import key_reference, parse_key
from frost_sta_client.runtime.values import wire_time

_COMPONENT_ALIASES = {
    "phenomenon_time": "phenomenonTime",
    "result_time": "resultTime",
    "result_quality": "resultQuality",
    "valid_time": "validTime",
    "feature_of_interest": "FeatureOfInterest/id",
}


class DataArrayValue:
    """One data array bound to a Datastream or a MultiDatastream."""

    class Property(Enum):
        ID = "id"
        PHENOMENON_TIME = "phenomenonTime"
        RESULT = "result"
        RESULT_TIME = "resultTime"
        RESULT_QUALITY = "resultQuality"
        VALID_TIME = "validTime"
        PARAMETERS = "parameters"
        FEATURE_OF_INTEREST = "FeatureOfInterest/id"

    def __init__(self):
        self._components = None
        self.datastream = None
        self.multi_datastream = None
        self.data_array = []

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, value):
        if value is None:
            self._components = None
            return
        if isinstance(value, (str, bytes, set, frozenset)) or not isinstance(value, Sequence):
            raise TypeError("components must be a list of property paths")
        self._components = [_component_path(item) for item in value]

    def add_observation(self, observation):
        if not self._components:
            raise ValueError("components must be set")
        row = [_cell(observation, path) for path in self._components]
        self.data_array.append(row)
        return row

    def to_json(self, service):
        parent_name, parent = _single_parent(self)
        body = {
            parent_name: key_reference(parent, service),
            "components": list(self._components or []),
            "dataArray": [list(row) for row in self.data_array],
        }
        return body


class DataArrayDocument:
    """The body of CreateObservations."""

    def __init__(self):
        self.value = []

    def add_data_array_value(self, value):
        if not isinstance(value, DataArrayValue):
            raise TypeError("value should be a DataArrayValue")
        self.value.append(value)
        return value

    def to_json(self, service):
        return [item.to_json(service) for item in self.value]

    def observations_from(self, payload, observation_class, service):
        """Turn the action result into observations with key and self link."""
        if not isinstance(payload, list):
            raise ValueError("CreateObservations result should be a list of entity URLs")
        created = []
        for item in payload:
            if not isinstance(item, str):
                raise ValueError("CreateObservations result should be a list of entity URLs")
            observation = observation_class()
            observation.self_link = item
            observation.id = parse_key(item, observation_class.__key_type__)
            observation.set_service(service)
            created.append(observation)
        return created


def _component_path(item):
    if isinstance(item, DataArrayValue.Property):
        return item.value
    if isinstance(item, str) and item:
        return _COMPONENT_ALIASES.get(item, item)
    raise TypeError("component must be a string path or a DataArrayValue.Property")


def _single_parent(value):
    has_datastream = value.datastream is not None
    has_multi = value.multi_datastream is not None
    if has_datastream == has_multi:
        raise ValueError("exactly one of datastream or multi_datastream is required")
    if has_datastream:
        if value.datastream.id is None:
            raise ValueError("datastream requires an id")
        return "Datastream", value.datastream
    if value.multi_datastream.id is None:
        raise ValueError("multi_datastream requires an id")
    return "MultiDatastream", value.multi_datastream


def _cell(observation, path):
    if path == "id":
        return observation.id
    if path == "phenomenonTime":
        return wire_time(observation.phenomenon_time)
    if path == "result":
        return observation.result
    if path == "resultTime":
        return wire_time(observation.result_time)
    if path == "resultQuality":
        return observation.result_quality
    if path == "validTime":
        return wire_time(observation.valid_time)
    if path == "parameters":
        value = observation.parameters
        if hasattr(value, "to_json"):
            return value.to_json(None)
        return value
    if path == "FeatureOfInterest/id":
        feature = observation.feature_of_interest
        if feature is None or feature.id is None:
            return None
        return feature.id
    raise ValueError("unknown data array component {}".format(path))
