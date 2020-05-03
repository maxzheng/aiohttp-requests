import functools


class AsyncContextManager:
    def __init__(self, aiter):
        self.aiter = aiter

    async def __aenter__(self):
        return await self.aiter.__anext__()

    async def __aexit__(self, typ, val, tb):
        try:
            if typ is not None:
                await self.aiter.athrow(typ, val, tb)
            else:
                await self.aiter.asend(None)
            raise RuntimeError("generator didn't stop")
        except StopAsyncIteration:
            pass
        return True


def asynccontextmanager(fn):
    @functools.wraps(fn)
    def _(*args, **kwargs):
        return AsyncContextManager(fn(*args, **kwargs))
    return _
