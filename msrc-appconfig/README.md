# msrc-appconfig

Type safe composable configuration management in Python

[![Build Status](https://msrcambridge.visualstudio.com/One/_apis/build/status/msrc-appconfig%20PR%20GATE?branchName=master)](https://msrcambridge.visualstudio.com/One/_build/latest?definitionId=455&branchName=master) [![msrc-appconfig package in One feed in Azure Artifacts](https://msrcambridge.feeds.visualstudio.com/_apis/public/Packaging/Feeds/90c888ee-b2dc-4533-bef8-63fef8df24bf/Packages/3867b4b4-d9c9-4b77-877d-499652c5eb2b/Badge)](https://msrcambridge.visualstudio.com/One/_packaging?_a=package&feed=90c888ee-b2dc-4533-bef8-63fef8df24bf&package=3867b4b4-d9c9-4b77-877d-499652c5eb2b&preferRelease=true)

The package orchestrates application configuration from multiple sources: 
built-in application defaults; .ini, JSON and YAML configuration files;
shell environment variables; command line arguments.

All configuration values are checked and converted to proper type allowing for
safer use in application code.

The module allows to set up a configuration as a global shared configuration object
easily accessible from different parts of application code.

The configuration object can also be serialized and shared across processes
locally and in the Cloud.

## Getting started

Install the package with `pip install msrc-appconfig`. You may first need
to configure `pip` to lookup the "One" feed. Click on the PyPi icon above,
then "Connect to feed" button, choose Python in the left navigation column 
and follow the instructions.

Configuration schema is a class definition with typed attributes and built-in defaults.
```python
import typing

class AppConfig(typing.NamedTuple):
    app_name: str = "Sample"
    repeat: int = 1
```

To compile configuration object from this schema use `gather_config` function.
```python
from msrc.appconfig import gather_config

def main(app_config: AppConfig):
    for i in range(app_config.repeat):
        print("Hello from", app_config.app_name)


if __name__ == '__main__':
    app_config = gather_config(AppConfig, arg_aliases=dict(n='app_name'))
    main(app_config)
```

If the above code is in a file named `getting_started.py`, then you may already run it:
```
>python getting_started.py 
INFO:msrc.appconfig:logging level set to INFO.
Hello from Sample
```

Now try the following commands:
```
>python sample.py -h
usage: getting_started.py [-h [OPTION]] [-l LEVEL|FILE]
                          [-c CONF_FILE [CONF_FILE ...]] [-e PREFIX]

optional arguments:
  -h [OPTION], --help [OPTION]
                        Prints this help message and optionally description of an     
                        option.
  -l LEVEL|FILE         Either logging level or a path to a logging configuration     
                        file.
  -c CONF_FILE [CONF_FILE ...]
                        Additional configuration files. Allowed formats are JSON or   
                        YAML.
  -e PREFIX             Prefix for shell variables to look at. If environment
                        contains <PREFIX>_<ELEMENT_NAME>=VALUE the VALUE
                        overrides corresponding configuration element. The
                        default prefix is GETTING_STARTED_. A prefix of sole
                        dash disables the environment lookup.
Additionally, you may specify the following options. Use '--help OPTION_NO_DASHES' to 
get help on an option marked (*).
-n STR, --app_name STR, --app-name STR
--repeat INT

>GETTING_STARTED_REPEAT=3 python getting_started.py -l debug -n "another example"
INFO:msrc.appconfig:logging level set to DEBUG.
DEBUG:msrc.appconfig:Examining shell variables starting with GETTING_STARTED_.
DEBUG:msrc.appconfig:Shell variable GETTING_STARTED_repeat=3.
DEBUG:msrc.appconfig:discovered app_name = 'another example' from argv
INFO:msrc.appconfig:final repeat = 3 from env > GETTING_STARTED_repeat
INFO:msrc.appconfig:final app_name = 'another example' from argv
Hello from another example
Hello from another example
Hello from another example
```
The last command shows you may use environment variables to set configuration values.
On Windows the example should be run with two commands. First, set the environment
variable with `SET GETTING_STARTED_REPEAT=3`, and then run python script as shown.

You may also place configuration values in files and specify these file names in
code or on command line. For example, create a file named `sample.yaml`:
```yaml
app_name: getting started
repeat: 2
``` 
and continue the command line session (on Windows, first unset the environment
variable with `SET GETTING_STARTED_REPEAT=`):
```
>python getting_started.py -l warn -c sample.yaml
Hello from getting started
Hello from getting started
```
Note also that with `-l` argument you control the amount of details being logged.
The optional function argument `gather_config(log_level=logging.WARN,...)` has
similar effect.

## Configuration Schema

A schema is a class definition that serves as a template for application configuration.
The package uses introspection to build a list of configuration schema elements
and then reads configuration data from different sources.

Out of the box the package accepts configuration schema created with `typing.NamedTuple`.
The example above shows that for each of its elements configuration schema contains a name,
a type and a default value. The default value is optional, although you should be cautious
mixixng elements with and without default values. For named tuples all elements without
default values must come before elements with default values.
If an element doesn't have a default, its value must be present in one of configuration sources.
Otherwise `gather_config()` stops running the script.

The package accepts elements of the following types only:

* Simple types: `str`, `int`, `float`, `bool`, any [enumeration](https://docs.python.org/3/library/enum.html).
* Uniform tuples of simple types. These are annotated with [`typing.Tuple`](https://docs.python.org/3/library/typing.html#typing.Tuple) generic type.
  E.g., `Tuple[int, int]` is a pair of integers, `Tuple[str, ...]` is a tuple of strings
  of any length including empty tuple.
* Other application configuration schema class. This allows composition of schemas.

All other types will raise an error in call to `gather_config()`
and other package functions requiring introspection.

### Optional metadata
Metadata field | Description
------|------------
help | Description of the element used in UI.
is_secret | If True, the element value is obfuscated in logs.

### Available plugins

Appconfig plugins allow alternative mechanisms to declare application configuration
schema in addition to named tuples.

#### Dataclasses

`msrc.appconfig.dataclasses` is available for python version 3.7 and above. 
It allows for more flexible configuration declaration using [`@dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass) decorator. 
Compared to named tuples this approach allows building inheritance trees
of application configuration. It's a good practice to declare application configuration
as a "frozen" object. This prevents accidentally changing configuration values
along the application run.
Here is a sample declaration of an appconfig schema using `dataclasses`:

```python
from dataclasses import dataclass, field

@dataclass(frozen=True)
class AppConfig:
    no_default: str
    with_default: repeat = 3
    with_help: bool = field(default=False, metadata=dict(help="description of the flag"))
    secret_password: str = attr.id(repr=False)
```

To use `dataclasses` schema specify the extra when installing msrc.appconfig:

    >pip install msrc-appconfig[dataclasses]

Alternatively, install `msrc-appconfig-dataclasses` as a separate package.

#### Attrs

`msrc.appconfig.attrs` takes additional external dependency on [attrs](https://www.attrs.org/).

This package is a predecessor of `dataclasses`. It works on all versions of Python
and is even more flexible. Here is a way to declare an appconfig schema using `attrs`:

```python
import attrs

@attr.s(frozen=True, kw_only=True, auto_attribs=True)
class AppConfig:
    no_default: str
    with_default: repeat = 3
    with_help: bool = attr.ib(default=False, metadata=dict(help="description of the flag"))
    secret_password: str = attr.id(repr=False)
```

To use `attrs` schema specify the extra when installing msrc.appconfig:

    >pip install msrc-appconfig[attrs]

Alternatively, install `msrc-appconfig-attrs` as a separate package.

#### Param

`msrc.appconfig.param` takes additional external dependency on [`param`](https://pypi.org/project/param) package.
Application configuration classes must inherit from `param.Parameterized`.
For fixed size tuples the `param` package have support for `float` type only (`ParamNumeric()`). 
Tuples of unbound size are encoded as `ParamList(class_=<type>)`.

To use `param` schema specify the extra when installing msrc.appconfig:

    >pip install msrc-appconfig[param]

Alternatively, install `msrc-appconfig-param` as a separate package.


## Configuration sources

The default configuration source is the schema itself where you define default values.
The values are overriden with the following order:
- `override_defaults` dictionary in `gather_config()` arguments;
- configuration files;
- shell variables a.k.a. environment variables;
- command line arguments.

### Files

The module reads `configparser` (`.ini`), JSON (`.json`) and YAML (`.yaml`, `.yml`) files.

The list of files to be read can be specified using `config_files` optional
argument: `gather_config(config_files=[...], ...)`, and with `-c` command line option which
take one or more file paths. Note though that relative paths are resolved against
main script directory for `config_files=` and against current working directory for `-c`.

You may enable a default configuration file with a utility function:
`gather_config(config_files=script_config_file(), ...)`
If you now run `python sample.py` the default configuration file can
be `sample.yaml` (or `.json`, or `.ini`, or `.yml`) 
in the same directory as the `sample.py` script.
If you run `python -m msrc.example` the file can be `example.json` (or `.yaml`, or `.ini`)
in current directory.

Another utility function makes it easy to use hierarchical configurations. If you start a script
`/foo/bar/script.py`, and the script calls
`gather_config(config_files=config_files_in_parents('config.json'), ...)`, then the function
will look for `/config.json`,`/foo/config.json`,`/foo/bar/config.json` and will read these
files in this order if they exist.

In any configuration file you may also reference other configuration files
using `_include` element. The value of this element is a path or a list of paths to read.
Relative paths are resolved againsth the location of the including file.
The included files are read before processing the rest of the parent file,
i.e. other elements in the file may override values from those mentioned in `_include`.

### Shell variables

Shell variables with names like `<prefix><element> = <value>` override a value
of a configuration element `<element>`.
If you run `python sample.py` then the default prefix is `SAMPLE_`.
If you run `python -m msrc.example` then the prefix is `EXAMPLE_`.
You can also specify another prefix with `env_var_prefix=` function argument 
or `-e` command line option. A single hyphen sign has a special meaning,
it disables the use of environment variables. 

For tuples shell variable value should contain all tuple values separated by space.
E.g. for a script `script.py` to specify a pair of numbers 
as a value of a configuration element named `limits`
the environment variable may look like `script_limits=-1.5 2.56`.
If the tuple type is str, and a string value must have a space in it
put the value in double quotes, quoting double quotes themselves with `'\"'`
and the backslash with `'\\'`, e.g.
`script_paths=C:\Windows "\"C:\\Program Files\""`


### Command line arguments

For floating point values any valid positive number works ok as well as special values
`nan` and `inf`. Negative numbers start with minus sign, `argparse` considers them
an option rather than a value. A workaround is to place space in front of the value,
e.g. `python script.py --interval " -1.5" 2.5`.

For enums you may supply either a enum name or it value, preference given to names.

For tuples the option expects multiple arguments.

Boolean elements whith `False` as default value may be used as flags,
i.e. if the option is present with no arguments, the value of the element is set to `True`.
In any case you may also supply an argument. 
Any string that starts with 't' or 'y' is interpreted as `True`, for example `'true'` or `'Yes'`.
Any string that starts with 'f' or 'n' is interpreted as `False`, for example `'F'` or `'no'`.
