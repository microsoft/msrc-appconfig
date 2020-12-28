"""The script shows tips to using attrs-based configuration schema.

- Inheritance BaseConfig -> TheConfig
- Composition, including missing different schemas.

The sample_config.ini file can be used to initialize the configuration.
For example, try the following invocation:
>python sample_attrs.py -c sample_config.ini --appconfig.repeat 3 -b "sample base"
"""  # noqa
from typing import NamedTuple

import attr
from msrc.appconfig import gather_config


class AppConfig(NamedTuple):
    app_name: str = "Sample"
    repeat: int = 1


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
# frozen: always optional, prevents accidental change of a shared config
# auto_attribs: optional here as all attributes are initialized with attr.ib()
# kw_only: recommended, allows to mix atrributes with and without defaults.
class BaseConfig():
    base_string: str = attr.ib('', metadata=dict(
        help="A sample configuration element of type string."))


@attr.s(frozen=True, auto_attribs=True, kw_only=True)
# auto_attribs: required here
class TheConfig(BaseConfig):
    appconfig: AppConfig = AppConfig()


def main(app_config: AppConfig, arg: str):
    print("Base string has been configured to %r" % arg)
    for i in range(app_config.repeat):
        print("Hello from", app_config.app_name)


if __name__ == '__main__':
    app_config = gather_config(
        TheConfig,
        arg_aliases=dict(n="appconfig.app_name", b="base_string")
    )
    main(app_config.appconfig, app_config.base_string)
