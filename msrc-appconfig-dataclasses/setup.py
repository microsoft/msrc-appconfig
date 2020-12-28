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

long_description = Path("README.md").read_text()

setuptools.setup(
    name="msrc-appconfig-dataclasses",
    version=package_version,
    author="Vassily Lyutsarev",
    author_email="vassilyl@microsoft.com",
    description="Plugin for msrc-appconfig.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://aka.ms/msrc-appconfig",
    packages=setuptools.find_namespace_packages(
        include=["msrc.*"]),
    install_requires=["msrc-appconfig"],
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
