import itertools
from unittest import mock
import urllib.parse

import pytest
from yarl import URL

from .utils import dummy_server_factory


def test_host_name_matcher_ipv4_network():
    from aiohttp_requests.proxy import HostNameMatcher

    inputs = [
        (
            "192.168.0.0",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", True),
                ("192.168.0.", True),
                ("192.168.0.0", True),
                ("192.168.0.0.", True),
                ("192.168/16", True),
                ("192.168.0/16", True),
                ("192.168./16", True),
                ("192.168.0./16", True),
                ("192.168.0.0/16", True),
                ("192.168.0.0./16", True),
                ("192.168/24", True),
                ("192.168.0/24", True),
                ("192.168./24", True),
                ("192.168.0./24", True),
                ("192.168.0.0/24", True),
                ("192.168.0.0./24", True),
                (".192.168", False),
                (".192.168.", False),
            ],
        ),
        (
            "192.168.0.0.",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", True),
                ("192.168.0.", True),
                ("192.168.0.0", True),
                ("192.168.0.0.", True),
                ("192.168/16", True),
                ("192.168.0/16", True),
                ("192.168./16", True),
                ("192.168.0./16", True),
                ("192.168.0.0/16", True),
                ("192.168.0.0./16", True),
                ("192.168/24", True),
                ("192.168.0/24", True),
                ("192.168./24", True),
                ("192.168.0./24", True),
                ("192.168.0.0/24", True),
                ("192.168.0.0./24", True),
                (".192.168", False),
                (".192.168.", False),
            ],
        ),
        (
            "192.168.0.1",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", True),
                ("192.168.0.", True),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", True),
                ("192.168.0/16", True),
                ("192.168./16", True),
                ("192.168.0./16", True),
                ("192.168.0.0/16", True),
                ("192.168.0.0./16", True),
                ("192.168/24", True),
                ("192.168.0/24", True),
                ("192.168./24", True),
                ("192.168.0./24", True),
                ("192.168.0.0/24", True),
                ("192.168.0.0./24", True),
                (".192.168", False),
                (".192.168.", False),
            ],
        ),
        (
            "192.168.0.1.",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", True),
                ("192.168.0.", True),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", True),
                ("192.168.0/16", True),
                ("192.168./16", True),
                ("192.168.0./16", True),
                ("192.168.0.0/16", True),
                ("192.168.0.0./16", True),
                ("192.168/24", True),
                ("192.168.0/24", True),
                ("192.168./24", True),
                ("192.168.0./24", True),
                ("192.168.0.0/24", True),
                ("192.168.0.0./24", True),
                (".192.168", False),
                (".192.168.", False),
            ]
        ),
        (
            "192.168.1.0",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", False),
                ("192.168.0.", False),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", True),
                ("192.168.0/16", True),
                ("192.168./16", True),
                ("192.168.0./16", True),
                ("192.168.0.0/16", True),
                ("192.168.0.0./16", True),
                ("192.168/24", False),
                ("192.168.0/24", False),
                ("192.168./24", False),
                ("192.168.0./24", False),
                ("192.168.0.0/24", False),
                ("192.168.0.0./24", False),
                (".192.168", False),
                (".192.168.", False),
            ],
        ),
        (
            "192.168.1.0.",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", False),
                ("192.168.0.", False),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", True),
                ("192.168.0/16", True),
                ("192.168./16", True),
                ("192.168.0./16", True),
                ("192.168.0.0/16", True),
                ("192.168.0.0./16", True),
                ("192.168/24", False),
                ("192.168.0/24", False),
                ("192.168./24", False),
                ("192.168.0./24", False),
                ("192.168.0.0/24", False),
                ("192.168.0.0./24", False),
                (".192.168", False),
                (".192.168.", False),
            ],
        ),
        (
            "192.168",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", False),
                ("192.168.0.", False),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", False),
                ("192.168.0/16", False),
                ("192.168./16", False),
                ("192.168.0./16", False),
                ("192.168.0.0/16", False),
                ("192.168.0.0./16", False),
                ("192.168/24", False),
                ("192.168.0/24", False),
                ("192.168./24", False),
                ("192.168.0./24", False),
                ("192.168.0.0/24", False),
                ("192.168.0.0./24", False),
                (".192.168", True),
                (".192.168.", True),
            ]
        ),
        (
            "192.168.",
            [
                ("192.168", True),
                ("192.168.", True),
                ("192.168.0", False),
                ("192.168.0.", False),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", False),
                ("192.168.0/16", False),
                ("192.168./16", False),
                ("192.168.0./16", False),
                ("192.168.0.0/16", False),
                ("192.168.0.0./16", False),
                ("192.168/24", False),
                ("192.168.0/24", False),
                ("192.168./24", False),
                ("192.168.0./24", False),
                ("192.168.0.0/24", False),
                ("192.168.0.0./24", False),
                (".192.168", True),
                (".192.168.", True),
            ],
        ),
        (
            "hostname",
            [
                ("192.168", False),
                ("192.168.", False),
                ("192.168.0", False),
                ("192.168.0.", False),
                ("192.168.0.0", False),
                ("192.168.0.0.", False),
                ("192.168/16", False),
                ("192.168.0/16", False),
                ("192.168./16", False),
                ("192.168.0./16", False),
                ("192.168.0.0/16", False),
                ("192.168.0.0./16", False),
                ("192.168/24", False),
                ("192.168.0/24", False),
                ("192.168./24", False),
                ("192.168.0./24", False),
                ("192.168.0.0/24", False),
                ("192.168.0.0./24", False),
                (".192.168", False),
                (".192.168.", False),
            ],
        ),
    ]

    for in_, expecteds in inputs:
        for n in range(1, 4):
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [i[0] for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_) == expected, \
                    f"matcher({in_!r}) != {expected} where matcher = HostNameMatcher({hosts!r})"
            # input with port
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [i[0] for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_, "8080") == expected, \
                    f"matcher({in_!r}, '8080') != {expected} where matcher = HostNameMatcher({hosts!r})"
            # expected hosts with ports (1)
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [f"{i[0]}:8080" for i in l]
                matcher = HostNameMatcher(hosts)
                assert not matcher(in_), \
                    f"matcher({in_!r}) != False where matcher = HostNameMatcher({hosts!r})"
            # expected hosts with ports (2)
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [f"{i[0]}:8080" for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_, "8080") == expected, \
                    f"matcher({in_!r}, '8080') != {expected} where matcher = HostNameMatcher({hosts!r})"
            # expected hosts with asterisk port
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [f"{i[0]}:*" for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_) == expected, \
                    f"matcher({in_!r}) != {expected} where matcher = HostNameMatcher({hosts!r})"

    # wildcard
    expecteds = ["*", "*:*"]
    for in_, _ in inputs:
        for expected in expecteds:
            matcher = HostNameMatcher(expected)
            assert matcher(in_)


