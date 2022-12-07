from __future__ import annotations
from typing import Optional
from msrc.appconfig.schema import Element, SchemaSource, interpret_type
import attr


def inspect(schema: type) -> Optional[SchemaSource]:
    try:
        fields = attr.fields(schema)
    except attr.exceptions.NotAnAttrsClassError:
        return None

    def make_element(field: attr.Attribute[object]) -> Element:
        field_type = field.type
        if field_type is None:
            raise ValueError(f"{schema}.{field.name}: "
                             "no type annotation.")
        element_type = interpret_type(field_type)
        if element_type is not None:
            return Element(
                help=field.metadata.get("help", None),
                element_type=element_type,
                is_secret=not field.repr,
                has_default=not (field.default is attr.NOTHING),
                default_value=field.default)
        else:
            raise ValueError(f"{schema}.{field.name}: {field.type} "
                             "type unsupported.")
    return tuple((field.name, make_element(field))
                 for field in fields
                 if not field.name.startswith('_'))
