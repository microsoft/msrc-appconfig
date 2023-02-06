from __future__ import annotations
from msrc.appconfig.schema import (
    Element, AtomicType, TupleType, Schema, SchemaSource)
from typing import Optional, Tuple, Union, Type, Any, cast
import param
import enum


class IntTuple(param.NumericTuple):
    """
    Parameter class that must always have integer values
    """

    def _validate(self, val: object):
        super()._validate(val)
        # NumeriTuple ensures val is a numeric tuple
        if val is not None:
            val = cast(Tuple[object, ...], val)
            for i, n in enumerate(val):
                if not isinstance(n, int):
                    raise ValueError(
                        "{}: tuple element at index {} with "
                        "value {} in {} is not an integer"
                        .format(self.name, i, n, val))


def inspect(schema: type) -> Optional[SchemaSource]:
    if issubclass(schema, param.Parameterized):
        params = {
            name: p for name, p in schema.param.objects().items()
            if not p.readonly
        }
    else:
        return None

    def make_element(
        name: str,
        f: param.parameterized.Parameter[object]
    ) -> Element:
        t: Union[AtomicType, Type[enum.Enum], TupleType, Schema[object]]
        if isinstance(f, param.Integer):
            t = AtomicType.INT
        elif isinstance(f, param.Number):
            t = AtomicType.FLOAT
        elif isinstance(f, param.Boolean):
            t = AtomicType.BOOL
        elif isinstance(f, param.String):
            t = AtomicType.STR
        elif isinstance(f, param.ClassSelector):
            if issubclass(f.class_, enum.Enum):
                t = f.class_
            else:
                t = Schema(f.class_)
        elif isinstance(f, IntTuple):
            t = TupleType(AtomicType.INT, f.length)
        elif isinstance(f, param.NumericTuple):
            t = TupleType(AtomicType.FLOAT, f.length)
        # pyright 1.1.292 inference makes param.List.class_ be Type[object]
        # which is incorrect.
        elif isinstance(f, param.List) and cast(Any, f.class_) is None:
            raise ValueError("List parameter %s doesn't specify type of "
                             "list items using class_ keyword.")
        elif isinstance(f, param.List) and issubclass(f.class_, bool):
            t = TupleType(AtomicType.BOOL, 0, parse_to_list=True)
        elif isinstance(f, param.List) and issubclass(f.class_, int):
            t = TupleType(AtomicType.INT, 0, parse_to_list=True)
        elif isinstance(f, param.List) and issubclass(f.class_, float):
            t = TupleType(AtomicType.FLOAT, 0, parse_to_list=True)
        elif isinstance(f, param.List) and issubclass(f.class_, str):
            t = TupleType(AtomicType.STR, 0, parse_to_list=True)
        elif isinstance(f, param.List) and issubclass(f.class_, enum.Enum):
            t = TupleType(f.class_, 0, parse_to_list=True)
        else:
            raise ValueError("%s: type %r unsupported." % (name, f))
        return Element(
            help=f.doc,
            element_type=t,
            is_secret=False,
            has_default=f.default is not None,
            default_value=f.default)
    return tuple(
        (name, make_element(name, f)) for name, f in params.items()
        if not name.startswith('_'))