def test_host_name_matcher_ipv6_network():
    from aiohttp_requests.proxy import HostNameMatcher

    inputs = [
        (
            "[::1]",
            [
                ("[::]/128", False),
                ("[::/128]", False),
                ("[::1]/128", True),
                ("[::1/128]", True),
                ("[::]/112", True),
                ("[::/112]", True),
                ("[fe80::]/64", False),
                ("[fe80::/64]", False),
            ],
        ),
        (
            "[fe80::1]",
            [
                ("[::]/128", False),
                ("[::/128]", False),
                ("[::1]/128", False),
                ("[::1/128]", False),
                ("[::]/112", False),
                ("[::/112]", False),
                ("[fe80::]/64", True),
                ("[fe80::/64]", True),
            ],
        ),
    ]

    for in_, expecteds in inputs:
        for n in range(1, 4):
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [i[0] for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_) == expected, \
                    f"matcher({in_!r}) != {expected} where matcher = HostNameMatcher({hosts!r})"
            # input with port
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [i[0] for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_, "8080") == expected, \
                    f"matcher({in_!r}, '8080') != {expected} where matcher = HostNameMatcher({hosts!r})"
            # expected hosts with ports (1)
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [f"{i[0]}:8080" for i in l]
                matcher = HostNameMatcher(hosts)
                assert not matcher(in_), \
                    f"matcher({in_!r}) != False where matcher = HostNameMatcher({hosts!r})"
            # expected hosts with ports (2)
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [f"{i[0]}:8080" for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_, "8080") == expected, \
                    f"matcher({in_!r}, '8080') != {expected} where matcher = HostNameMatcher({hosts!r})"
            # expected hosts with asterisk port
            for l in itertools.combinations(expecteds, n):
                expected = any(i[1] for i in l)
                hosts = [f"{i[0]}:*" for i in l]
                matcher = HostNameMatcher(hosts)
                assert matcher(in_) == expected, \
                    f"matcher({in_!r}) != {expected} where matcher = HostNameMatcher({hosts!r})"

    # wildcard
    expecteds = ["*", "*:*"]
    for in_, _ in inputs:
        for expected in expecteds:
            matcher = HostNameMatcher(expected)
            assert matcher(in_)


