from typing import Dict
from msrc.appconfig import from_argv
import pytest
from common import AllTypes, all_args, all_values, En


def test_argv():
    loaded = from_argv(AllTypes, all_args)
    assert loaded == all_values


def test_argv_unknown():
    unknown = ["--unknown"]
    loaded = from_argv(AllTypes, all_args+unknown)
    expected: Dict[str, object] = dict(all_values.items())
    expected["_unknown_args"] = unknown
    assert loaded == expected


def test_argv_aliases():
    loaded = from_argv(
        AllTypes,
        ["--integer", "34", "-o", "1", "2"],
        {"o": "nested.options"})
    assert loaded == dict(
        integer=34,
        nested=dict(options=(En.Option1, En.Option2))
    )


def test_first_arg_not_class():
    with pytest.raises(TypeError):
        from_argv("something", [])  # type: ignore


def test_first_arg_unsupported():
    with pytest.raises(ValueError):
        from_argv(int, [])
