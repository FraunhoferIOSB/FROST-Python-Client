"""The four built-in SensorThings models.

An empty model location uses one of these. ``extensions`` is
``(multi_datastream, data_array)``. Both flags default to on.
"""

from frost_sta_client.runtime.specs import OperationSpec

DATA_ARRAY_CONFORMANCE = (
    "http://www.opengis.net/spec/iot_sensing/1.1/req/data-array/data-array"
)
MULTIDATASTREAM_CONFORMANCE = (
    "http://www.opengis.net/spec/iot_sensing/1.1/req/multi-datastream"
)

CREATE_OBSERVATIONS = OperationSpec(
    "CreateObservations",
    bound=False,
    parameters=(),
    return_type="Collection(Edm.String)",
)


class BuiltInModel:
    """One combination of MultiDatastream and Data Array over the shipped types."""

    def __init__(self, multi_datastream, data_array):
        self.multi_datastream = bool(multi_datastream)
        self.data_array = bool(data_array)
        self._base = _base_model()

    @property
    def ENTITY_SETS(self):
        sets = dict(self._base.ENTITY_SETS)
        if not self.multi_datastream:
            sets.pop("multi_datastreams", None)
        return sets

    @property
    def ACTIONS(self):
        if self.data_array:
            return (CREATE_OBSERVATIONS,)
        return ()

    @property
    def FUNCTIONS(self):
        return ()

    @property
    def TYPES(self):
        return self._base.TYPES


def builtin_model(multi_datastream, data_array):
    return BuiltInModel(multi_datastream, data_array)


def extensions_from_conformance(urls):
    """Return ``(multi_datastream, data_array)`` for a conformance list."""
    found = set(urls or ())
    return (
        MULTIDATASTREAM_CONFORMANCE in found,
        DATA_ARRAY_CONFORMANCE in found,
    )


def conformance_urls(document):
    """Read conformance URIs from a SensorThings service document."""
    if not isinstance(document, dict):
        return frozenset()
    values = None
    settings = document.get("serverSettings")
    if isinstance(settings, dict):
        values = settings.get("conformance")
    if values is None:
        values = document.get("conformance")
    if not isinstance(values, list):
        return frozenset()
    found = []
    for item in values:
        if isinstance(item, str):
            found.append(item)
        elif isinstance(item, dict):
            for key in ("url", "href", "name"):
                if isinstance(item.get(key), str):
                    found.append(item[key])
                    break
    return frozenset(found)


def _base_model():
    import frost_sta_client.generated.model as bundled

    return bundled
