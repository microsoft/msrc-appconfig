from msrc.appconfig import schema as s
from enum import Enum
import typing as ty
import pytest
from common import all_types_schema, mk_schema, mk_class, En, Nested


class CheckDefaults(ty.NamedTuple):
    f0: str = "string"
    f1: int = 1
    f2: float = 3.14
    f3: bool = True
    f4: En = En.Option2
    f5: ty.Tuple[str, str] = ("a", "b")
    f6: ty.Tuple[int, ...] = ()
    f7: ty.Tuple[int, ...] = (1, 2, 3)
    f8: Nested = Nested((True, False), (En.Option2, En.Option1))


DummyEnum = Enum("TestEnum", "A B C")


def test_tuple_ctor():
    assert s.TupleType(s.AtomicType.BOOL, 0) is not None
    assert s.TupleType(s.AtomicType.STR, 1) is not None
    assert s.TupleType(DummyEnum, 2) is not None
    with pytest.raises(ValueError):
        s.TupleType(s.AtomicType.BOOL, -1)
    with pytest.raises(AssertionError):
        s.TupleType(int, 0)  # type: ignore # intentionally


def test_tuple_repr():
    assert repr(
        s.TupleType(s.AtomicType.BOOL, 0)
    ) == "Tuple[BOOL, ...]"
    assert repr(
        s.TupleType(En, 2)
    ) == "Tuple[<enum 'En'>, <enum 'En'>]"
    assert repr(
        s.TupleType(s.AtomicType.STR, 0, parse_to_list=True)
    ) == "Tuple/List[STR]"


def test_element_ctor():
    assert s.Element(s.AtomicType.BOOL) is not None
    assert s.Element(DummyEnum) is not None
    assert s.Element(s.TupleType(s.AtomicType.STR, 0),
                     False, 0, "help", True) is not None
    assert s.Element(all_types_schema) is not None
    with pytest.raises(TypeError):
        s.Element(int)  # type: ignore # intentionally
    assert s.Element(s.TupleType(s.AtomicType.STR, 0, True),
                     True, []) is not None
    with pytest.raises(ValueError):
        s.Element(s.TupleType(s.AtomicType.STR, 0),
                  True, [])


# Parsing element values
# ----------------------

def test_parse_enum():
    assert s.Element(DummyEnum).parse("A") == DummyEnum.A
    assert s.Element(DummyEnum).parse(1) == DummyEnum.A
    with pytest.raises(ValueError):
        s.Element(DummyEnum).parse("X")


def test_parse_tuple_zero():
    "Tuples size==0 can take any sequences and individual values"
    assert s.Element(s.TupleType(s.AtomicType.INT, 0)).parse(
        ()) == ()
    assert s.Element(s.TupleType(s.AtomicType.INT, 0)).parse(
        (1,)) == (1,)
    assert s.Element(s.TupleType(s.AtomicType.INT, 1)).parse(
        "1") == (1,)
    assert s.Element(s.TupleType(s.AtomicType.INT, 1)).parse(
        1) == (1,)
    assert s.Element(s.TupleType(s.AtomicType.INT, 0)).parse(
        (1, 2)) == (1, 2)
    assert s.Element(
        s.TupleType(s.AtomicType.INT, 0, parse_to_list=True)).parse(
        ()) == []


def test_parse_tuple_one():
    "Tuples size==1 can take sequences len=1 and individual values"
    assert s.Element(s.TupleType(s.AtomicType.INT, 1)).parse(
        (1,)) == (1,)
    assert s.Element(s.TupleType(s.AtomicType.INT, 1)).parse(
        "1") == (1,)


def test_parse_tuple_two():
    "Tuples size!=1 can take sequences of proper length"
    assert s.Element(s.TupleType(s.AtomicType.INT, 2)).parse(
        ("1", 2)) == (1, 2)
    with pytest.raises(ValueError):
        s.Element(s.TupleType(s.AtomicType.INT, 2)).parse(
            ("1",))
    with pytest.raises(ValueError):
        s.Element(s.TupleType(s.AtomicType.INT, 2)).parse(
            (1, 2, 3))


def test_cannot_parse_schema():
    with pytest.raises(TypeError):
        s.Element(all_types_schema).parse({"fractional": 1.0})


# Other
# -----

def test_config_value_str():
    "ConfigValue has specific string representation."
    v = s.ConfigValue(("name",), "value", ("kind", "source"))
    assert str(v) == "name = 'value' from kind > source"


