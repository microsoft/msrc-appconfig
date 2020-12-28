import pytest
import param

import msrc.appconfig as ag


class SampleConfig(param.Parameterized):
    element = param.String(None)


class DerivedConfig(SampleConfig, param.Parameterized):
    derived = param.String(None)


@pytest.fixture
def reset_global():
    ag._SharedInstance.appconfig = None


def test_global(reset_global):
    with pytest.raises(RuntimeError):
        ag.get_global(SampleConfig)
    default = SampleConfig(element="test")
    assert ag.get_global(SampleConfig, default) is default
    with pytest.raises(ValueError):
        ag.set_global(dict())
    ag.set_global(DerivedConfig(element="one", derived="two"))
    assert ag.get_global(SampleConfig).element == "one"
    assert ag.get_global(DerivedConfig).derived == "two"
    with pytest.raises(ValueError):
        ag.get_global(int)
    with pytest.raises(RuntimeError):
        ag.set_global(DerivedConfig(
            element="three", derived="four"))


def test_gather_config_derived(reset_global, mocker):
    defaults = dict(element="one", derived="two")
    cfg = ag.gather_config(
        DerivedConfig,
        argv=[],
        override_defaults=defaults,
        set_global=True)
    assert isinstance(cfg, DerivedConfig)
    assert ag.get_global(SampleConfig).element == "one"
    assert ag.get_global(DerivedConfig).derived == "two"


def test_environ(mocker):
    mocker.patch.dict("os.environ", {"test_element": "a string"})
    observed = ag.from_environ(DerivedConfig, "test_")
    assert observed == dict(element="a string")
