from __future__ import annotations
"""Provides appconfig support for typing.NamedTuple"""
from typing import Mapping, NamedTuple, Optional, cast
from typing_extensions import TypeGuard
from msrc.appconfig.schema import Element, SchemaSource, interpret_type


def is_typed_named_tuple(appconfig: object) -> TypeGuard[NamedTuple]:
    return isinstance(appconfig, type) \
        and issubclass(appconfig, tuple) \
        and hasattr(cast(object, appconfig), "_fields") \
        and hasattr(cast(object, appconfig), "__annotations__") \
        and (len(appconfig._fields) ==   # type: ignore
             len(appconfig.__annotations__))


def inspect(appconfig: object) -> Optional[SchemaSource]:
    if not is_typed_named_tuple(appconfig):
        return None
    fields = appconfig._fields  # type: ignore # reportPrivateUsage
    annotations = appconfig.__annotations__
    defaults: Mapping[str, object] = getattr(
        appconfig, "_field_defaults", {})
    docs: Mapping[str, str] = getattr(appconfig, "_field_help", {})

    def make_element(name: str) -> Element:
        element_type = interpret_type(annotations[name])
        if element_type is not None:
            return Element(
                element_type=element_type,
                has_default=name in defaults,
                default_value=defaults.get(name, None),
                help=docs.get(name, None))
        else:
            raise TypeError("Type %r unsupported for field %s in %s." % (
                annotations[name], name, appconfig))

    return tuple((field, make_element(field))
                 for field in fields
                 if not field.startswith('_'))
