from starlette.responses import JSONResponse

class BoundedBody:
    """Bound request bytes before JSON or multipart parsing, including chunked uploads.

    Buffer at most 1.1 MB per request in memory. Never log the request payload.
    The small envelope allowance accommodates one 1 MiB file plus form headers.
    """
    def __init__(self, app, limit=1100000):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http' or scope['method'] in ('GET','HEAD','OPTIONS'):
            return await self.app(scope,receive,send)
        parts, size = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect': return
            chunk = message.get('body',b'')
            size += len(chunk)
            if size > self.limit:
                return await JSONResponse({'detail':'Request too large. One attachment of at most 1 MB is allowed.'},413)(scope,receive,send)
            parts.append(chunk)
            if not message.get('more_body',False): break
        delivered = False
        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {'type':'http.request','body':b''.join(parts),'more_body':False}
            return await receive()
        await self.app(scope,bounded_receive,send)
