async def post_body(request):
    body = b""
    more_body = True
    while more_body:
        message = await request.receive()
        assert message["type"] == "http.request", message
        body += message.get("body", b"")
        more_body = message.get("more_body", False)

    return body
