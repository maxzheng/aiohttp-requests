from aiohttp_requests import requests
from aioresponses import aioresponses
import pytest


@pytest.mark.asyncio
async def test_aiohttp_requests():
    test_url = 'http://dummy-url'
    test_payload = {'hello': 'world'}

    with aioresponses() as mocked:
        mocked.get(test_url, payload=test_payload)

        response = await requests.get(test_url)
        json = await response.json()

        assert test_payload == json

    requests.close()  # Normally called on destroy
