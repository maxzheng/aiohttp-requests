import asyncio

import pytest
from aiohttp import web, client_exceptions
from aioresponses import aioresponses
from cryptography.hazmat.primitives import serialization

from aiohttp_requests import requests, Requests
from aiohttp_requests.compat import asynccontextmanager
from .utils import dummy_server_factory


@pytest.fixture(params=["::1", "127.0.0.1"])
async def dummy_server(request, loop):
    from aiohttp import web

    async def handler(request):
        return web.Response(text="ok")

    # ugly verbose code due to absence of "async yield from"
    async for sockname in dummy_server_factory(request.param, handler):
        yield "http://{}/".format(sockname)


async def test_aiohttp_requests():
    test_url = 'http://dummy-url'
    test_payload = {'hello': 'world'}

    with aioresponses() as mocked:
        mocked.get(test_url, payload=test_payload)

        response = await requests.get(test_url)
        json = await response.json()

        assert test_payload == json

    await requests.async_close()  # Normally called on destroy


async def test_aiohttp_requests_integration(dummy_server):
    response = await requests.get(dummy_server)
    content = await response.text()

    assert response.status == 200
    assert content == "ok"


async def test_aiohttp_requests_after_close(loop, dummy_server):
    # Closing ourself
    await (await requests.async_session()).close()

    await test_aiohttp_requests_integration(dummy_server)

    # Closing aiohttp session
    await (await requests.async_session()).close()

    await test_aiohttp_requests_integration(dummy_server)


async def test_aiohttp_disposal():
    requests = Requests()
    with aioresponses() as mocked:
        mocked.get("http://example.com", body=b"test")
        response = await requests.get("http://example.com")
        assert await response.text() == "test"
    del requests
    # run a event loop to give a chance for spawned task in __del__() to run.
    await asyncio.sleep(1)
    # if it's been enough, it should've been ok... ;)


async def test_aiohttp_disposal_without_having_session_created():
    requests = Requests()
    del requests
    await asyncio.sleep(1)
    # if it's been enough, it should've been ok... ;)


@pytest.mark.parametrize(
    ["ca_bundle_envs", "bundle_applied"],
    [
        (
            {
                "REQUESTS_CA_BUNDLE": None,
                "CURL_CA_BUNDLE": None,
            },
            None,
        ),
        (
            {
                "REQUESTS_CA_BUNDLE": 0,
                "CURL_CA_BUNDLE": None,
            },
            0,
        ),
        (
            {
                "REQUESTS_CA_BUNDLE": None,
                "CURL_CA_BUNDLE": 0,
            },
            0,
        ),
        (
            {
                "REQUESTS_CA_BUNDLE": 0,
                "CURL_CA_BUNDLE": 1,
            },
            0,
        ),
    ]
)
async def test_aiohttp_tls(tmp_path, server_certs, setenv, ca_bundle_envs, bundle_applied):
    for ei in range(0, len(server_certs)):
        bundle_sets = [
            [c for i, c in enumerate(server_certs) if i != ei],
            [server_certs[ei]],
        ]

        bundle_paths = [tmp_path / "bundle{}.pem".format(i) for i in range(len(bundle_sets))]
        for bundle_path, bundle in zip(bundle_paths, bundle_sets):
            bundle_path.write_bytes(
                b"\n".join(
                    c.ca_certificate.public_bytes(serialization.Encoding.PEM)
                    for c in bundle
                ),
            )

        for k, v in ca_bundle_envs.items():
            if v is not None:
                setenv[k] = str(bundle_paths[v])
            else:
                del setenv[k]

        for bundle_index, bundle_set in enumerate(bundle_sets):
            for server_cert, server_key, _ in bundle_set:
                server_cert_path = tmp_path / "server_cert.pem"
                server_cert_path.write_bytes(
                    server_cert.public_bytes(serialization.Encoding.PEM) + b"\n" +
                    server_key.private_bytes(
                        serialization.Encoding.PEM,
                        format=serialization.PrivateFormat.PKCS8,
                        encryption_algorithm=serialization.NoEncryption(),
                    )
                )

                async def handler(request):
                    return web.Response(text="ok")

                async with asynccontextmanager(dummy_server_factory)(
                    bind_addr="127.0.0.1",
                    handler=handler,
                    certfile=str(server_cert_path),
                    keyfile=str(server_cert_path),
                ) as netloc:
                    try:
                        response = await requests.get("https://{}".format(netloc))
                        assert await response.text() == "ok"
                        assert bundle_applied == bundle_index
                    except (
                        client_exceptions.ClientConnectorCertificateError,
                        client_exceptions.ClientConnectorSSLError,
                    ) as e:
                        assert bundle_applied != bundle_index, e.__cause__