def test_deep_items():
    schema = mk_schema(
        ("a", int), ("b", mk_class(
            ("a", int), ("b", int))
        ), ("c", int)
    )
    assert tuple(
        k for k, e in schema.deep_items()) == (
        ("a",), ("b", "a"), ("b", "b"), ("c",)
    )


def test_unsupported_type(mocker):
    with pytest.raises(TypeError):
        mk_schema(("a", int), ("b", None))
    with pytest.raises(TypeError):
        mk_schema(("a", dict))
    with pytest.raises(TypeError):
        # Tuple must have at least one generic arg
        mk_schema(("a", ty.Tuple))
    with pytest.raises(TypeError):
        # Tuples must be homogenious
        mk_schema(("a", ty.Tuple[int, str]))
    with pytest.raises(TypeError):
        # Tuple element must be any atomic but a schema
        A = mk_class(("a", int))
        mk_schema(("a", ty.Tuple[A]))
    mocker.patch("msrc.appconfig.schema.get_schema",
                 return_value=(("a", 0),))


def test_from_dict():
    schema = mk_schema(("a", int))
    assert (12,) == schema.from_dict(dict(a=12))
    assert (24,) == schema.from_dict(dict(a="24"))
    schema = mk_schema(("a", int), ("b", mk_class(("c", str))))
    assert (21, ("d",)) == schema.from_dict(dict(a=21, b=dict(c="d")))


def test_from_dict_with_defaults():
    schema = s.Schema(Nested)
    nested = schema.from_dict(dict(booleans=(True, True)))
    assert nested.options == (En.Option1, En.Option2)


def test_from_dict_errors():
    schema = mk_schema(("a", int), ("b", mk_class(("c", str))))
    with pytest.raises(ValueError):
        schema.from_dict(dict(d=12))
    with pytest.raises(ValueError):
        schema.from_dict(dict(b=12))


def test_to_dict():
    schema = s.Schema(CheckDefaults)
    data = dict(f1=34, f6=(12, 13), f8=dict(booleans=(False, True)))
    instance = schema.from_dict(data)
    result = schema.to_dict(instance)
    assert result == data
    result = schema.to_dict(instance, include_defaults=True)
    assert result == dict(
        f0="string",
        f1=34,
        f2=3.14,
        f3=True,
        f4=En.Option2,
        f5=("a", "b"),
        f6=(12, 13),
        f7=(1, 2, 3),
        f8=dict(
            booleans=(False, True),
            options=(En.Option2, En.Option1))
    )


def test_to_dict_error():
    schema = s.Schema(CheckDefaults)
    with pytest.raises(TypeError):
        schema.to_dict(None)


def test_typestr_atomic():
    el = s.Element(s.AtomicType.INT)
    assert "INT" == el.type_str()


def test_typestr_enum():
    el = s.Element(En)
    assert "En" == el.type_str()


def test_typestr_schema():
    el = s.Element(mk_schema(("a", int)))
    assert "_" == el.type_str()


def test_typestr_tuple0():
    el = s.Element(s.TupleType(s.AtomicType.BOOL, 0))
    assert "[BOOL ...]" == el.type_str()


def test_typestr_tuple2():
    el = s.Element(s.TupleType(En, 2))
    assert "En En" == el.type_str()


def test_typestr_tuple3():
    el = s.Element(s.TupleType(s.AtomicType.STR, 3))
    assert "STR STR STR" == el.type_str()


def test_type_check():
    schema = s.Schema(CheckDefaults)
    assert all(el.has_default for name, el in schema.items())
    instance = schema.from_dict({})
    assert schema.type_check(instance)
    # Wrong type of a field
    assert not schema.type_check(instance._replace(f1=2.71))
    # None doesn't type-check anything
    assert not schema.type_check(None)
    # Wrong number of elements in a nested field
    assert not schema.type_check(instance._replace(
        f8=instance.f8._replace(booleans=(True, True, True))))
    # str doesn't match int anything but str
    assert not any(elt.type_check("1")
                   for name, elt in schema.items()
                   if name != "f0")
    # int doesn't match int anything but int or float
    assert not any(elt.type_check(1)
                   for name, elt in schema.items()
                   if name != "f1" and name != "f2")
    # but bool match int and float
    assert schema["f1"].type_check(True)
    assert schema["f2"].type_check(True)
    # and int match float
    assert schema["f2"].type_check(1)
    # tuple must have proper size
    assert not schema["f5"].type_check(())
    assert not schema["f5"].type_check(("a", "b", "c"))


class CheckInvalidDefaults(ty.NamedTuple):
    f0: str = 1  # type: ignore


def test_invalid_default():
    with pytest.raises(ValueError):
        s.Schema(CheckInvalidDefaults)
