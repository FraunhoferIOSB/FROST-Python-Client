"""Service root, HTTP, and the generated entity-set facade."""

import requests

from frost_sta_client.runtime.control import choose_control
from frost_sta_client.runtime.csdl import parse_csdl
from frost_sta_client.runtime.errors import call, response_json
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
    """Client for one service root and one generated model.

    ``model`` is a module produced for this service. When it is omitted, the
    bundled SensorThings model is used so the existing names keep working.
    ``control`` skips the probe when the vocabulary is already known. Otherwise
    the first write reads this root's ``$metadata`` and ``OData-Version``.
    """

    def __init__(self, url, auth_handler=None, proxies=None, metadata=None, model=None, control=None):
        if not isinstance(url, str) or not url.strip():
            raise ValueError("url must be a non-empty string")
        self.url = url.strip().rstrip("/")
        if auth_handler is not None and not isinstance(auth_handler, AuthHandler):
            raise ValueError("auth_handler must be an AuthHandler")
        self.auth_handler = auth_handler
        if proxies is not None and not isinstance(proxies, dict):
            raise ValueError("proxies must be a dictionary")
        self.proxies = proxies
        self.model = model if model is not None else _bundled_model()
        self._control = control
        self._metadata = _coerce_metadata(metadata)
        self._metadata_response = None
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
            self._control = self._probe_control()
        return self._control

    def join(self, path):
        """Join a relative path with a single slash. An empty base path is allowed."""
        return "{}/{}".format(self.url.rstrip("/"), str(path).lstrip("/"))

    def execute(self, method, url, **kwargs):
        kwargs.setdefault("timeout", 60)
        auth = None
        if self.auth_handler is not None:
            auth = self.auth_handler.add_auth_header()
        response = requests.request(method, url, proxies=self.proxies, auth=auth, **kwargs)
        response.raise_for_status()
        return response

    def live_model(self):
        """Metadata of this root, fetched once unless a document was injected.

        A 404 means this root does not publish ``$metadata``. No action is
        advertised. Other HTTP errors propagate.
        """
        if self._metadata is None:
            self._metadata = _model_from_response(self._metadata_exchange())
        return self._metadata

    def _metadata_exchange(self):
        if self._metadata_response is None:
            self._metadata_response = self._get_allowing_status(self.join("$metadata"))
        return self._metadata_response

    def _get_allowing_status(self, url):
        try:
            return self.execute("get", url)
        except requests.HTTPError as exc:
            response = getattr(exc, "response", None)
            if response is not None and response.status_code == 404:
                return response
            raise

    def _probe_control(self):
        response = self._metadata_exchange()
        version = response.headers.get("OData-Version")
        body = response.text or ""
        is_csdl = response.status_code == 200 and body.lstrip().startswith("<")
        document = None
        if not version and not is_csdl:
            service_document = self._get_allowing_status(self.url)
            version = version or service_document.headers.get("OData-Version")
            if service_document.status_code == 200 and service_document.text:
                try:
                    document = service_document.json()
                except ValueError:
                    document = None
        return choose_control(version, is_csdl, document)

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
        if not self.advertises(name):
            raise RuntimeError("{} is not advertised by this service root".format(name))
        url = "{}/{}".format(entity_url(entity, self), name)
        method_name = "get" if kind == "function" else "post"
        kwargs = {"json": body} if method_name == "post" else {}
        response = call(self, method_name, url, "Calling {}".format(name), **kwargs)
        if not getattr(response, "content", b""):
            return None
        return response_json(response)

    def advertises(self, name):
        """True when this root's metadata lists the action or function."""
        model = self.live_model()
        return name in getattr(model, "actions", ()) or name in getattr(model, "functions", ())

    def invoke(self, name, body=None, *, kind="action"):
        if not self.advertises(name):
            raise RuntimeError("{} is not advertised by this service root".format(name))
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


class _EmptyModel:
    """A root that published no CSDL document."""

    actions = frozenset()
    functions = frozenset()


def _bundled_model():
    import frost_sta_client.generated.model as bundled

    return bundled


def _model_from_response(response):
    if response.status_code == 404:
        return _EmptyModel()
    text = response.text or ""
    if not text.lstrip().startswith("<"):
        return _EmptyModel()
    return parse_csdl(text)


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
