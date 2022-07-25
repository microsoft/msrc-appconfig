import os
from pathlib import Path

import setuptools

# Major part is in a file
here = os.getenv("GITHUB_WORKSPACE") or Path.cwd()
version_file = Path(here, "VERSION.txt")
if not version_file.is_file():
    version_file = Path(Path(here).parent, "VERSION.txt")
package_version = version_file.read_text().strip()
long_description = Path("README.md").read_text()

setuptools.setup(
    name="msrc-appconfig",
    version=package_version,
    author="Vassily Lyutsarev",
    author_email="vassilyl@microsoft.com",
    description="Orchestrates application configuration from config files, "
    "shell variables and command line arguments.",
    license="MIT License",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/microsoft/msrc-appconfig",
    packages=setuptools.find_namespace_packages(include=[
        "msrc.appconfig",
        "msrc.appconfig_decl"
    ]),
    install_requires=[
        "ruamel.yaml",
        "typing_extensions"
    ],
    extras_require={
        "attrs": ["msrc-appconfig-attrs=="+package_version],
        "dataclasses": ["msrc-appconfig-dataclasses=="+package_version],
        "param": ["msrc-appconfig-param=="+package_version]
    },
    package_data={
        "msrc.appconfig": ["py.typed"],
        "msrc.appconfig_decl": ["py.typed"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
