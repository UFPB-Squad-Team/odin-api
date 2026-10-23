from fastapi.responses import StreamingResponse


class OwnedStreamResponse(StreamingResponse):
    """Read binary output in bounded chunks and close it on every ASGI exit."""

    def __init__(self, stream, **kwargs):
        self.stream = stream

        def chunks():
            while chunk := stream.read(64 * 1024):
                yield chunk

        super().__init__(chunks(), **kwargs)

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.stream.close()
