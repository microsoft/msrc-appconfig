import os
from typing import Tuple
from msrc.appconfig.schema import Schema, ConfigValue
from msrc.appconfig.logger import logger
"""Reads configuration values from shell variables."""


def from_environ(
        schema: Schema[object],
        prefix: str
) -> Tuple[ConfigValue, ...]:
    """Tries to read config elements from os shell variables.

    Variable name should match <prefix><config_element_name>.
    For tuples the value must be a space delimited list.
    In that case an element of the list can be placed in double quotes
    and use two escape sequences: '\"' and '\\'
    """
    logger.debug("Examining shell variables starting with %s.", prefix)

    def generator():
        for name, element in schema.deep_items():
            env_key = prefix + ".".join(name)
            if env_key in os.environ:
                value = os.environ[env_key]
                logger.debug("Shell variable %s=%s.", env_key, value)
                yield ConfigValue(name, element.parse(value), ("env", env_key))
    return tuple(generator())
