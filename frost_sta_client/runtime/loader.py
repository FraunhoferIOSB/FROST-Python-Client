"""Load a generated model package from the directory the caller chose."""

import hashlib
import importlib.util
import sys
from pathlib import Path


def load_model(location):
    """Import ``model.py`` from a generated directory or from a file path.

    The returned module is the one ``SensorThingsService`` binds. It is not
    the checked-in SensorThings model unless that directory was passed.
    """
    path = Path(location)
    if path.is_dir():
        path = path / "model.py"
    if not path.is_file():
        raise ValueError("generated model not found at {}".format(location))
    digest = hashlib.sha256(str(path.resolve()).encode("utf-8")).hexdigest()[:16]
    module_name = "frost_sta_client_model_{}".format(digest)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ValueError("cannot load generated model {}".format(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    for required in ("ENTITY_SETS", "ACTIONS", "FUNCTIONS"):
        if not hasattr(module, required):
            raise ValueError("generated model {} has no {}".format(path, required))
    return module
