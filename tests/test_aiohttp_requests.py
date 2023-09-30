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
    # One request
    response = await requests.get('https://www.google.com')
    content = await response.text()

    assert response.status == 200
    assert len(content) > 10000


async def test_aiohttp_requests_integration_multiple():
    # Multiple requests
    responses = await requests.get(['https://www.google.com'] * 2)
    assert len(responses) == 2
    for response in responses:
        content = await response.text()

        assert response.status == 200
        assert len(content) > 10000

    # Multiple requests as iterator
    responses = requests.get(['https://www.google.com'] * 2, as_iterator=True)
    for response in responses:
        response = await response
        content = await response.text()

        assert response.status == 200
        assert len(content) > 10000


async def test_aiohttp_requests_after_close():
    # Closing ourself
    requests.close()

    await test_aiohttp_requests_integration()

    # Closing aiohttp session
    await requests.session.close()

    await test_aiohttp_requests_integration()
