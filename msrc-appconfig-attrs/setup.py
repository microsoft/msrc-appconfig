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
    name="msrc-appconfig-attrs",
    version=package_version,
    author="Vassily Lyutsarev",
    author_email="vassilyl@microsoft.com",
    description="Plugin for msrc-appconfig.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/microsoft/msrc-appconfig",
    packages=setuptools.find_namespace_packages(
        include=["msrc.appconfig_decl"]),
    install_requires=["msrc-appconfig", "attrs"],
    classifiers=[
        "Programming Language :: Python :: 3",
        # "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