async def test_should_bypass_proxies(setenv, loop):
    from aiohttp_requests import Requests
    from aiohttp.client_reqrep import ClientResponse
    from aiohttp.helpers import BasicAuth

    setenv["http_proxy"] = "http://user:pass@proxy.example.com:8080/"
    setenv["https_proxy"] = "http://user:pass@proxy.example.com:8081/"
    setenv["no_proxy"] = "[::]/112,192.168.0.0/16,192.168,hostname"

    cases = [
        (
            "http://[::1]",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "http://[::1:0]",
            [
                ("proxy", URL("http://proxy.example.com:8080/")),
                ("proxy_auth", BasicAuth("user", "pass"))
            ]
        ),

        (
            "http://192.168.0.1/",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "http://192.168.1.1/",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "http://172.16.0.1/",
            [
                ("proxy", URL("http://proxy.example.com:8080/")),
                ("proxy_auth", BasicAuth("user", "pass"))
            ]
        ),

        (
            "http://hostname/",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "http://example.com",
            [
                ("proxy", URL("http://proxy.example.com:8080/")),
                ("proxy_auth", BasicAuth("user", "pass"))
            ]
        ),

        (
            "https://[::1]",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "https://[::1:0]",
            [
                ("proxy", URL("http://proxy.example.com:8081/")),
                ("proxy_auth", BasicAuth("user", "pass"))
            ]
        ),

        (
            "https://192.168.0.1/",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "https://192.168.1.1/",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "https://172.16.0.1/",
            [
                ("proxy", URL("http://proxy.example.com:8081/")),
                ("proxy_auth", BasicAuth("user", "pass"))
            ]
        ),

        (
            "https://hostname/",
            [
                ("proxy", None),
                ("proxy_auth", None)
            ]
        ),

        (
            "https://example.com",
            [
                ("proxy", URL("http://proxy.example.com:8081/")),
                ("proxy_auth", BasicAuth("user", "pass"))
            ]
        ),
    ]

    call_args = None

    async def request_mock(method, url, *args, **kwargs):
        nonlocal call_args
        call_args = mock.call(method, url, *args, **kwargs)
        return ClientResponse(
            method, URL(url),
            writer=None,
            continue100=False,
            timer=None,
            request_info=None,
            traces=None,
            loop=loop,
            session=None,
        )

    with mock.patch(
        "aiohttp.ClientSession",
        return_value=mock.Mock(request=request_mock)
    ):
        req = Requests()
        for case in cases:
            await req.get(case[0])
            for arg, expected in case[1]:
                assert call_args[2][arg] == expected, f"req.get({case[0]!r}) => request({arg} != {expected!r})"


@pytest.fixture(params=["::1", "127.0.0.1"])
async def dummy_proxy(request):
    from aiohttp import web

    async def handler(request):
        return web.Response(text="proxy")

    # ugly verbose code due to absence of "async yield from"
    async for sockname in dummy_server_factory(request.param, handler):
        yield sockname


@pytest.fixture(params=["::1", "127.0.0.1"])
async def dummy_server(request):
    from aiohttp import web

    async def handler(request):
        return web.Response(text="ok")

    # ugly verbose code due to absence of "async yield from"
    async for sockname in dummy_server_factory(request.param, handler):
        yield "http://{}/".format(sockname)


@pytest.fixture
async def dummy_proxy_with_env(dummy_proxy, setenv):
    setenv["http_proxy"] = "http://{}".format(dummy_proxy)
    yield dummy_proxy


async def test_nonproxied_requests(loop, dummy_server):
    from aiohttp_requests import requests
    resp = await requests.get(dummy_server)
    assert await resp.text() == "ok"


async def test_proxied_requests(loop, dummy_proxy_with_env, dummy_server):
    from aiohttp_requests import requests
    resp = await requests.get(dummy_server)
    assert await resp.text() == "proxy"


async def test_proxied_requests_no_proxy(loop, dummy_proxy_with_env, dummy_server, setenv):
    from aiohttp_requests import requests
    # I love yarl, but when it comes to IPv6, it is broken by design.
    setenv["no_proxy"] = urllib.parse.urlparse(dummy_server).netloc
    resp = await requests.get(dummy_server)
    assert await resp.text() == "ok"
