import setuptools
import datetime
import cli.nuttercli as nuttercli

with open("README.md", "r") as fh:
    long_description = fh.read()

version = nuttercli.get_cli_version()
setuptools.setup(
    name="nutter",
    version=version,
    author="Jesus Aguilar, Rob Bagby",
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
    python_requires='>=3.5.2',
)