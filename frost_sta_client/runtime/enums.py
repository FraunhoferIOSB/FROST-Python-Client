"""Enum base that registers generated enumerations for property coercion."""

from enum import Enum

from frost_sta_client.runtime.registry import register_type


class RegisteredEnum(Enum):
    """Generated enums subclass this so their EDM name can be resolved."""

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        short = getattr(cls, "__csdl_name__", None) or cls.__name__
        namespace = getattr(cls, "__namespace__", "")
        qualified = "{}.{}".format(namespace, short) if namespace else short
        register_type(short, qualified, cls)
