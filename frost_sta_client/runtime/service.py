"""Service root, HTTP, and the generated entity-set facade."""

from pathlib import Path

import requests

from frost_sta_client.runtime.builtin import (
    builtin_model,
    conformance_urls,
    extensions_from_conformance,
)
from frost_sta_client.runtime.control import choose_control
from frost_sta_client.runtime.csdl import parse_csdl
from frost_sta_client.runtime.errors import call, response_json
from frost_sta_client.runtime.modelcheck import assert_same_model
from frost_sta_client.runtime.names import snake
from frost_sta_client.runtime.specs import OperationSpec
from frost_sta_client.service.auth_handler import AuthHandler

_PROTECTED = {
    "advertises",
    "create",
    "delete",
    "execute",
    "invoke",
    "join",
    "live_model",
    "patch",
    "update",
    "url",
    "write_prefix",
}


class SensorThingsService:
    """Client for one service root and one model.

    ``model`` is a generated model location, or empty for a built-in
    SensorThings model. The second argument, ``extensions``, is
    ``(multi_datastream, data_array)`` and selects which built-in model that
    is. Both default to on. A loaded
    model is followed as it stands: an action it contains can be called.
    Before the first read or write the root is read once. SensorThings is
    compared with the built-in model selected by conformance. OData is
    compared with that root's ``$metadata``. ``control`` skips the probe when
    the vocabulary is already known.
    """

    def __init__(
        self,
        url,
        model=None,
        extensions=(True, True),
        auth_handler=None,
        proxies=None,
        metadata=None,
        control=None,
    ):
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")
        self.url = url.strip().rstrip("/")
        if auth_handler is not None and not isinstance(auth_handler, AuthHandler):
            raise ValueError("auth_handler must be an AuthHandler")
        self.auth_handler = auth_handler
        if proxies is not None and not isinstance(proxies, dict):
            raise ValueError("proxies must be a dictionary")
        self.proxies = proxies
        if isinstance(model, tuple):
            extensions = model
            model = None
        self.extensions = _extensions(extensions)
        self.model = _resolve_model(model, self.extensions)
        self._explicit_control = control is not None
        self._control = control
        self._metadata = _coerce_metadata(metadata)
        self._probed = False
        self._ready = False
        self._checking = False
        self._kind = None
        self._root_document = None
        self._sets = {}
        self._operations = {}
        self._bind_model(self.model)

    @classmethod
    def open(cls, url, out, auth_handler=None, proxies=None):
        """Write this root's ``$metadata`` to ``out``, load it, and return a service."""
        from frost_sta_client.generate import fetch_metadata, write_package
        from frost_sta_client.runtime.loader import load_model

        auth = None
        if auth_handler is not None:
            auth = auth_handler.add_auth_header()
        text = fetch_metadata(url, auth=auth)
        write_package(text, out, service_root=url.strip().rstrip("/"))
        return cls(url, auth_handler=auth_handler, proxies=proxies, model=load_model(out))

    @property
    def write_prefix(self):
        if self._control is None:
            self._probe()
        return self._control

    def join(self, path):
        """Join a relative path with a single slash. An empty base path is allowed."""
        return "{}/{}".format(self.url.rstrip("/"), str(path).lstrip("/"))

    def execute(self, method, url, **kwargs):
        self.ensure_ready()
        return self._exchange(method, url, **kwargs)

    def _exchange(self, method, url, **kwargs):
        kwargs.setdefault("timeout", 60)
        auth = None
        if self.auth_handler is not None:
            auth = self.auth_handler.add_auth_header()
        response = requests.request(method, url, proxies=self.proxies, auth=auth, **kwargs)
        response.raise_for_status()
        return response

    def ensure_ready(self):
        """Read the root once, then compare the loaded model, before a request."""
        if self._ready or self._explicit_control or self._checking:
            return
        self._checking = True
        try:
            if self._control is None:
                self._probe()
            self._check_model()
            self._ready = True
        finally:
            self._checking = False

    def _probe(self):
        """GET the service root once and cache SensorThings versus OData."""
        if self._probed:
            return
        response = self._exchange("get", self.url)
        version = response.headers.get("OData-Version")
        text = response.text or ""
        is_csdl = response.status_code == 200 and text.lstrip().startswith("<")
        document = None
        if not is_csdl and response.status_code == 200 and text:
            try:
                document = response.json()
            except ValueError:
                document = None
        self._control = choose_control(version, is_csdl, document)
        self._root_document = document
        self._kind = "sta" if self._control == "@iot" else "odata"
        self._probed = True

    def _check_model(self):
        if self._kind == "sta":
            flags = extensions_from_conformance(conformance_urls(self._root_document))
            expected = builtin_model(flags[0], flags[1])
            assert_same_model(self.model, expected, self.url)
            return
        assert_same_model(self.model, self._odata_metadata(), "{} $metadata".format(self.url))

    def _odata_metadata(self):
        if self._metadata is not None:
            return self._metadata
        response = self._exchange("get", self.join("$metadata"))
        text = response.text or ""
        if response.status_code != 200 or not text.lstrip().startswith("<"):
            raise RuntimeError("no $metadata at {}".format(self.url))
        self._metadata = parse_csdl(text)
        return self._metadata

    def live_model(self):
        """OData metadata of this root, fetched once unless a document was injected.

        A SensorThings root has no ``$metadata``. This is not called for that
        dialect. Other HTTP errors propagate.
        """
        return self._odata_metadata()

    def __getattr__(self, name):
        if name in self._sets:
            wire, cls = self._sets[name]

            def entity_method(wire=wire, cls=cls):
                from frost_sta_client.runtime.dao import Dao

                return Dao(self, cls, wire)

            entity_method.__name__ = name
            entity_method.__doc__ = "Return the DAO for the {} entity set.".format(wire)
            return entity_method
        if name in self._operations:
            spec, kind = self._operations[name]

            def operation(*args, spec=spec, kind=kind, **kwargs):
                if spec.bound:
                    entity = args[0] if args else kwargs.get("entity")
                    body = args[1] if len(args) > 1 else kwargs.get("body")
                    return self._invoke_bound(spec.name, entity, body, kind)
                body = args[0] if args else kwargs.get("body")
                return self.invoke(spec.name, body, kind=kind)

            operation.__name__ = name
            operation.__doc__ = "Call {} {}.".format(spec.name, kind)
            operation.operation = spec
            return operation
        raise AttributeError("{!r} has no attribute {!r}".format(type(self).__name__, name))

    def _bind_model(self, model):
        taken = set(_PROTECTED)
        for py_name, value in model.ENTITY_SETS.items():
            wire, cls = value[0], value[1]
            method_name = py_name if py_name not in taken else _spare(py_name, taken)
            self._sets[method_name] = (wire, cls)
            taken.add(method_name)
        for item in getattr(model, "ACTIONS", ()):
            self._add_operation(_as_operation(item), "action", taken)
        for item in getattr(model, "FUNCTIONS", ()):
            self._add_operation(_as_operation(item), "function", taken)

    def _add_operation(self, spec, kind, taken):
        method_name = _bind_name(spec.name, taken)
        self._operations[method_name] = (spec, kind)

    def _invoke_bound(self, name, entity, body, kind):
        from frost_sta_client.runtime.control import entity_url

        if entity is None:
            raise TypeError("{} is bound and requires an entity".format(name))
        self._require_operation(name)
        url = "{}/{}".format(entity_url(entity, self), name)
        method_name = "get" if kind == "function" else "post"
        kwargs = {"json": body} if method_name == "post" else {}
        response = call(self, method_name, url, "Calling {}".format(name), **kwargs)
        if not getattr(response, "content", b""):
            return None
        return response_json(response)

    def _operation_named(self, name):
        for spec, kind in self._operations.values():
            if spec.name == name:
                return spec, kind
        return None

    def _require_operation(self, name):
        if self._operation_named(name) is None:
            raise RuntimeError("{} is not in the loaded model".format(name))

    def advertises(self, name):
        """True when the loaded model contains the action or function."""
        return self._operation_named(name) is not None

    def invoke(self, name, body=None, *, kind="action"):
        self._require_operation(name)
        method = "get" if kind == "function" else "post"
        kwargs = {"json": body} if method == "post" else {}
        response = call(self, method, self.join(name), "Calling {}".format(name), **kwargs)
        if not getattr(response, "content", b""):
            return None
        return response_json(response)

    def create(self, entity):
        return self._dao_for(entity).create(entity)

    def update(self, entity):
        return self._dao_for(entity).update(entity)

    def patch(self, entity, body):
        return self._dao_for(entity).patch(entity, body)

    def delete(self, entity):
        return self._dao_for(entity).delete(entity)

    def _dao_for(self, entity):
        from frost_sta_client.runtime.dao import Dao

        entity_set = getattr(entity, "__entity_set__", None)
        if not entity_set:
            raise TypeError("{} is not an entity".format(type(entity).__name__))
        return Dao(self, type(entity), entity_set)


