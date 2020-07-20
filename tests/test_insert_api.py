from datasette.app import Datasette
import sqlite_utils
import pytest
import httpx


@pytest.fixture
def db_path(tmp_path_factory):
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "data.db"
    db = sqlite_utils.Database(db_path)
    db.vacuum()
    return db_path


@pytest.fixture
def ds(db_path):
    return Datasette([db_path])


@pytest.fixture
def ds_root_only(db_path):
    return Datasette(
        [db_path],
        metadata={
            "plugins": {
                "datasette-insert-api": {"allow": {"bot": "test"}},
                "datasette-auth-tokens": {
                    "tokens": [{"token": "test-bot", "actor": {"bot": "test"}}]
                },
            }
        },
    )


@pytest.mark.asyncio
async def test_plugin_is_installed(ds):
    app = ds.app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/plugins.json")
        assert 200 == response.status_code
        installed_plugins = {p["name"] for p in response.json()}
        assert "datasette-insert-api" in installed_plugins
        # Check we have our testing dependency too:
        assert "datasette-auth-tokens" in installed_plugins


@pytest.mark.parametrize(
    "input,pk,expected",
    # expected=None means reuse the inpt as the expected
    [
        (
            [
                {"id": 3, "name": "Cleopaws", "age": 5},
                {"id": 11, "name": "Pancakes", "age": 4},
            ],
            "id",
            None,
        ),
        # rowid example:
        (
            [{"name": "Cleopaws", "age": 5}, {"name": "Pancakes", "age": 4}],
            None,
            [
                {"rowid": 1, "name": "Cleopaws", "age": 5},
                {"rowid": 2, "name": "Pancakes", "age": 4},
            ],
        ),
        # Single row
        (
            {"id": 1, "name": "Cleopaws", "age": 5},
            "id",
            [{"id": 1, "name": "Cleopaws", "age": 5}],
        ),
        (
            {"name": "Cleopaws", "age": 5},
            None,
            [{"rowid": 1, "name": "Cleopaws", "age": 5}],
        ),
    ],
)
@pytest.mark.asyncio
async def test_insert_creates_table(ds, input, pk, expected):
    app = ds.app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.post(
            "http://localhost/-/insert/data/newtable{}".format(
                "?pk={}".format(pk) if pk else ""
            ),
            json=input,
        )
        assert 200 == response.status_code
        assert {"table_count"} == set(response.json().keys())
        # Read that table data
        response2 = await client.get(
            "http://localhost/data/newtable.json?_shape=array",
        )
        assert 200 == response2.status_code
        assert (expected or input) == response2.json()


@pytest.mark.asyncio
async def test_insert_alter(ds):
    async with httpx.AsyncClient(app=ds.app()) as client:
        response = await client.post(
            "http://localhost/-/insert/data/dogs?pk=id",
            json=[{"id": 3, "name": "Cleopaws", "age": 5}],
        )
        assert 200 == response.status_code
        assert (await rows(client)) == [
            {"id": 3, "name": "Cleopaws", "age": 5},
        ]
        # Should throw error without alter
        response2 = await client.post(
            "http://localhost/-/insert/data/dogs",
            json=[{"id": 3, "name": "Cleopaws", "age": 5, "weight_lb": 51.1}],
        )
        assert 400 == response2.status_code
        # Insert with an alter
        response3 = await client.post(
            "http://localhost/-/insert/data/dogs?alter=1",
            json=[{"id": 3, "name": "Cleopaws", "age": 5, "weight_lb": 51.1}],
        )
        assert 200 == response3.status_code
        assert (await rows(client)) == [
            {"id": 3, "name": "Cleopaws", "age": 5, "weight_lb": 51.1},
        ]


@pytest.mark.asyncio
async def test_permission_denied(ds_root_only):
    async with httpx.AsyncClient(app=ds_root_only.app()) as client:
        response = await client.post(
            "http://localhost/-/insert/data/dogs?pk=id",
            json=[{"id": 3, "name": "Cleopaws", "age": 5}],
        )
        assert 403 == response.status_code


@pytest.mark.asyncio
async def test_permission_allowed(ds_root_only):
    async with httpx.AsyncClient(app=ds_root_only.app()) as client:
        response = await client.post(
            "http://localhost/-/insert/data/dogs?pk=id",
            json=[{"id": 3, "name": "Cleopaws", "age": 5}],
            headers={"Authorization": "Bearer test-bot"},
        )
        assert 200 == response.status_code
        assert (await rows(client)) == [
            {"id": 3, "name": "Cleopaws", "age": 5},
        ]


async def rows(client):
    return (await client.get("http://localhost/data/dogs.json?_shape=array")).json()
