# datasette-update-api

[![PyPI](https://img.shields.io/pypi/v/datasette-update-api.svg)](https://pypi.org/project/datasette-update-api/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-update-api?label=changelog)](https://github.com/simonw/datasette-update-api/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-update-api/blob/master/LICENSE)

Datasette plugin providing an API for updating data

## Installation

Install this plugin in the same environment as Datasette.

    $ pip install datasette-update-api

## Usage

Usage instructions go here.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-update-api
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest
