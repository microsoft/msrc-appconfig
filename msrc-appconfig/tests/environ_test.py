from msrc.appconfig.read_environ import from_environ
import os
import pytest
import typing as ty
from common import mk_schema, mk_class


def test_int():
    s = mk_schema(("test", int))
    p = "int_"
    os.environ["int_test"] = "34"
    d = list(from_environ(s, p))
    assert d == [(("test", ), 34, ("env", "int_test"))]


def test_nested_float():
    s = mk_schema(
        ("test", mk_class(("float", float)))
    )
    p = "nested_"
    os.environ["nested_test.float"] = "3.14"
    d = list(from_environ(s, p))
    assert d == [(("test", "float"), 3.14, ("env", "nested_test.float"))]


def test_novar():
    s = mk_schema(("test", int))
    p = "novar_"
    d = list(from_environ(s, p))
    assert d == []


def test_parse_err():
    s = mk_schema(("test", int))
    p = "parse_err_"
    os.environ["parse_err_test"] = "a"
    with pytest.raises(ValueError):
        list(from_environ(s, p))


def test_str():
    s = mk_schema(("test", str))
    p = "str_"
    os.environ["str_test"] = "string"
    d = list(from_environ(s, p))
    assert d == [(("test", ), "string", ("env", "str_test"))]
    os.environ["str_test"] = ""
    d = list(from_environ(s, p))
    assert d == [(("test", ), "", ("env", "str_test"))]


def test_bool():
    s = mk_schema(("test", bool))
    p = "bool_"
    os.environ["bool_test"] = "true"
    d = list(from_environ(s, p))
    assert d == [(("test", ), True, ("env", "bool_test"))]
    os.environ["bool_test"] = "false"
    d = list(from_environ(s, p))
    assert d == [(("test", ), False, ("env", "bool_test"))]
    os.environ["bool_test"] = "a"
    with pytest.raises(ValueError):
        list(from_environ(s, p))


def test_strtuple():
    s = mk_schema(("test", ty.Tuple[str, str]))
    p = "strtuple_"
    os.environ["strtuple_test"] = "one two"
    d = list(from_environ(s, p))
    assert d == [(("test", ), ("one", "two"), ("env", "strtuple_test"))]
    os.environ["strtuple_test"] = '"one two" three'
    d = list(from_environ(s, p))
    assert d == [(("test", ), ("one two", "three"), ("env", "strtuple_test"))]
    os.environ["strtuple_test"] = '"\\"one \\\\ two\\"" three'
    d = list(from_environ(s, p))
    assert d == [(("test", ), ("\"one \\ two\"", "three"),
                  ("env", "strtuple_test"))]
    os.environ["strtuple_test"] = '"" ""'
    d = list(from_environ(s, p))
    assert d == [(("test", ), ("", ""), ("env", "strtuple_test"))]
