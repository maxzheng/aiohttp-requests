from aiohttp_requests import requests
from aioresponses import aioresponses


async def test_aiohttp_requests():
    test_url = 'http://dummy-url'
    test_payload = {'hello': 'world'}

    with aioresponses() as mocked:
        mocked.get(test_url, payload=test_payload)

        response = await requests.get(test_url)
        json = await response.json()

        assert test_payload == json

    requests.close()  # Normally called on destroy


async def test_aiohttp_requests_integration():
    response = await requests.get('https://www.google.com')
    content = await response.text()

    assert response.status == 200
    assert len(content) > 10000


async def test_aiohttp_requests_after_close(loop):
    # Closing ourself
    requests.close()

    await test_aiohttp_requests_integration()

    # Closing aiohttp session
    await requests.session.close()

    await test_aiohttp_requests_integration()
