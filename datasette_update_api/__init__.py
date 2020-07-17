from datasette import hookimpl
from datasette.utils.asgi import Response
import json
import sqlite_utils
from .utils import post_body


async def insert_update(request, datasette):
    database = request.url_vars["database"]
    table = request.url_vars["table"]
    db = datasette.get_database(database)

    post_json = json.loads(await post_body(request))

    def insert(conn):
        db = sqlite_utils.Database(conn)
        db[table].insert_all(post_json, replace=True, pk=request.args.get("pk") or None)
        return db[table].count

    table_count = await db.execute_write_fn(insert, block=True)

    return Response.json({"table_count": table_count})


@hookimpl
def register_routes():
    return [
        (r"^/-/update/(?P<database>[^/]+)/(?P<table>[^/]+)$", insert_update),
    ]
