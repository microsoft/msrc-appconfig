from msrc.appconfig import from_files
import pytest
from common import AllTypes, WithDefaults, all_values, all_yaml, En


def test_yaml_single_file(tmp_path):
    (tmp_path/"conf.yaml").write_text(all_yaml)
    loaded = from_files(AllTypes, tmp_path/"conf.yaml")
    assert loaded == all_values


def test_two_files(tmp_path):
    """Second file overrides and adds to the first."""
    (tmp_path/"conf1.yaml").write_text(
        "fractional: 4.13\noption: Option1")
    (tmp_path/"conf2.json").write_text(
        '{"fractional": 3.14, "nested":{"booleans": [true, false]}}')
    loaded = from_files(AllTypes,
                        tmp_path/"conf1.yaml", tmp_path/"conf2.json")
    assert loaded == dict(fractional=3.14,
                          option=En.Option1,
                          nested=dict(booleans=(True, False)))


def test_first_arg_not_class():
    with pytest.raises(TypeError):
        from_files("something")  # type: ignore


def test_first_arg_unsupported():
    with pytest.raises(ValueError):
        from_files(int)


def test_wrong_type(tmp_path):
    conf_path = tmp_path/"conf.yaml"
    conf_path.write_text("a: [true]")
    with pytest.raises(TypeError):
        from_files(WithDefaults, conf_path)


def test_ignore_unrecognized(tmp_path):
    conf_path = tmp_path/"conf.yaml"
    conf_path.write_text("b: 12")
    loaded = from_files(WithDefaults, conf_path)
    assert {} == loaded


def test_wrong_nested(tmp_path):
    conf_path = tmp_path/"conf.yaml"
    conf_path.write_text("nested: 12")
    with pytest.raises(TypeError):
        from_files(AllTypes, conf_path)
