async def test_asynccontextmanager_basic(loop):
    from aiohttp_requests.compat import asynccontextmanager

    class MyException(Exception):
        pass

    async def _():
        nonlocal a
        a += 1
        try:
            yield 123
        except MyException:
            a += 1
        a += 1

    a = 0
    async with asynccontextmanager(_)() as v:
        assert v == 123
        assert a == 1
    assert a == 2

    a = 0
    async with asynccontextmanager(_)() as v:
        assert v == 123
        assert a == 1
        raise MyException()
    assert a == 3
