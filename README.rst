aiohttp-requests
============================================================

A thin wrapper for `aiohttp <https://aiohttp.readthedocs.io>`_ client with `Requests <http://docs.python-requests.org/>`_ simplicity.

Behold, the power of aiohttp client with Requests simplicity
============================================================

.. code-block: python

    >>> import asyncio
    >>>
    >>> import aiohttp
    >>> from aiohttp_requests import requests
    >>>
    >>> async def main():
    ...     r = await requests.get('https://api.github.com/user', auth=aiohttp.BasicAuth('user', 'password'))
    ...     text = await r.text()
    ...     json = await r.json()
    ...     return r, content, text, json
    ...
    >>> loop = asyncio.get_event_loop()
    >>> r, text, json = loop.run_until_complete(main())
    >>>
    >>> r
    <ClientResponse(https://api.github.com/user) [200 OK]>
    >>> r.status
    200
    >>> r.headers['Content-Type']
    'application/json; charset=utf-8'
    >>> r.get_encoding()
    'utf-8'
    >>> text
    '{"login":"...'
    >>> json
    {'login': 'user', 'public_repos': 28, ...}

The `requests` object is just proxying `get` and any other HTTP verb methods to `aiohttp.ClientSession`, which returns `aiohttp.ClientResponse`. To do anything else, just read the `aiohttp <https://aiohttp.readthedocs.io>`_ doc.

Links & Contact Info
====================

| PyPI Package: https://pypi.python.org/pypi/aiohttp-requests
| GitHub Source: https://github.com/maxzheng/aiohttp-requests
| Report Issues/Bugs: https://github.com/maxzheng/aiohttp-requests/issues
|
| Follow: https://twitter.com/MaxZhengX
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com
