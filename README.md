# datasette-insert-api

[![PyPI](https://img.shields.io/pypi/v/datasette-insert-api.svg)](https://pypi.org/project/datasette-insert-api/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-insert-api?label=changelog)](https://github.com/simonw/datasette-insert-api/releases)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/datasette-insert-api/blob/master/LICENSE)

Datasette plugin providing an API for inserting and updating data

## Installation

Install this plugin in the same environment as Datasette.

    $ pip install datasette-insert-api

## Usage

Having installed the plugin, data can be inserted or updated and tables can be created by POSTing JSON data to the following URL:

    /-/insert/name-of-database/name-of-table

The JSON should look like this:

```json
[
    {
        "id": 1,
        "name": "Cleopaws",
        "age": 5
    },
    {
        "id": 2,
        "name": "Pancakes",
        "age": 5
    }
]
```

The first time data is posted to the URL a table of that name will be created if it does not aready exist, with the desired columns.

You can specify which column should be used as the primary key using the `?pk=` URL argument.

Here's how to POST to a database and create a new table using the Python `requests` library:

```python
import requests

requests.post("http://localhost:8001/-/insert/unsafe/dogs?pk=id", json=[
    {
        "id": 1,
        "name": "Cleopaws",
        "age": 5
    },
    {
        "id": 2,
        "name": "Pancakes",
        "age": 4
    }
])
```
And here's how to do the same thing using `curl`:

```
curl --request POST \
  --data '[
      {
        "id": 1,
        "name": "Cleopaws",
        "age": 5
      },
      {
        "id": 2,
        "name": "Pancakes",
        "age": 4
      }
    ]' \
    'http://localhost:8001/-/insert/unsafe/dogs?pk=id'
```

### Inserting a single row

If you are inserting a single row you can optionally send it as a dictionary rather than a list with a single item:

```
curl --request POST \
  --data '{
      "id": 1,
      "name": "Cleopaws",
      "age": 5
    }' \
    'http://localhost:8001/-/insert/unsafe/dogs?pk=id'
```

### Automatically adding new columns

If you send data to an existing table with keys that are not reflected by the existing columns, you will get an HTTP 400 error with a JSON response like this:

```json
{
    "status": 400,
    "error": "Unknown keys: 'foo'",
    "error_code": "unknown_keys"
}
```

If you add `?alter=1` to the URL you are posting to any missing columns will be automatically added:

```
curl --request POST \
  --data '[
      {
        "id": 3,
        "name": "Boris",
        "age": 1,
        "breed": "Husky"
      }
    ]' \
    'http://localhost:8001/-/insert/unsafe/dogs?alter=1'
```

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:

    cd datasette-insert-api
    python3 -mvenv venv
    source venv/bin/activate

Or if you are using `pipenv`:

    pipenv shell

Now install the dependencies and tests:

    pip install -e '.[test]'

To run the tests:

    pytest
