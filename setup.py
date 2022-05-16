from setuptools import setup
import os

VERSION = "0.6"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-insert",
    description="Datasette plugin for inserting and updating data",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://datasette.io/plugins/datasette-insert",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-insert/issues",
        "CI": "https://github.com/simonw/datasette-insert/actions",
        "Changelog": "https://github.com/simonw/datasette-insert/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_insert"],
    entry_points={"datasette": ["insert = datasette_insert"]},
    install_requires=["datasette>=0.46", "sqlite-utils"],
    extras_require={
        "test": ["pytest", "pytest-asyncio", "httpx", "datasette-auth-tokens"]
    },
    python_requires=">=3.7",
)
