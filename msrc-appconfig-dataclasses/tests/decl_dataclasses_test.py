from dataclasses import dataclass, field
from enum import Enum
import typing as ty

import pytest

import msrc.appconfig
from msrc.appconfig.schema import Schema


class En(Enum):
    Option1 = 1
    Option2 = 2


@dataclass(frozen=True)
class Nested:
    booleans: ty.Tuple[bool, bool] = field(metadata=dict(
        help="A pair of Boolean values."))
    options: ty.Tuple[En, En] = (En.Option1, En.Option2)


@dataclass(frozen=True)
class AllTypes:
    integer: int
    fractional: float
    boolean: bool
    option: En
    strings: ty.Tuple[str, str]
    integers: ty.Tuple[int, int]
    fractionals: ty.Tuple[float, float]
    nested: Nested
    string: str = field(repr=False)  # is_secret


@dataclass(frozen=True)
class Base:
    base: int = 0


@dataclass(frozen=True)
class Derived(Base, Nested):
    derived: str = ""


@dataclass(frozen=True)
class ListsNotSupported:
    f: list


@dataclass(frozen=True)
class DictsNotSupported:
    f: dict


@dataclass(frozen=True)
class NonUniformTuplesNotSupported:
    f: ty.Tuple[str, int]


def test_schema():
    s = Schema(AllTypes)
    assert len(s) == 9
    assert len(tuple(s.deep_items())) == 10
    element_type = ty.cast(Schema, s["nested"].element_type)
    assert element_type["options"].has_default
    assert len([item for item in s.deep_items() if item[1].has_default]) == 1
    assert element_type["booleans"].help
    assert len([item for item in s.deep_items() if item[1].help]) == 1
    assert s["string"].is_secret
    assert len([item for item in s.deep_items() if item[1].is_secret]) == 1


def test_inheritance():
    assert len(Schema(Base)) == 1
    assert len(Schema(Nested)) == 2
    assert len(Schema(Derived)) == 4
    assert isinstance(msrc.appconfig.from_dict(
        Derived, dict(booleans=(True, True))), Derived)


def test_unsupported():
    with pytest.raises(ValueError):
        Schema(ListsNotSupported)
    with pytest.raises(ValueError):
        Schema(DictsNotSupported)
    with pytest.raises(ValueError):
        Schema(NonUniformTuplesNotSupported)


@dataclass(frozen=True)
class Inner():
    b: int


@dataclass(frozen=True)
class Outer():
    a2: Inner = Inner(2)


def test_dataclass_gather_nested_default():
    c = msrc.appconfig.gather_config(Outer, argv=[])
    assert c.a2.b == 2
