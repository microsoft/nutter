import setuptools
import common.utils as utils

with open("README.md", "r") as fh:
    long_description = fh.read()

version = utils.get_nutter_version()


def parse_requirements(filename):
    """Load requirements from a pip requirements file."""
    lineiter = (line.strip() for line in open(filename))
    return [line for line in lineiter if line and not line.startswith("#")]


setuptools.setup(
    name="nutter",
    version=version,
    author="Jesus Aguilar, Rob Bagby",
    install_requires=parse_requirements("requirements.txt"),
    author_email="jesus.aguilar@microsoft.com, rob.bagby@microsoft.com",
    description="A databricks notebook testing library",
    long_description="A databricks notebook testing library",
    long_description_content_type="text/markdown",
    entry_points={
        'console_scripts': [
            'nutter = cli.nuttercli:main'
        ]},
    url="https://github.com/microsoft/nutter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8.0',
)
