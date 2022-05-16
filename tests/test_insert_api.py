from datasette import hookimpl
from datasette.app import Datasette
from datasette.plugins import pm
import sqlite_utils
import pytest


@pytest.fixture
def db_path(tmp_path_factory):
    db_directory = tmp_path_factory.mktemp("dbs")
    db_path = db_directory / "data.db"
    db = sqlite_utils.Database(db_path)
    db.vacuum()
    return db_path


@pytest.fixture
def unsafe():
    class UnsafeInsertAll:
        __name__ = "UnsafeInsertAll"

        @hookimpl
        def permission_allowed(self, action):
            if action == "insert:all":
                return True

    pm.register(UnsafeInsertAll(), name="undo")
    yield
    pm.unregister(name="undo")


@pytest.fixture
def ds(db_path):
    return Datasette([db_path])


@pytest.fixture
def ds_root_only(db_path):
    return Datasette(
        [db_path],
        metadata={
            "plugins": {
                "datasette-insert": {"allow": {"bot": "test"}},
                "datasette-auth-tokens": {
                    "tokens": [{"token": "test-bot", "actor": {"bot": "test"}}]
                },
            }
        },
    )


@pytest.mark.asyncio
async def test_plugin_is_installed(ds):
    response = await ds.client.get("/-/plugins.json")
    assert response.status_code == 200
    installed_plugins = {p["name"] for p in response.json()}
    assert "datasette-insert" in installed_plugins
    # Check we have our testing dependency too:
    assert "datasette-auth-tokens" in installed_plugins


@pytest.mark.asyncio
async def test_permission_denied_by_default(ds):
    response = await ds.client.post(
        "/-/insert/data/newtable",
        json=[{"foo": "bar"}],
    )
    assert response.status_code == 403


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
async def test_insert_creates_table(ds, unsafe, input, pk, expected):
    app = ds.app()
    response = await ds.client.post(
        "/-/insert/data/newtable{}".format(
            "?pk={}".format(pk) if pk else ""
        ),
        json=input,
    )
    assert response.status_code == 200
    assert {"table_count"} == set(response.json().keys())
    # Read that table data
    response2 = await ds.client.get(
        "/data/newtable.json?_shape=array",
    )
    assert 200 == response2.status_code
    assert (expected or input) == response2.json()


@pytest.mark.asyncio
async def test_insert_alter(ds, unsafe):
    response = await ds.client.post(
        "/-/insert/data/dogs?pk=id",
        json=[{"id": 3, "name": "Cleopaws", "age": 5}],
    )
    assert response.status_code == 200
    assert (await rows(ds.client)) == [
        {"id": 3, "name": "Cleopaws", "age": 5},
    ]
    # Should throw error without alter
    response2 = await ds.client.post(
        "/-/insert/data/dogs",
        json=[{"id": 3, "name": "Cleopaws", "age": 5, "weight_lb": 51.1}],
    )
    assert 400 == response2.status_code
    # Insert with an alter
    response3 = await ds.client.post(
        "/-/insert/data/dogs?alter=1",
        json=[{"id": 3, "name": "Cleopaws", "age": 5, "weight_lb": 51.1}],
    )
    assert 200 == response3.status_code
    assert (await rows(ds.client)) == [
        {"id": 3, "name": "Cleopaws", "age": 5, "weight_lb": 51.1},
    ]


@pytest.mark.asyncio
async def test_missing_column_error(ds, unsafe):
    response = await ds.client.post(
        "/-/insert/data/dogs?pk=id",
        json=[{"id": 3, "name": "Cleopaws", "age": 5}],
    )
    assert response.status_code == 200
    response2 = await ds.client.post(
        "/-/insert/data/dogs?pk=id",
        json=[{"id": 3, "name": "Cleopaws", "age": 5, "size": "medium"}],
    )
    assert response2.status_code == 400
    assert response2.json() == {
        "status": 400,
        "error": "table dogs has no column named size",
        "error_code": "unknown_keys",
    }


@pytest.mark.asyncio
async def test_permission_denied_by_allow_block(ds_root_only):
    response = await ds_root_only.client.post(
        "/-/insert/data/dogs?pk=id",
        json=[{"id": 3, "name": "Cleopaws", "age": 5}],
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_permission_allowed_by_allow_block(ds_root_only):
    response = await ds_root_only.client.post(
        "/-/insert/data/dogs?pk=id",
        json=[{"id": 3, "name": "Cleopaws", "age": 5}],
        headers={"Authorization": "Bearer test-bot"},
    )
    assert response.status_code == 200
    assert (await rows(ds_root_only.client)) == [
        {"id": 3, "name": "Cleopaws", "age": 5},
    ]


@pytest.mark.parametrize(
    "permissions,try_action,expected_status,expected_msg",
    [
        # insert-update allowed
        (
            {
                "insert-update": True,
                "create-table": False,
                "alter-table": False,
            },
            "insert-update",
            200,
            None,
        ),
        # insert-update denied
        (
            {
                "insert-update": False,
                "create-table": False,
                "alter-table": False,
            },
            "insert-update",
            403,
            "Permission denied",
        ),
        # create-table allowed
        (
            {
                "insert-update": True,
                "create-table": True,
                "alter-table": False,
            },
            "create-table",
            200,
            None,
        ),
        # create-table denied
        (
            {
                "insert-update": True,
                "create-table": False,
                "alter-table": False,
            },
            "create-table",
            400,
            "Table dogs does not exist",
        ),
        # Alter table allowed
        (
            {
                "insert-update": True,
                "create-table": False,
                "alter-table": True,
            },
            "alter-table",
            200,
            None,
        ),
        # Alter table denied
        (
            {
                "insert-update": True,
                "create-table": False,
                "alter-table": False,
            },
            "alter-table",
            400,
            "table dogs has no column named weight",
        ),
    ],
)
@pytest.mark.asyncio
async def test_permission_finely_grained(
    ds_root_only, permissions, try_action, expected_status, expected_msg
):
    class TestPlugin:
        __name__ = "TestPlugin"

        @hookimpl
        def permission_allowed(self, datasette, actor, action):
            if action.startswith("insert:"):
                return permissions.get(action.replace("insert:", ""))

    pm.register(TestPlugin(), name="undo")
    try:
        # First create the table (if we aren't testing create-table) using
        # the root authenticated API token
        if try_action != "create-table":
            await ds_root_only.client.post(
                "/-/insert/data/dogs?pk=id",
                json=[{"id": 1, "name": "Toodles", "age": 3}],
                headers={"Authorization": "Bearer test-bot"},
            )

        # Now we can test the TestPlugin-provided permissions
        if try_action in ("insert-update", "create-table"):
            response = await ds_root_only.client.post(
                "/-/insert/data/dogs?pk=id",
                json=[{"id": 3, "name": "Cleopaws", "age": 5}],
            )
        elif try_action == "alter-table":
            response = await ds_root_only.client.post(
                "/-/insert/data/dogs?pk=id&alter=1",
                json=[{"id": 3, "name": "Cleopaws", "age": 5, "weight": 51.5}],
            )
        else:
            assert False, "{} is not a valid test action".format(try_action)
        assert response.status_code == expected_status
        if expected_status != 200:
            assert response.json()["error"] == expected_msg
    finally:
        pm.unregister(name="undo")


async def rows(client):
    return (await client.get("/data/dogs.json?_shape=array")).json()
