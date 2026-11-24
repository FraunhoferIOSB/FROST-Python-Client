"""Declarative field descriptions emitted by the generator.

Generated classes carry these objects and no per-type behavior.
"""


class PropertySpec:
    """One structural property."""

    def __init__(self, wire, python_name, edm, nullable=True):
        self.wire = wire
        self.python_name = python_name
        self.edm = edm
        self.nullable = nullable

    def __repr__(self):
        return "PropertySpec({!r}, {!r}, {!r}, nullable={!r})".format(
            self.wire, self.python_name, self.edm, self.nullable
        )


class ParameterSpec:
    """One action or function parameter kept from CSDL."""

    def __init__(self, name, edm, nullable=True):
        self.name = name
        self.edm = edm
        self.nullable = nullable

    def __repr__(self):
        return "ParameterSpec({!r}, {!r}, nullable={!r})".format(
            self.name, self.edm, self.nullable
        )


class OperationSpec:
    """One action or function, including the parameters declared for it."""

    def __init__(self, name, bound=False, parameters=(), return_type=None):
        self.name = name
        self.bound = bool(bound)
        self.parameters = tuple(parameters)
        self.return_type = return_type

    def __repr__(self):
        return "OperationSpec({!r}, bound={!r}, parameters={!r}, return_type={!r})".format(
            self.name, self.bound, self.parameters, self.return_type
        )


class NavigationSpec:
    """One navigation property."""

    def __init__(self, wire, python_name, target, collection=False, containment=False):
        self.wire = wire
        self.python_name = python_name
        self.target = target
        self.collection = collection
        self.containment = containment

    def __repr__(self):
        return "NavigationSpec({!r}, {!r}, {!r}, collection={!r}, containment={!r})".format(
            self.wire, self.python_name, self.target, self.collection, self.containment
        )
