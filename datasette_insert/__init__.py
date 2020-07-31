from datasette import hookimpl
from datasette.utils.asgi import Response
from datasette.utils import actor_matches_allow, sqlite3
import os
import json
import sqlite_utils
from .utils import post_body


class MissingTable(Exception):
    pass


async def insert_update(request, datasette):
    database = request.url_vars["database"]
    table = request.url_vars["table"]
    db = datasette.get_database(database)

    # Check permissions
    allow_insert_update = False
    allow_create_table = False
    allow_alter_table = False
    allow_all = await datasette.permission_allowed(
        request.actor, "insert:all", database, default=False
    )
    if allow_all:
        allow_insert_update = True
        allow_create_table = True
        allow_alter_table = True
    else:
        # Check for finely grained permissions
        allow_insert_update = await datasette.permission_allowed(
            request.actor, "insert:insert-update", (database, table), default=False
        )
        allow_create_table = await datasette.permission_allowed(
            request.actor, "insert:create-table", database, default=False
        )
        allow_alter_table = await datasette.permission_allowed(
            request.actor, "insert:alter-table", (database, table), default=False
        )

    if not allow_insert_update:
        return Response.json({"error": "Permission denied", "status": 403}, status=403)

    post_json = json.loads(await post_body(request))
    if isinstance(post_json, dict):
        post_json = [post_json]

    def insert(conn):
        db = sqlite_utils.Database(conn)
        if not allow_create_table and not db[table].exists():
            raise MissingTable()
        db[table].insert_all(
            post_json,
            replace=True,
            pk=request.args.get("pk"),
            alter=(request.args.get("alter") and allow_alter_table),
        )
        return db[table].count

    try:
        table_count = await db.execute_write_fn(insert, block=True)
    except MissingTable:
        return Response.json(
            {
                "status": 400,
                "error": "Table {} does not exist".format(table),
                "error_code": "missing_table",
            },
            status=400,
        )
    except sqlite3.OperationalError as ex:
        if "has no column" in str(ex):
            return Response.json(
                {"status": 400, "error": str(ex), "error_code": "unknown_keys"},
                status=400,
            )
        else:
            return Response.json({"error": str(ex), "status": 500}, status=500)

    return Response.json({"table_count": table_count})


@hookimpl
def permission_allowed(datasette, actor, action):
    if action != "insert:all":
        return None
    # action is insert:all
    if os.environ.get("DATASETTE_INSERT_UNSAFE"):
        return True
    plugin_config = datasette.plugin_config("datasette-insert") or {}
    if "allow" in plugin_config:
        return actor_matches_allow(actor, plugin_config["allow"])


@hookimpl
def register_routes():
    return [
        (r"^/-/insert/(?P<database>[^/]+)/(?P<table>[^/]+)$", insert_update),
    ]
