from __future__ import annotations
from typing import Optional
from msrc.appconfig.schema import Element, SchemaSource, interpret_type
import dataclasses


def inspect(schema: type) -> Optional[SchemaSource]:
    if not dataclasses.is_dataclass(schema):
        return None
    fields = dataclasses.fields(schema)

    def make_element(field: dataclasses.Field[object]) -> Element:
        element_type = interpret_type(field.type)
        if element_type is not None:
            return Element(
                help=field.metadata.get("help", None),
                element_type=element_type,
                is_secret=not field.repr,
                has_default=not (
                    field.default is dataclasses.MISSING
                    and field.default_factory  # type: ignore
                    is dataclasses.MISSING),
                default_value=field.default)
        else:
            raise ValueError("%s: type %s unsupported."
                             % (field.name, field.type))
    return tuple((field.name, make_element(field))
                 for field in fields
                 if not field.name.startswith('_'))
