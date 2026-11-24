"""Facade for the generated SensorThings model and the shared runtime.

README names such as ``Thing``, ``SensorThingsService``, and ``observations``
resolve when the loaded model contains those types and entity sets. Importing
this package does not configure a JSON backend.
"""

import frost_sta_client.generated as generated
import frost_sta_client.model as model
from frost_sta_client.runtime.data_array import DataArrayDocument, DataArrayValue
from frost_sta_client.runtime.entity import Entity
from frost_sta_client.runtime.entity_list import EntityList
from frost_sta_client.runtime.service import SensorThingsService
from frost_sta_client.service.auth_handler import AuthHandler
from frost_sta_client.__version__ import (
    __author__,
    __contact__,
    __copyright__,
    __description__,
    __license__,
    __title__,
    __url__,
    __version__,
)

for _name in generated.__all__:
    globals()[_name] = getattr(generated, _name)

__all__ = [
    "__author__",
    "__contact__",
    "__copyright__",
    "__description__",
    "__license__",
    "__title__",
    "__url__",
    "__version__",
    "model",
    "AuthHandler",
    "DataArrayDocument",
    "DataArrayValue",
    "Entity",
    "EntityList",
    "SensorThingsService",
]
__all__.extend(generated.__all__)
