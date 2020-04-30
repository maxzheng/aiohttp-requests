import asyncio
import os
import aiohttp
import functools
import ssl
import urllib.request

from yarl import URL
from aiohttp.helpers import BasicAuth, ProxyInfo, strip_auth_from_url
from aiohttp.cookiejar import CookieJar
from aiohttp.client_exceptions import InvalidURL
from aiohttp.client_reqrep import ClientResponse

from .proxy import should_bypass_proxies


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


def merge_environment_settings(proxies, verify):
    # Set environment's proxies.
    _proxies = urllib.request.getproxies_environment()
    if proxies is not None:
        _proxies.update(proxies)

    # Look for requests environment configuration and be compatible
    # with cURL.
    if verify is True or verify is None:
        verify = (os.environ.get('REQUESTS_CA_BUNDLE') or os.environ.get('CURL_CA_BUNDLE'))
    return _proxies, verify


def render_proxy_spec(url, proxies):
    assert url.scheme != "no"
    proxy_url = proxies.get(url.scheme)
    if proxy_url is None:
        return ProxyInfo(None, None)
    else:
        proxy_without_auth, auth = strip_auth_from_url(URL(proxy_url))
        return ProxyInfo(proxy_without_auth, auth)


def render_ssl_context(verify, cert):
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.verify_flags = ssl.VERIFY_DEFAULT
    if verify is not False:
        if verify:
            ctx.load_verify_locations(cafile=verify)
        else:
            ctx.load_default_certs()
        ctx.verify_mode = ssl.CERT_REQUIRED
        ctx.check_hostname = True
    else:
        ctx.verify_mode = ssl.CERT_NONE
        ctx.check_hostname = False
    if cert:
        if isinstance(cert, tuple) and len(cert) == 2:
            ctx.load_cert_chain(cert[0], cert[1])
        else:
            ctx.load_cert_chain(cert)
    return ctx


def handle_requests_basic_auth(auth):
    if auth is None:
        return None
    elif isinstance(auth, BasicAuth):
        return auth
    elif isinstance(auth, tuple) and len(auth) == 2:
        return BasicAuth(auth[0], auth[1])
    else:
        try:
            from requests.auth import (
                HTTPBasicAuth as RequestsHTTPBasicAuth,
                HTTPDigestAuth as RequestsHTTPDigestAuth,
            )
            if isinstance(auth, RequestsHTTPBasicAuth):
                return BasicAuth(auth.username, auth.password)
            elif isinstance(auth, RequestsHTTPDigestAuth):
                raise NotImplementedError("digest authentication not implemented")
            else:
                raise NotImplementedError("unknown authentication method: {!r}".format(auth))
        except ImportError:
            pass
    raise NotImplementedError("{0!r} is unsupported".format(auth))


class RequestInfoWrapper:
    def __init__(self, req_info):
        self.req_info = req_info

    @property
    def url(self):
        return str(self.req_info.url)

    @property
    def method(self):
        return self.req_info.method

    @property
    def headers(self):
        return self.req_info.headers

    @property
    def body(self):
        # unavailable
        return b""


class OurClientResponse(ClientResponse):
    def __del__(self):
        self.close()
        super().__del__()

    @property
    def status_code(self):
        return self.status

    @property
    def request(self):
        return RequestInfoWrapper(self.request_info)

    async def body(self):
        if self._content is None:
            await self.read()
        return self._content

    async def read(self):
        try:
            return await super().read()
        finally:
            self.close()


def add_methods(class_):
    def _(meth):
        lower_meth = meth.lower()
        fn = lambda self, *args, **kwargs: self.request(meth, *args, **kwargs)
        fn.__name__ = lower_meth
        fn.__qualname__ = class_.__qualname__ + "." + lower_meth
        setattr(class_, lower_meth, fn)
    for meth in aiohttp.hdrs.METH_ALL:
        _(meth)
    return class_


@add_methods
class Requests:
    """ Thin wrapper for aiohttp.ClientSession with Requests simplicity """
    def __init__(self, *args, **kwargs):
        self._session_args = (args, kwargs)
        self._session = None
        self._session_mu = asyncio.Lock()

    @property
    def session(self):
        """ An instance of aiohttp.ClientSession """
        if not self._session or self._session.closed or self._session.loop.is_closed():
            self._session = aiohttp.ClientSession(*self._session_args[0], **self._session_args[1])
        return self._session

    @asynccontextmanager
    async def merge_cookies(self, cookies):
        if not cookies:
            yield
        else:
            with self._session_mu:
                prev_cookie_jar = self._session._cookie_jar
                new_cookie_jar = CookieJar(unsafe=prev_cookie_jar._unsafe, loop=prev_cookie_jar._loop)
                new_cookie_jar.update_cookies(prev_cookie_jar)
                new_cookie_jar.update_cookies(cookies)
                yield
                self._session._cookie_jar = prev_cookie_jar

    async def request(self, method, url, params=None, data=None, headers=None, cookies=None, files=None,
                      auth=None, timeout=None, allow_redirects=True, proxies=None,
                      hooks=None, stream=None, verify=None, cert=None, json=None,
                      **kwargs):
        if hooks is not None:
            raise NotImplementedError("hooks is currently unimplemened")
        if stream is not None:
            raise NotImplementedError("stream is currently unimplemened")

        try:
            parsed_url = URL(url)
        except ValueError:
            raise InvalidURL(url)

        proxies, verify = merge_environment_settings(proxies, verify)

        proxy_override = kwargs.pop("proxy", None)
        proxy_auth_override = kwargs.pop("proxy_auth", None)

        if proxy_override is None:
            proxy_info = render_proxy_spec(parsed_url, proxies)
            if proxy_auth_override is not None:
                proxy_info.proxy_auth = proxy_auth_override

        if proxies and should_bypass_proxies(parsed_url, proxies.get("no")):
            proxy_info = ProxyInfo(None, None)

        verify_ssl = kwargs.pop("verify_ssl", None)
        fingerprint = kwargs.pop("fingerprint", None)
        ssl_context = kwargs.pop("ssl_context", None)
        ssl = kwargs.pop("ssl", None)

        if verify_ssl is None and fingerprint is None and ssl_context is None and ssl is None:
            ssl = render_ssl_context(verify, cert)

        auth = handle_requests_basic_auth(auth)

        async with self.merge_cookies(cookies):
            resp = await self.session.request(
                method, url,
                params=params,
                data=data,
                headers=headers,
                auth=auth,
                timeout=timeout,
                allow_redirects=allow_redirects,
                proxy=proxy_info.proxy,
                proxy_auth=proxy_info.proxy_auth,
                json=json,
                verify_ssl=verify_ssl,
                fingerprint=fingerprint,
                ssl_context=ssl_context,
                ssl=ssl,
            )
            resp.__class__ = OurClientResponse
            return resp

    def close(self):
        """
        Close aiohttp.ClientSession.

        This is useful to be called manually in tests if each test when each test uses a new loop. After close, new
        requests will automatically create a new session.

        Note: We need a sync version for `__del__` and `aiohttp.ClientSession.close()` is async even though it doesn't
        have to be.
        """
        if self._session:
            if not self._session.closed:
                # Older aiohttp does not have _connector_owner
                if not hasattr(self._session, '_connector_owner') or self._session._connector_owner:
                    self._session._connector.close()
                self._session._connector = None
            self._session = None

    def __del__(self):
        self.close()


requests = Requests()
