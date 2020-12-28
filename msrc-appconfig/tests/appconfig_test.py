import pytest
import typing as ty
import math

import msrc.appconfig as ag
from common import AllTypes, all_args, all_values, mk_class
from common import WithDefaults, WithNestedDefaults


class SampleConfig(ty.NamedTuple):
    element: str


@pytest.fixture
def reset_global():
    ag._SharedInstance.appconfig = None


def test_global(reset_global):
    default = SampleConfig(element="test")
    assert ag.get_global(SampleConfig, default) is default
    with pytest.raises(RuntimeError):
        ag.get_global(SampleConfig)
    with pytest.raises(ValueError):
        ag.get_global(SampleConfig, 0)
    assert ag.get_global(object, default) is default

    ag.set_global(default)
    assert ag.get_global(SampleConfig) is default
    with pytest.raises(ValueError):
        ag.set_global(dict())
    with pytest.raises(ValueError):
        ag.get_global(int)
    with pytest.raises(RuntimeError):
        ag.set_global(SampleConfig(element="two"))


def test_gather_config_config_type_error(mocker):
    """`config_type` must be a type."""
    with pytest.raises(TypeError):
        ag.gather_config({})  # type: ignore


def test_gather_config_insufficient_data(mocker):
    with pytest.raises(SystemExit):
        ag.gather_config(SampleConfig)


def test_gather_config_from_args(mocker):
    mocker.patch("sys.argv", ["script"]+all_args)
    cfg = ag.gather_config(AllTypes)
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values


def test_gather_config_unknown_args(mocker):
    mocker.patch("sys.argv", ["script"]+all_args+["unknown", "args"])
    with pytest.raises(SystemExit):
        # unknown args
        ag.gather_config(AllTypes)


def test_gather_config_override_defaults(mocker):
    mocker.patch("sys.argv", ["script"])
    cfg = ag.gather_config(AllTypes, override_defaults=all_values)
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values


@pytest.mark.parametrize("option", ["c", "l", "e", "h"])
def test_gather_arg_aliases_override(option):
    """Arg_aliases override built-in short options"""
    cfg = ag.gather_config(
        mk_class(("test", int)),
        argv=[
            "-"+option, "12"
        ],
        arg_aliases={
            option: "test"
        })
    assert cfg.test == 12


def test_gather_config_no_argv(mocker):
    """To prevent reading from sys.argv set argv to ()"""
    mocker.patch("sys.argv", ["script", "unknown", "args"])
    with pytest.raises(SystemExit):  # unknown args
        ag.gather_config(AllTypes, override_defaults=all_values)
    cfg = ag.gather_config(AllTypes,
                           override_defaults=all_values,
                           argv=())
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values


def test_gather_config_no_env(mocker):
    """To prevent looking up shell variables set env_var_prefix to '-'."""
    mocker.patch("sys.argv", ["script"])
    from_environ = mocker.patch("msrc.appconfig.read_all._from_environ")
    from_environ.return_value = ()
    cfg = ag.gather_config(AllTypes, override_defaults=all_values)
    from_environ.assert_called_once()  # with script file name
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values
    from_environ.reset_mock()
    cfg = ag.gather_config(AllTypes,
                           override_defaults=all_values,
                           env_var_prefix='-')
    from_environ.assert_not_called()  # with script file name
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values


def test_gather_config_no_files(mocker):
    """When config_files==[] or None, no config lookup."""
    mocker.patch("sys.argv", ["script"])
    from_files = mocker.patch("msrc.appconfig.read_all._from_file")
    from_files.return_value = ()
    cfg = ag.gather_config(AllTypes, override_defaults=all_values)
    from_files.assert_not_called()  # with script file name
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values
    from_files.reset_mock()
    cfg = ag.gather_config(AllTypes,
                           override_defaults=all_values,
                           config_files=[])
    from_files.assert_not_called()  # with script file name
    assert isinstance(cfg, AllTypes)
    assert ag.to_dict(cfg) == all_values


def test_environ(mocker):
    mocker.patch.dict("os.environ", {"test_element": "a string"})
    observed = ag.from_environ(SampleConfig, "test_")
    assert observed == dict(element="a string")


def test_from_dict():
    observed = ag.from_dict(AllTypes, all_values)
    assert isinstance(observed, AllTypes)


def test_to_dict_include_defaults():
    probe = WithDefaults()
    assert ag.to_dict(probe) == {}
    assert ag.to_dict(probe, include_defaults=True) == {"a": 999}
    probe = WithDefaults(a=888)
    assert ag.to_dict(probe) == {"a": 888}
    assert ag.to_dict(probe, include_defaults=True) == {"a": 888}
    probe = WithNestedDefaults()
    assert ag.to_dict(probe) == {}
    assert ag.to_dict(probe, include_defaults=True) == {"nested": {"a": 999}}


def test_to_argv():
    expct = ag.gather_config(AllTypes, override_defaults=all_values, argv=[])
    args = ag.to_argv(expct)
    observed = ag.gather_config(AllTypes, argv=args)
    assert observed == expct
    probe = mk_class(("f", float))
    expct = ag.gather_config(probe, override_defaults=dict(f=-2e21), argv=[])
    args = ag.to_argv(expct)
    observed = ag.gather_config(probe, argv=args)
    assert observed == expct
    expct = ag.gather_config(probe, override_defaults=dict(f=-math.inf),
                             argv=[])
    args = ag.to_argv(expct)
    observed = ag.gather_config(probe, argv=args)
    assert observed == expct
