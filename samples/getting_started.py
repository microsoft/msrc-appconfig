import typing

from msrc.appconfig import gather_config


class AppConfig(typing.NamedTuple):
    app_name: str = "Sample"
    repeat: int = 1


def main(app_config: AppConfig):
    for i in range(app_config.repeat):
        print("Hello from", app_config.app_name)


if __name__ == '__main__':
    app_config = gather_config(AppConfig, arg_aliases=dict(n='app_name'))
    main(app_config)
