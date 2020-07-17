from datasette.app import Datasette
import sqlite_utils
import pytest
import httpx


@pytest.fixture
def ds(tmp_path_factory):
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "data.db"
    db = sqlite_utils.Database(db_path)
    db.vacuum()
    ds = Datasette([db_path])
    return ds


@pytest.mark.asyncio
async def test_plugin_is_installed(ds):
    app = ds.app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.get("http://localhost/-/plugins.json")
        assert 200 == response.status_code
        installed_plugins = {p["name"] for p in response.json()}
        assert "datasette-update-api" in installed_plugins


@pytest.mark.asyncio
async def test_insert_creates_table(ds):
    app = ds.app()
    async with httpx.AsyncClient(app=app) as client:
        response = await client.post(
            "http://localhost/-/update/data/newtable?pk=id",
            json=[
                {"id": 3, "name": "Cleopaws", "age": 5},
                {"id": 11, "name": "Pancakes", "age": 4},
            ],
        )
        assert 200 == response.status_code
        assert {"table_count": 2} == response.json()
        # Read that table data
        response2 = await client.get(
            "http://localhost/data/newtable.json?_shape=array",
        )
        assert 200 == response2.status_code
        assert [
            {"id": 3, "name": "Cleopaws", "age": 5},
            {"id": 11, "name": "Pancakes", "age": 4},
        ] == response2.json()
