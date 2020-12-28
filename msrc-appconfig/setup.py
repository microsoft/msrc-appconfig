import os
from pathlib import Path

import setuptools

# Major part is in a file
here = os.getenv("BUILD_SOURCESDIRECTORY") or Path.cwd()
version_file = Path(here, "VERSION.txt")
if not version_file.is_file():
    version_file = Path(Path(here).parent, "VERSION.txt")
base_version = version_file.read_text().strip()
build_id = os.getenv("BUILD_BUILDID")
is_final_env = os.getenv("IsFinalRelease")
is_final = isinstance(is_final_env, str) and is_final_env.lower() == 'true'
dev_version = (
    '' if build_id is None or is_final
    else ".dev" + build_id
)

# The full version of the package that we are creating is later needed
# for running pytest, because we want to install the newly created package
# from the feed.
package_version = base_version + dev_version

# See also 'publish_to_artifacts.yaml',
# https://docs.microsoft.com/en-us/azure/devops/pipelines/process/variables?view=azure-devops&tabs=yaml%2Cbatch#set-a-job-scoped-variable-from-a-script
print("##vso[task.setvariable variable=version;isOutput=true]%s"
      % package_version)

long_description = Path("README.md").read_text()

setuptools.setup(
    name="msrc-appconfig",
    version=package_version,
    author="Vassily Lyutsarev",
    author_email="vassilyl@microsoft.com",
    description="Orchestrates application configuration from config files, "
    "shell variables and command line arguments.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://aka.ms/msrc-appconfig",
    packages=setuptools.find_namespace_packages(include=[
        "msrc.appconfig",
        "msrc.appconfig_decl"
    ]),
    install_requires=[
        "ruamel.yaml"
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
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
