import aiohttp
import functools

from coworker import Coworker


class _Corequest(Coworker):
    """ Worker for making concurrent requests """
    async def do_task(self, task):
        request, verb, path, args, kwargs = task
        return await request(verb, path, *args, **kwargs)


class Requests:
    """ Thin wrapper for aiohttp.ClientSession with Requests simplicity """
    def __init__(self, *args, max_concurrency=10, **kwargs):
        self._session_args = (args, kwargs)
        self._session = None

        #: Worker for concurrent requests
        self._worker = _Corequest(max_concurrency=max_concurrency)

    @property
    def session(self):
        """ An instance of aiohttp.ClientSession """
        if not self._session or self._session.closed or self._session._loop.is_closed():
            self._session = aiohttp.ClientSession(*self._session_args[0], **self._session_args[1])
        return self._session

    def __getattr__(self, attr):
        if attr.upper() in aiohttp.hdrs.METH_ALL:
            @functools.wraps(self.session._request)
            def session_request(path, *args, **kwargs):
                """
                This ensures `self.session` is always called where it can check the session/loop state so can't use
                functools.partials as monkeypatch seems to do something weird where __getattr__ is only called once
                for each attribute after patch is undone
                """
                if isinstance(path, (list, tuple)):
                    return self._concurrent_request(self.session._request, attr.upper(), path, args, kwargs,
                                                    as_iterator=kwargs.pop('as_iterator', False))
                else:
                    return self.session._request(attr.upper(), path, *args, **kwargs)

            return session_request
        else:
            return super().__getattribute__(attr)

    def __setattr__(self, attr, value):
        if attr == 'max_concurrency':
            self._worker.max_concurrency = value
        else:
            super().__setattr__(attr, value)

    def _concurrent_request(self, request, verb, paths, args, kwargs, as_iterator=False):
        return self._worker.do([(request, verb, path, args, kwargs) for path in paths], as_iterator=as_iterator)

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
                    try:
                        self._session._connector._close()  # New version returns a coroutine in close() as warning
                    except Exception:
                        self._session._connector.close()
                self._session._connector = None
            self._session = None

    def __del__(self):
        self.close()


requests = Requests()
