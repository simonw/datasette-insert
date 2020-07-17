from setuptools import setup
import os

VERSION = "0.1a"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-update-api",
    description="Datasette plugin providing an API for updating data",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-update-api",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-update-api/issues",
        "CI": "https://github.com/simonw/datasette-update-api/actions",
        "Changelog": "https://github.com/simonw/datasette-update-api/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_update_api"],
    entry_points={"datasette": ["update_api = datasette_update_api"]},
    install_requires=["datasette", "sqlite-utils"],
    extras_require={"test": ["pytest", "pytest-asyncio", "httpx"]},
    tests_require=["datasette-update-api[test]"],
)
