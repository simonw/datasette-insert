# datasette-insert-api

[![PyPI](https://img.shields.io/pypi/v/datasette-insert-api.svg)](https://pypi.org/project/datasette-insert-api/)
[![Changelog](https://img.shields.io/github/v/release/simonw/datasette-insert-api?include_prereleases&label=changelog)](https://github.com/simonw/datasette-insert-api/releases)
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

You can create a new local empty database file by running one of the following commands:

    sqlite3 data.db vacuum
    # Or if you have sqlite-utils:
    sqlite-utils data.db vacuum

Then start Datasette locally like this:

    datasette data.db

Here's how to POST to a database and create a new table using the Python `requests` library:

```python
import requests

requests.post("http://localhost:8001/-/insert/data/dogs?pk=id", json=[
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
    'http://localhost:8001/-/insert/data/dogs?pk=id'
```
Or by piping in JSON like so:

    cat dogs.json | curl --request POST -d @- \
        'http://localhost:8001/-/insert/data/dogs?pk=id'

### Inserting a single row

If you are inserting a single row you can optionally send it as a dictionary rather than a list with a single item:

```
curl --request POST \
  --data '{
      "id": 1,
      "name": "Cleopaws",
      "age": 5
    }' \
    'http://localhost:8001/-/insert/data/dogs?pk=id'
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
    'http://localhost:8001/-/insert/data/dogs?alter=1'
```
## Permissions and authentication

This plugin does not require authentication by default.

This should be safe when running `datasette` on a local machine because Datasette defaults to only allowing localhost connections (`127.0.0.1`) and does not allow CORS requests.

If you plan to run this on a server somewhere, or you plan to enable JavaScript CORS access using the `--cors` Datasette option, you will need to take extra steps to secure the API.

You can read about [Datasette's approach to authentication](https://datasette.readthedocs.io/en/stable/authentication.html) in the Datasette manual.

I recommend using this plugin in conjunction with [datasette-auth-tokens](https://github.com/simonw/datasette-auth-tokens), which provides a mechanism for making authenticated calls using API tokens.

You can then use ["allow" blocks](https://datasette.readthedocs.io/en/stable/authentication.html#defining-permissions-with-allow-blocks) in the `datasette-insert-api` plugin configuration to specify which authenticated tokens are allowed to make use of the API.

Here's an example `metadata.json` file which restricts access to the `/-/insert` API to an API token defined in an `INSERT_TOKEN` environment variable:

```json
{
    "plugins": {
        "datasette-insert-api": {
            "allow": {
                "bot": "insert-bot"
            }
        },
        "datasette-auth-tokens": {
            "tokens": [
                {
                    "token": {
                        "$env": "INSERT_TOKEN"
                    },
                    "actor": {
                        "bot": "insert-bot"
                    }
                }
            ]
        }
    }
}
```
With this configuration in place you can start Datasette like this:

    INSERT_TOKEN=abc123 datasette data.db -m metadata.json

You can now send data to the API using `curl` like this:

```
curl --request POST \
  -H "Authorization: Bearer abc123" \
  --data '[
      {
        "id": 3,
        "name": "Boris",
        "age": 1,
        "breed": "Husky"
      }
    ]' \
    'http://localhost:8001/-/insert/data/dogs'
```

Or using the Python `requests` library like so:

```python
requests.post(
    "http://localhost:8001/-/insert/data/dogs",
    json={"id": 1, "name": "Cleopaws", "age": 5},
    headers={"Authorization": "bearer abc123"},
)
```

### Finely grained permissions

Using an `"allow"` block as described above grants full permission to the features enabled by the API.

The API implements several new Datasett permissions, which other plugins can use to make more finely grained decisions.

The full set of permissions are as follows:

- `insert-api:all` - all permissions - this is used by the `"allow"` block described above. Argument: `database_name`
- `insert-api:insert-update` - the ability to insert data into an existing table, or to update data by its primary key. Arguments: `(database_name, table_name)`
- `insert-api:create-table` - the ability to create a new table. Argument: `database_name`
- `insert-api:alter-table` - the ability to add columns to an existing table (using `?alter=1`). Arguments: `(database_name, table_name)`

You can use plugins like [datasette-permissions-sql](https://github.com/simonw/datasette-permissions-sql) to hook into these more detailed permissions for finely grained control over what actions each authenticated actor can take.

Plugins that implement the [permission_allowed()](https://datasette.readthedocs.io/en/stable/plugin_hooks.html#plugin-hook-permission-allowed) plugin hook can take full control over these permission decisions.

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