def _resolve_model(model, extensions):
    if model is None or (isinstance(model, str) and not model.strip()):
        return builtin_model(extensions[0], extensions[1])
    if isinstance(model, (str, Path)):
        from frost_sta_client.runtime.loader import load_model

        return load_model(model)
    return model


def _extensions(extensions):
    if (
        isinstance(extensions, tuple)
        and len(extensions) == 2
        and all(isinstance(item, bool) for item in extensions)
    ):
        return extensions
    raise ValueError("extensions must be (multi_datastream, data_array)")


def _bind_name(name, taken):
    py_name = snake(name)
    if py_name in taken or not py_name.isidentifier():
        py_name = _spare(py_name + "_action", taken)
    taken.add(py_name)
    return py_name


def _as_operation(item):
    if isinstance(item, OperationSpec):
        return item
    if isinstance(item, tuple) and item:
        bound = bool(item[1]) if len(item) > 1 else False
        return OperationSpec(item[0], bound)
    raise TypeError("operation must be an OperationSpec")


def _coerce_metadata(metadata):
    if metadata is None:
        return None
    if isinstance(metadata, str):
        if not metadata.lstrip().startswith("<"):
            raise ValueError("metadata must be a CSDL document or a parsed model")
        return parse_csdl(metadata)
    return metadata


def _spare(name, taken):
    candidate = name if name.isidentifier() else "operation"
    while candidate in taken or not candidate.isidentifier():
        candidate = candidate + "_value"
    return candidate
