aiohttp-requests
============================================================

Behold, the power of `aiohttp <https://aiohttp.readthedocs.io>`_ client with `Requests <http://docs.python-requests.org/>`_ simplicity:

.. code-block:: python

    import asyncio

    import aiohttp
    from aiohttp_requests import requests

    async def main():
        response = await requests.get('https://api.github.com', auth=aiohttp.BasicAuth('user', 'password'))
        text = await response.text()
        json = await response.json()
        return response, text, json

    r, text, json = asyncio.get_event_loop().run_until_complete(main())

    >>> r
    <ClientResponse(https://api.github.com/) [200 OK]>
    >>> r.status
    200
    >>> r.headers['Content-Type']
    'application/json; charset=utf-8'
    >>> r.get_encoding()
    'utf-8'
    >>> text
    '{"current_user_url":"https://api.github.com/user",...'
    >>> json
    {'current_user_url': 'https://api.github.com/user', ... }

The `requests` object is just proxying `get` and any other HTTP verb methods to `aiohttp.ClientSession <http://aiohttp.readthedocs.io/en/v3.0.1/client_reference.html#client-session>`_, which returns `aiohttp.ClientResponse <http://aiohttp.readthedocs.io/en/v3.0.1/client_reference.html#response-object>`_. To do anything else, just read the `aiohttp <https://aiohttp.readthedocs.io>`_ doc.

Links & Contact Info
====================

| PyPI Package: https://pypi.python.org/pypi/aiohttp-requests
| GitHub Source: https://github.com/maxzheng/aiohttp-requests
| Report Issues/Bugs: https://github.com/maxzheng/aiohttp-requests/issues
|
| Follow: https://twitter.com/MaxZhengX
| Connect: https://www.linkedin.com/in/maxzheng
| Contact: maxzheng.os @t gmail.com
