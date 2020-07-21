from setuptools import setup
import os

VERSION = "0.4"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="datasette-insert-api",
    description="Datasette plugin providing an API for inserting and updating data",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/simonw/datasette-insert-api",
    project_urls={
        "Issues": "https://github.com/simonw/datasette-insert-api/issues",
        "CI": "https://github.com/simonw/datasette-insert-api/actions",
        "Changelog": "https://github.com/simonw/datasette-insert-api/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["datasette_insert_api"],
    entry_points={"datasette": ["insert_api = datasette_insert_api"]},
    install_requires=["datasette", "sqlite-utils"],
    extras_require={
        "test": ["pytest", "pytest-asyncio", "httpx", "datasette-auth-tokens"]
    },
    tests_require=["datasette-insert-api[test]"],
)
