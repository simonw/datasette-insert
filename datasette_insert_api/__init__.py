from datasette import hookimpl
from datasette.utils.asgi import Response
from datasette.utils import sqlite3
import json
import sqlite_utils
from .utils import post_body


async def insert_update(request, datasette):
    database = request.url_vars["database"]
    table = request.url_vars["table"]
    db = datasette.get_database(database)

    post_json = json.loads(await post_body(request))
    if isinstance(post_json, dict):
        post_json = [post_json]

    def insert(conn):
        db = sqlite_utils.Database(conn)
        db[table].insert_all(
            post_json,
            replace=True,
            pk=request.args.get("pk"),
            alter=request.args.get("alter"),
        )
        return db[table].count

    try:
        table_count = await db.execute_write_fn(insert, block=True)
    except sqlite3.OperationalError as ex:
        if "has no column" in str(ex):
            return Response.json(
                {"status": 400, "error": str(ex), "error_code": "unknown_keys"},
                status=400,
            )
        else:
            return Respones.json({"error": str(ex), "status": 500}, status=500)

    return Response.json({"table_count": table_count})


@hookimpl
def register_routes():
    return [
        (r"^/-/insert/(?P<database>[^/]+)/(?P<table>[^/]+)$", insert_update),
    ]
