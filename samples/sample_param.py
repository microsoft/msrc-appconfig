"""The script shows tips to using param-based configuration schema.

- Inheritance BaseConfig -> TheConfig
- Composition, including missing different schemas.

The sample_config.ini file can be used to initialize the configuration.
For example, try the following invocation:
>python sample_param.py -c sample_config.ini --appconfig.repeat 3
"""
import typing

import param

from msrc.appconfig import gather_config


class AppConfig(typing.NamedTuple):
    app_name: str = "Sample"
    repeat: int = 1


class BaseConfig(param.Parameterized):
    base_string: str = typing.cast(str, param.String(
        doc="A sample configuration element of type string."))


#  Always put place Parameterized the last in the list of base classes
class TheConfig(BaseConfig, param.Parameterized):
    appconfig: AppConfig = typing.cast(  # cast is an identity function
        AppConfig,
        param.ClassSelector(AppConfig, default=AppConfig()))


def main(app_config: AppConfig, arg: str):
    print("Base string has been configured to %r" % arg)
    for i in range(app_config.repeat):
        print("Hello from", app_config.app_name)


if __name__ == '__main__':
    app_config = gather_config(TheConfig,
                               arg_aliases=dict(n="appconfig.app_name"))
    main(app_config.appconfig, app_config.base_string)
