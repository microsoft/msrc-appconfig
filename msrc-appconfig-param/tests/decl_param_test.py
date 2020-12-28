from enum import Enum
import typing as ty

import pytest
import param

import msrc.appconfig
from msrc.appconfig.schema import Schema
from msrc.appconfig_decl.decl_param import IntTuple


class En(Enum):
    Option1 = 1
    Option2 = 2


class Nested(param.Parameterized):
    booleans: ty.List[bool] = ty.cast(ty.List[bool], param.List(
        None,
        class_=bool,
        doc="A pair of Boolean values."))
    options: ty.List[En] = ty.cast(ty.List[En], param.List(
        class_=En,
        default=[En.Option1, En.Option2]))


class AllTypes(param.Parameterized):
    string: str = ty.cast(str, param.String(None))
    integer: int = ty.cast(int, param.Integer(None))
    fractional: float = ty.cast(float, param.Number(None))
    boolean: bool = ty.cast(bool, param.Boolean(None))
    option: En = ty.cast(En, param.ClassSelector(En))
    strings: ty.List[str] = ty.cast(ty.List[str], param.List(None, class_=str))
    integers: ty.Tuple[int, int] = ty.cast(ty.Tuple[int, int],
                                           IntTuple(None, 2))
    fractionals: ty.Tuple[float, float] = ty.cast(ty.Tuple[float, float],
                                                  param.NumericTuple(None, 2))
    float_array: ty.List[float] = ty.cast(ty.List[float],
                                          param.List(None, float))
    int_array: ty.List[int] = ty.cast(ty.List[int], param.List(None, int))
    nested: Nested = ty.cast(Nested, param.ClassSelector(Nested))


class Base(param.Parameterized):
    base: int = ty.cast(int, param.Integer())


class Derived(Base, Nested, param.Parameterized):
    derived: str = ty.cast(str, param.String())


class PathNotSupported(param.Parameterized):
    f: dict = ty.cast(dict, param.Path())


class GenericListNotSupported(param.Parameterized):
    f: dict = ty.cast(dict, param.List())


def test_schema():
    s = Schema(AllTypes)
    assert len(s) == 11 + 1
    assert len(tuple(s.deep_items())) == 12 + 2  # s.name and s.nested.name
    element_type = ty.cast(Schema, s["nested"].element_type)
    assert element_type["options"].has_default
    assert len([item for item in s.deep_items() if item[1].has_default]) == 3
    assert element_type["booleans"].help
    assert len([item for item in s.deep_items() if item[1].help]) == 3


def test_inheritance():
    assert len(Schema(Base)) == 2
    assert len(Schema(Nested)) == 3
    assert len(Schema(Derived)) == 5
    assert isinstance(msrc.appconfig.from_dict(
        Derived, dict(booleans=(True, True))), Derived)


def test_unsupported():
    with pytest.raises(ValueError):
        Schema(PathNotSupported)
    with pytest.raises(ValueError):
        Schema(GenericListNotSupported)


class IntPairSample(param.Parameterized):
    pair = IntTuple()


def test_inttuple():
    ok_pair = (1, 2)
    ok = IntPairSample(pair=ok_pair)
    assert ok.pair == ok_pair
    with pytest.raises(ValueError):
        IntPairSample(pair=(1, 3.14))
