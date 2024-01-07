# MSRC Appconfig project

![Check and test code](https://github.com/microsoft/msrc-appconfig/workflows/Check%20and%20test%20code/badge.svg)
![PyPI](https://img.shields.io/pypi/v/msrc-appconfig)

Type-safe composable application configuration management in Python

Application configuration is a set of values that depend on execution environment and/or user intent,
such as path to data location, database password or maximum number of iterations.

Good programming practice is to keep configuration values separate from application code.
Python standard library has tools to achieve this:

- `argparse` for values that change often from run to run;
- `sys.environ` more stable values that do not change between runs in the same environment;
- `configparser`, `json` to keep sets of values in separate files.

There is no good solution though to the use of the above tools together.
For example, you need quite a lot of code if you want
to be able to override a value that comes from a `.json` file with a command line option.

The `msrc-appconfig` project aims to fill this gap.
You declare application configuration schema as a class with attributes and type annotations.
The package queries multiple sources to discover configuration values
and to override them if necessary in a predictable way. 
In return you receive configuration object as an instance of the schema.
You can pass the configuration object over the call tree,
use it as a global shared instance,
or pass between processes, locally and in the cloud.

## Getting Started

`samples/getting_started.py`:
```python
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
```
The package supports Python >= 3.7. 
You may consider creating and activating a temporary virtual environment using any tool of your choice.
Here is a sample session that connects to private PyPI feed,
installs `msrc-appconfig` package and runs `getting_started.py` script.
```
>pip install msrc-appconfig
>python getting_started.py
INFO:msrc.appconfig:logging level set to INFO.
Hello from Sample

>python getting_started.py -h
usage: getting_started.py [-h [OPTION]] [-l LEVEL|FILE]
                          [-c CONF_FILE [CONF_FILE ...]] [-e PREFIX]

optional arguments:
  -h [OPTION], --help [OPTION]
                        Prints this help message and optionally description of
                        an option.
  -l LEVEL|FILE         Either logging level or a path to a logging
                        configuration file. The default is INFO.
  -c CONF_FILE [CONF_FILE ...]
                        Additional configuration files. Allowed formats are
                        JSON or YAML.
  -e PREFIX             Prefix for shell variables to look at. If environment
                        contains <PREFIX>_<ELEMENT_NAME>=VALUE the VALUE
                        overrides corresponding configuration element. The
                        default prefix is GETTING_STARTED_. A prefix of sole
                        dash disables the environment lookup.
Additionally, you may specify the following options. Use '--help OPTION_NO_DASHES' to get help on an option marked (*).
-n STR, --app_name STR, --app-name STR
--repeat INT

```
Now create configuration file `sample.yaml` with just two lines:
```yaml
app_name: getting started
repeat: 2
``` 
and continue the command line session:
```
>python getting_started.py -c sample.yaml
INFO:msrc.appconfig:logging level set to INFO.
INFO:msrc.appconfig:final app_name = 'getting started' from file > C:/.../sample.yaml
INFO:msrc.appconfig:final repeat = 2 from file > C:/.../sample.yaml
Hello from getting started
Hello from getting started

>python getting_started.py -l debug -c sample.yaml --repeat 3
INFO:msrc.appconfig:logging level set to DEBUG.
DEBUG:msrc.appconfig:start processing config file C:\...\sample.yaml
DEBUG:msrc.appconfig:successfully loaded C:\...\sample.yaml
DEBUG:msrc.appconfig:discovered app_name = 'getting started' from file > C:\...\sample.yaml
DEBUG:msrc.appconfig:discovered repeat = 2 from file > C:\...\sample.yaml     
DEBUG:msrc.appconfig:end processing conf file C:\...\sample.yaml
DEBUG:msrc.appconfig:Examining shell variables starting with GETTING_STARTED_.
DEBUG:msrc.appconfig:discovered repeat = 3 from argv
INFO:msrc.appconfig:final app_name = 'getting started' from file > C:\...\sample.yaml
INFO:msrc.appconfig:final repeat = 3 from argv
Hello from getting started
Hello from getting started
Hello from getting started

>
```

The repository contains code of the main package `msrc-appconfig` and its plugins.
Please refer to the main [README](./msrc-appconfig/README.md) Getting Started section for
more details.
The [API](./API.md) document contains an overview of top level functions.


## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

The project has adopted [PEP 8](https://www.python.org/dev/peps/pep-0008/) style for code.
We use [flake8](https://pypi.org/project/flake8/) with default options to lint the code.
Additionally, the [pyright](https://github.com/microsoft/pyright) static type checker must run without issues on the code.

To get quickly get started with VSCode consider importing `msrc-appconfig.code-profile`
and create python environment from `dev-requirements.txt`.

All new code must come with corresponding [pytest](https://docs.pytest.org/en/latest/) tests.
Keep code coverage at 100%.

All API changes must be documented with markdown doc strings.
Run api_md.py to update [the package API](API.md).

The project adopts [semantic versioning](https://semver.org/).
Version number is in VERSION.txt file.
To release a new package version update the version file and create github release.