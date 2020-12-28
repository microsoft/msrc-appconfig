from msrc.appconfig.read_argv import from_argv
import pytest
import math
import typing as ty
from common import mk_schema, mk_class


def test_int():
    s = mk_schema(("test_int", int))
    d, _ = from_argv(s, ("--test-int", "34", ))
    assert d == ((("test_int", ), 34, ("argv",)),)
    d, _ = from_argv(s, ("--test_int", "-34", ),
                     arg_aliases=dict(t="test_int"))
    assert d == ((("test_int", ), -34, ("argv",)), )
    d, _ = from_argv(s, ("-t", "34", ),
                     arg_aliases=dict(t="test_int"))
    assert d == ((("test_int", ), 34, ("argv",)), )
    d, _ = from_argv(s, ("-2", "34", ),
                     arg_aliases={2: "test_int"})  # type: ignore
    assert d == ()


def test_nested_float():
    s = mk_schema(("nested", mk_class(("float", float))))
    d, _ = from_argv(s, ("--nested.float", "3.14", ))
    assert d == ((("nested", "float"), 3.14, ("argv",)), )
    d, _ = from_argv(s, ("--nested.float", "-3.14", ),
                     arg_aliases={"t": "nested.float"})
    assert d == ((("nested", "float"), -3.14, ("argv",)), )
    d, _ = from_argv(s, ("-t", "inf", ),
                     arg_aliases={"t": "nested.float"})
    assert d == ((("nested", "float"), math.inf, ("argv",)), )


def test_parse_err():
    s = mk_schema(("test", int))
    with pytest.raises(ValueError):
        from_argv(s, ("--test", "string", ))


def test_str():
    s = mk_schema(("test", str))
    d, _ = from_argv(s, ("--test", "string", ))
    assert d == ((("test", ), "string", ("argv",)), )
    d, _ = from_argv(s, ("--test", "", ))
    assert d == ((("test", ), "", ("argv",)), )


def test_bool():
    s = mk_schema(("test", bool))
    d, _ = from_argv(s, ("--test", "true", ))
    assert d == ((("test", ), True, ("argv",)), )
    d, _ = from_argv(s, ("--test", "false", ))
    assert d == ((("test", ), False, ("argv",)), )
    with pytest.raises(ValueError):
        list(from_argv(s, ("--test", "string", )))
    d, _ = from_argv(s, ("--test", ))
    assert d == ((("test", ), True, ("argv",)), )


def test_strtuple():
    s = mk_schema(("test", ty.Tuple[str, str]))
    d, _ = from_argv(s, ("--test", "one", "two", ))
    assert d == ((("test", ), ("one", "two"), ("argv",)), )
    with pytest.raises(SystemExit):
        from_argv(s, ("--test", "one", ))


def test_strtuple_any():
    s = mk_schema(("test", ty.Tuple[str, ...]))
    d, _ = from_argv(s, ("--test", "one", "two", ))
    assert d == ((("test", ), ("one", "two"), ("argv",)), )
    d, _ = from_argv(s, ("--test", "one", ))
    assert d == ((("test", ), ("one",), ("argv",)), )
    d, _ = from_argv(s, ("--test", ))
    assert d == ((("test", ), (), ("argv",)), )
