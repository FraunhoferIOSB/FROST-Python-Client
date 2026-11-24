"""OData query options.

An option replaces the previous value of the same option only after the new
value has been checked. ``orderby`` without a direction is ascending.
``select`` with no arguments, or with a non-string, raises TypeError and leaves
a previous ``$select`` in place.
"""

from urllib.parse import urlencode

from frost_sta_client.runtime.entity_list import entity_list_from_json, validate_callback
from frost_sta_client.runtime.errors import call, response_json


class Query:
    def __init__(self, dao):
        self.dao = dao
        self.params = {}

    def filter(self, expression):
        if not isinstance(expression, str):
            raise TypeError("filter requires a string")
        self.params["$filter"] = expression
        return self

    def select(self, *args):
        if not args or not all(isinstance(arg, str) and arg for arg in args):
            raise TypeError("select() requires one or more property names")
        self.params["$select"] = ",".join(args)
        return self

    def expand(self, expression):
        if not isinstance(expression, str) or not expression:
            raise TypeError("expand requires a string")
        self.params["$expand"] = expression
        return self

    def orderby(self, criteria, direction="asc"):
        if not isinstance(criteria, str) or not criteria:
            raise TypeError("orderby requires a property name")
        if not isinstance(direction, str) or direction.lower() not in ("asc", "desc"):
            raise ValueError("orderby direction must be asc or desc")
        self.params["$orderby"] = "{} {}".format(criteria, direction.lower())
        return self

    def top(self, value):
        self.params["$top"] = str(_non_negative(value, "top"))
        return self

    def skip(self, value):
        self.params["$skip"] = str(_non_negative(value, "skip"))
        return self

    def count(self, value=True):
        if not isinstance(value, bool):
            raise TypeError("count requires a boolean")
        self.params["$count"] = "true" if value else "false"
        return self

    def list(self, callback=None, step_size=None):
        validate_callback(callback, step_size)
        response = call(
            self.dao.service,
            "get",
            self.build_url(),
            "Querying {}".format(self.dao.entity_class.__name__),
        )
        payload = response_json(response)
        listing = entity_list_from_json(payload, self.dao.entity_class, self.dao.service)
        listing.arm(callback, step_size)
        return listing

    def build_url(self):
        base = self.dao.collection_url()
        if not self.params:
            return base
        separator = "&" if "?" in base else "?"
        return base + separator + urlencode(self.params, safe=",/")


def _non_negative(value, name):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("{} requires a non-negative integer".format(name))
    return value
